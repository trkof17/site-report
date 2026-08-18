import streamlit as st
import datetime
import pandas as pd
import plotly.express as px
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import base64
from utils.db import get_user_projects, get_project_reports, supabase
from utils.styles import apply_global_styles, render_top_navbar
from utils.auth import get_current_user

st.set_page_config(
    page_title="SARCON Portal | Rapor Al",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

apply_global_styles(is_login=False)
render_top_navbar()

st.markdown("""
<div style="border-left: 3px solid #3b82f6; padding-left: 0.8rem; margin-bottom: 1.5rem;">
    <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.3rem;">Rapor Oluştur</h3>
    <p style="color: #737373; margin: 0; font-size: 0.8rem;">Proje verilerinizi PDF olarak alın</p>
</div>
""", unsafe_allow_html=True)

# --- KULLANICI BİLGİSİ (Girişten otomatik) ---
user = get_current_user()
user_email = user.email if user else "kullanici@example.com"

st.info(f"📧 Rapor e-posta adresinize gönderilecek: **{user_email}**")

# --- PROJE SEÇİMİ ---
projects, err = get_user_projects()
project_names = [p["project_name"] for p in projects] if projects else []

if not project_names:
    st.warning("Henüz bir proje oluşturmadınız. Veri Girişi sayfasından proje oluşturun.")
    st.stop()

selected_project = st.selectbox("Proje Seçin", project_names)
project_id = next(p["id"] for p in projects if p["project_name"] == selected_project)

# --- RAPOR TÜRÜ SEÇİMİ ---
st.markdown("### Rapor Kapsamı")
col_scope1, col_scope2 = st.columns(2)
with col_scope1:
    scope_days = st.selectbox(
        "Gün Aralığı",
        [7, 14, 30, 90, "Tümü"],
        index=0
    )

# --- VERİLERİ ÇEK ---
try:
    res_response = supabase.table("daily_resources").select("*").eq("project_id", project_id).execute()
    resources_data = res_response.data if res_response.data else []
except:
    resources_data = []

try:
    work_response = supabase.table("daily_work_progress").select("*").eq("project_id", project_id).execute()
    work_data = work_response.data if work_response.data else []
except:
    work_data = []

reports, _ = get_project_reports(project_id)

df_resources = pd.DataFrame(resources_data) if resources_data else pd.DataFrame()
df_work = pd.DataFrame(work_data) if work_data else pd.DataFrame()
df_reports = pd.DataFrame(reports) if reports else pd.DataFrame()

if df_reports.empty and df_resources.empty and df_work.empty:
    st.warning("Bu projeye ait henüz veri bulunmuyor.")
    st.stop()

# Tarih filtresi
if scope_days != "Tümü":
    cutoff_date = datetime.date.today() - datetime.timedelta(days=int(scope_days))
    if not df_reports.empty and 'report_date' in df_reports.columns:
        df_reports['report_date'] = pd.to_datetime(df_reports['report_date'])
        df_reports = df_reports[df_reports['report_date'] >= pd.Timestamp(cutoff_date)]
    if not df_resources.empty and 'report_date' in df_resources.columns:
        df_resources['report_date'] = pd.to_datetime(df_resources['report_date'])
        df_resources = df_resources[df_resources['report_date'] >= pd.Timestamp(cutoff_date)]
    if not df_work.empty and 'report_date' in df_work.columns:
        df_work['report_date'] = pd.to_datetime(df_work['report_date'])
        df_work = df_work[df_work['report_date'] >= pd.Timestamp(cutoff_date)]

# --- ÖZET METRİKLER ---
st.markdown("### 📊 Proje Özeti")

col1, col2, col3, col4 = st.columns(4)
with col1:
    total_labor = df_reports['actual_manpower'].sum() if not df_reports.empty and 'actual_manpower' in df_reports.columns else 0
    st.metric("Toplam İşçilik", f"{total_labor:,.0f} saat")

with col2:
    total_equipment = df_resources[df_resources['category'] == 'Makina']['value'].sum() if not df_resources.empty and 'category' in df_resources.columns else 0
    st.metric("Toplam Makina", f"{total_equipment:,.0f} adet")

with col3:
    avg_progress = df_work['ilerleme_yuzdesi'].mean() if not df_work.empty and 'ilerleme_yuzdesi' in df_work.columns else 0
    st.metric("Ortalama İlerleme", f"{avg_progress:.1f}%")

with col4:
    total_cost = df_reports['cost'].sum() if not df_reports.empty and 'cost' in df_reports.columns else 0
    st.metric("Toplam Maliyet", f"{total_cost:,.0f} TL")

# --- GRAFİKLER (Ön izleme) ---
if not df_reports.empty:
    st.markdown("### 📈 Veri Görselleri")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        daily_labor = df_reports.groupby('report_date')['actual_manpower'].sum().reset_index()
        daily_labor.columns = ['Tarih', 'İşçilik']
        if not daily_labor.empty:
            fig1 = px.line(daily_labor, x='Tarih', y='İşçilik', title="Günlük İşçilik")
            fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
            st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})
    
    with col_chart2:
        if 'trade' in df_reports.columns:
            trade_summary = df_reports.groupby('trade')['actual_manpower'].sum().reset_index()
            if not trade_summary.empty:
                fig2 = px.pie(trade_summary, names='trade', values='actual_manpower', title="İş Türü Dağılımı", hole=0.4)
                fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
                st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

# --- PDF OLUŞTUR ---
def generate_report_pdf(project_name, df_reports, df_resources, df_work):
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import datetime
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Türkçe karakter desteği
    try:
        pdfmetrics.registerFont(TTFont('Calibri', 'C:/Windows/Fonts/calibri.ttf'))
        font_name = 'Calibri'
    except:
        font_name = 'Helvetica'
    
    # Başlık
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(colors.HexColor("#1E3D59"))
    c.drawString(50, height - 50, "SARCON Portal")
    
    c.setFont(font_name, 14)
    c.setFillColor(colors.black)
    c.drawString(50, height - 80, f"Proje Raporu: {project_name}")
    
    c.setFont(font_name, 10)
    c.drawString(50, height - 100, f"Tarih: {datetime.date.today().strftime('%d.%m.%Y')}")
    
    # Özet Metrikler
    y = height - 140
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "1. Proje Özeti")
    y -= 22
    c.setFont(font_name, 10)
    
    total_labor = df_reports['actual_manpower'].sum() if not df_reports.empty and 'actual_manpower' in df_reports.columns else 0
    total_cost = df_reports['cost'].sum() if not df_reports.empty and 'cost' in df_reports.columns else 0
    avg_progress = df_work['ilerleme_yuzdesi'].mean() if not df_work.empty and 'ilerleme_yuzdesi' in df_work.columns else 0
    
    c.drawString(50, y, f"Toplam Iscilik: {total_labor:,.0f} saat")
    y -= 18
    c.drawString(50, y, f"Toplam Maliyet: {total_cost:,.0f} TL")
    y -= 18
    c.drawString(50, y, f"Ortalama Ilerleme: {avg_progress:.1f}%")
    
    # Detay Veriler
    y -= 35
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "2. Günlük Veriler (Son 10)")
    y -= 22
    c.setFont(font_name, 8)
    
    if not df_reports.empty:
        # Başlık satırı
        c.setFont("Helvetica-Bold", 8)
        c.drawString(50, y, "Tarih")
        c.drawString(120, y, "Aktivite")
        c.drawString(220, y, "Isci")
        c.drawString(290, y, "Makine")
        c.drawString(370, y, "Maliyet")
        y -= 12
        c.setFont(font_name, 8)
        
        for _, row in df_reports.tail(10).iterrows():
            if y < 50:
                c.showPage()
                c.setFont(font_name, 8)
                y = height - 50
            
            date_val = str(row.get('report_date', ''))[:10] if row.get('report_date') else ''
            activity = str(row.get('activity', ''))[:25] if row.get('activity') else ''
            labor = float(row.get('actual_manpower', 0)) if pd.notna(row.get('actual_manpower', 0)) else 0
            machine = float(row.get('actual_machine_hours', 0)) if pd.notna(row.get('actual_machine_hours', 0)) else 0
            cost = float(row.get('cost', 0)) if pd.notna(row.get('cost', 0)) else 0
            
            c.drawString(50, y, date_val)
            c.drawString(120, y, activity)
            c.drawString(220, y, f"{labor:.0f}")
            c.drawString(290, y, f"{machine:.1f}")
            c.drawString(370, y, f"{cost:,.0f}")
            y -= 12
    
    c.save()
    return buffer.getvalue()

# --- TEK BİR PDF İNDİR BUTONU ---
st.markdown("---")
st.markdown("### 📄 Raporu İndir")

if st.button("📄 PDF Rapor İndir", type="primary", use_container_width=True):
    with st.spinner("Rapor oluşturuluyor..."):
        try:
            pdf_data = generate_report_pdf(
                selected_project,
                df_reports,
                df_resources,
                df_work
            )
            
            st.download_button(
                label="PDF Raporu İndir",
                data=pdf_data,
                file_name=f"SARCON_Rapor_{selected_project}_{datetime.date.today()}.pdf",
                mime="application/pdf",
                key="download_pdf_final",
                use_container_width=True
            )
            
            st.success(f"✅ Rapor başarıyla oluşturuldu! PDF'i indirebilirsiniz.")
            
        except Exception as e:
            st.error(f"Rapor oluşturulurken bir hata oluştu: {e}")