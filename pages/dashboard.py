import streamlit as st
import datetime
import pandas as pd
import plotly.express as px
from utils.db import get_user_projects
from utils.styles import apply_global_styles, render_top_navbar

# Supabase'den yeni verileri çekmek için doğrudan bağlantı
from utils.db import supabase

st.set_page_config(
    page_title="SARCON Portal | Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Sidebar gizleme ve Üst Navigasyon Menüsünü Yükle
apply_global_styles(is_login=False)
render_top_navbar()

# Header
st.markdown("""
<div style="border-left: 3px solid #3b82f6; padding-left: 0.8rem; margin-bottom: 1.5rem;">
    <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.3rem;">Proje Özeti</h3>
    <p style="color: #737373; margin: 0; font-size: 0.8rem;">Kaynak ve ilerleme verilerinin güncel analizi</p>
</div>
""", unsafe_allow_html=True)

# Projeleri getir
projects, err = get_user_projects()
project_names = [p["project_name"] for p in projects] if projects else []

if not project_names:
    st.info("Henüz bir proje oluşturmadınız. Veri Girişi sayfasından proje oluşturabilirsiniz.")
else:
    col_proje1, col_proje2 = st.columns([3, 1])
    with col_proje1:
        selected_project = st.selectbox("Proje Seçin", project_names, label_visibility="collapsed")
    with col_proje2:
        if st.button("Yeni Proje", use_container_width=True):
            st.switch_page("pages/veri_girisi.py")
    
    project_id = next(p["id"] for p in projects if p["project_name"] == selected_project)
    
    # ==========================================
    # 1. KAYNAK VERİLERİNİ ÇEK (daily_resources)
    # ==========================================
    try:
        res_response = (
            supabase.table("daily_resources")
            .select("*")
            .eq("project_id", project_id)
            .execute()
        )
        resources_data = res_response.data if res_response.data else []
    except Exception as e:
        resources_data = []
        st.warning(f"Kaynak verileri alınamadı: {e}")
    
    # ==========================================
    # 2. İŞ İLERLEME VERİLERİNİ ÇEK (daily_work_progress)
    # ==========================================
    try:
        work_response = (
            supabase.table("daily_work_progress")
            .select("*")
            .eq("project_id", project_id)
            .execute()
        )
        work_data = work_response.data if work_response.data else []
    except Exception as e:
        work_data = []
        st.warning(f"İş ilerleme verileri alınamadı: {e}")
    
    # ==========================================
    # 3. VERİLERİ ANALİZ ET
    # ==========================================
    
    # Kaynak verilerini DataFrame'e çevir
    df_resources = pd.DataFrame(resources_data) if resources_data else pd.DataFrame()
    df_work = pd.DataFrame(work_data) if work_data else pd.DataFrame()
    
    # Toplam kaynak sayısı
    total_resources = len(df_resources) if not df_resources.empty else 0
    total_work_entries = len(df_work) if not df_work.empty else 0
    
    # Endirekt Personel toplamı (günlük toplam)
    endirect_total = 0
    direct_total = 0
    machine_total = 0
    material_total = 0
    
    if not df_resources.empty:
        # Endirekt Personel
        endirect_df = df_resources[df_resources['category'] == 'Endirekt Personel']
        if not endirect_df.empty:
            endirect_total = endirect_df['value'].sum()
        
        # Direkt Personel
        direct_df = df_resources[df_resources['category'] == 'Direkt Personel']
        if not direct_df.empty:
            direct_total = direct_df['value'].sum()
        
        # Makina
        machine_df = df_resources[df_resources['category'] == 'Makina']
        if not machine_df.empty:
            machine_total = machine_df['value'].sum()
        
        # Yapı Malzemesi (toplam miktar)
        material_df = df_resources[df_resources['category'] == 'Yapı Malzemesi']
        if not material_df.empty:
            material_total = material_df['value'].sum()
    
    # İş ilerleme - toplam ilerleme yüzdesi ve tamamlanan iş sayısı
    total_progress = 0
    completed_tasks = 0
    if not df_work.empty:
        total_progress = df_work['ilerleme_yuzdesi'].mean() if 'ilerleme_yuzdesi' in df_work.columns else 0
        completed_tasks = len(df_work[df_work['ilerleme_yuzdesi'] >= 100]) if 'ilerleme_yuzdesi' in df_work.columns else 0
    
    # ==========================================
    # 4. METRİKLER
    # ==========================================
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Endirekt Personel (Toplam)",
            f"{endirect_total:,.0f}",
            help="Tüm günlerdeki toplam endirekt personel sayısı"
        )
    
    with col2:
        st.metric(
            "Direkt Personel (Toplam)",
            f"{direct_total:,.0f}",
            help="Tüm günlerdeki toplam direkt personel sayısı"
        )
    
    with col3:
        st.metric(
            "Makina (Toplam)",
            f"{machine_total:,.0f}",
            help="Tüm günlerdeki toplam makina sayısı"
        )
    
    with col4:
        st.metric(
            "Ortalama İlerleme",
            f"{total_progress:.1f}%",
            help="Tüm iş kalemlerinin ortalama ilerleme yüzdesi"
        )
    
    st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)
    
    # ==========================================
    # 5. GRAFİKLER
    # ==========================================
    
    if not df_resources.empty:
        col_chart1, col_chart2 = st.columns([1, 1])
        
        # GRAFİK 1: Kategori Bazında Toplam Kaynak
        with col_chart1:
            st.markdown("<span style='font-size:0.9rem; font-weight:600; color:#d4d4d4;'>Kategori Bazında Toplam Kaynak</span>", unsafe_allow_html=True)
            
            category_summary = df_resources.groupby('category')['value'].sum().reset_index()
            category_summary.columns = ['Kategori', 'Toplam']
            
            if not category_summary.empty:
                fig1 = px.bar(
                    category_summary,
                    x='Kategori',
                    y='Toplam',
                    text='Toplam',
                    color='Kategori',
                    color_discrete_sequence=['#2563eb', '#38bdf8', '#34d399', '#facc15', '#f87171', '#a78bfa']
                )
                
                fig1.update_traces(
                    texttemplate='%{text:.0f}',
                    textposition='outside',
                    textfont=dict(color='#a3a3a3', size=11),
                    hovertemplate='<b>%{x}</b><br>Toplam: %{y}<extra></extra>'
                )
                
                fig1.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=10, r=10, t=25, b=50),
                    height=300,
                    xaxis=dict(
                        showgrid=False,
                        color='#a3a3a3',
                        title=None,
                        tickfont=dict(size=11)
                    ),
                    yaxis=dict(
                        showgrid=True,
                        gridcolor='#1f1f1f',
                        color='#a3a3a3',
                        title=None,
                        zeroline=False
                    ),
                    showlegend=False
                )
                st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("Kategori verisi bulunamadı.")
        
        # GRAFİK 2: Tarihe Göre Günlük Toplam Kaynak
        with col_chart2:
            st.markdown("<span style='font-size:0.9rem; font-weight:600; color:#d4d4d4;'>Günlük Toplam Kaynak</span>", unsafe_allow_html=True)
            
            daily_summary = df_resources.groupby('report_date')['value'].sum().reset_index()
            daily_summary.columns = ['Tarih', 'Toplam']
            
            if not daily_summary.empty:
                daily_summary['Tarih'] = pd.to_datetime(daily_summary['Tarih'])
                daily_summary = daily_summary.sort_values('Tarih')
                daily_summary['Tarih_Str'] = daily_summary['Tarih'].dt.strftime('%Y-%m-%d')
                
                fig2 = px.line(
                    daily_summary,
                    x='Tarih_Str',
                    y='Toplam',
                    markers=True,
                    line_shape='linear'
                )
                
                fig2.update_traces(
                    line=dict(color='#2563eb', width=2.5),
                    marker=dict(color='#2563eb', size=8),
                    hovertemplate='<b>Tarih:</b> %{x}<br><b>Toplam Kaynak:</b> %{y}<extra></extra>'
                )
                
                fig2.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=10, r=10, t=25, b=10),
                    height=300,
                    xaxis=dict(
                        showgrid=False,
                        color='#a3a3a3',
                        title=None,
                        tickfont=dict(size=10)
                    ),
                    yaxis=dict(
                        showgrid=True,
                        gridcolor='#1f1f1f',
                        color='#a3a3a3',
                        title=None,
                        zeroline=False
                    )
                )
                st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("Günlük veri bulunamadı.")
    else:
        st.info("Henüz bu projeye ait kaynak verisi bulunmuyor. Veri Girişi sayfasından kaynak ekleyin.")
    
    # ==========================================
    # 6. İŞ İLERLEME ÖZETİ
    # ==========================================
    if not df_work.empty:
        st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)
        st.markdown("<span style='font-size:0.9rem; font-weight:600; color:#d4d4d4;'>İş İlerleme Özeti</span>", unsafe_allow_html=True)
        
        col_w1, col_w2, col_w3 = st.columns(3)
        
        with col_w1:
            st.metric(
                "Toplam İş Kalemi",
                f"{len(df_work)}",
                help="Toplam iş ilerleme satırı sayısı"
            )
        
        with col_w2:
            st.metric(
                "Tamamlanan İş",
                f"{completed_tasks}",
                help="%100 ilerleme tamamlanmış iş sayısı"
            )
        
        with col_w3:
            st.metric(
                "Ortalama İlerleme",
                f"{df_work['ilerleme_yuzdesi'].mean():.1f}%",
                help="Tüm iş kalemlerinin ortalama ilerleme yüzdesi"
            )
        
        # İş ilerleme tablosu (son 10 satır)
        with st.expander("📋 Son 10 İş İlerleme Kaydı"):
            st.dataframe(
                df_work.tail(10)[['report_date', 'yapilan_is', 'is_turu', 'ilerleme_yuzdesi', 'kesif_miktari', 'yapilan_miktar']],
                use_container_width=True,
                column_config={
                    'report_date': 'Tarih',
                    'yapilan_is': 'Yapılan İş',
                    'is_turu': 'İş Türü',
                    'ilerleme_yuzdesi': 'İlerleme %',
                    'kesif_miktari': 'Keşif',
                    'yapilan_miktar': 'Yapılan'
                }
            )
    else:
        st.info("Henüz bu projeye ait iş ilerleme verisi bulunmuyor.")
