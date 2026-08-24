# -*- coding: utf-8 -*-
"""
Created on Thu Aug 20 05:15:13 2026
@author: taric
Updated: 2026-08-24 - Aks, kot ve bölge otomatik oluşturma sistemi eklendi
UI/UX iyileştirmeleri yapıldı, Türkçe karakterler düzeltildi
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import time
from datetime import datetime
from utils.db import supabase, get_user_projects
from utils.styles import apply_global_styles
from utils.top_navbar import render_top_navbar
from utils.animations import (
    animate_plotly,
    loading_spinner,
    toast_success,
    toast_error,
    toast_warning,
    toast_info,
    ENABLE_FADE_IN,
    ENABLE_HOVER
)

st.set_page_config(
    page_title="SARCON Portal | İlerleme Durumu",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

apply_global_styles(is_login=False)
render_top_navbar()

st.markdown('<div class="page-content">', unsafe_allow_html=True)

# ==========================================
# BAŞLIK VE AÇIKLAMA
# ==========================================
st.markdown("""
<div style="border-left: 3px solid #3b82f6; padding-left: 0.8rem; margin-bottom: 1.5rem;">
    <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.3rem;">Bölgesel İlerleme Durumu</h3>
    <p style="color: #737373; margin: 0; font-size: 0.8rem;">
        Projedeki bölgelerin (aks aralıkları) ilerleme durumlarını tanımlayın ve takip edin
    </p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# PROJE SEÇİMİ
# ==========================================
with loading_spinner("Projeler yükleniyor..."):
    projects, err = get_user_projects()
    time.sleep(0.3)

project_names = [p["project_name"] for p in projects] if projects else []

if not project_names:
    toast_warning("Uyarı", "Henüz bir proje oluşturmadınız.")
    st.stop()

selected_project = st.selectbox("Proje Seçin", project_names)
project_id = next(p["id"] for p in projects if p["project_name"] == selected_project)

# ==========================================
# AKS, KOT VE BÖLGE TANIMLAMA
# ==========================================
st.markdown("---")
st.markdown("### Aks ve Kot Tanımlama")

st.info(
    "**Aks Tanımlama:** Yatay akslar harf (A, B, C...), dikey akslar sayı (1, 2, 3...) olarak tanımlanır.\n\n"
    "**Örnek:** X Aksları: A-G → A, B, C, D, E, F, G | Y Aksları: 1-3 → 1, 2, 3 | Kotlar: -10.00, -5.50, 0.00, 3.30, 6.60"
)

col1, col2, col3 = st.columns(3)

with col1:
    x_aks_input = st.text_input(
        "X Aksları (Yatay)",
        placeholder="Örn: A-G",
        help="Başlangıç ve bitiş harflerini tire ile ayırın. Örn: A-G"
    )

with col2:
    y_aks_input = st.text_input(
        "Y Aksları (Dikey)",
        placeholder="Örn: 1-3",
        help="Başlangıç ve bitiş sayılarını tire ile ayırın. Örn: 1-3"
    )

with col3:
    kot_input = st.text_input(
        "Kotlar",
        placeholder="Örn: -10.00, -5.50, 0.00, 3.30, 6.60",
        help="Kotları virgül ile ayırarak girin. Örn: -10.00, -5.50, 0.00"
    )

# ==========================================
# AKS VE KOT DÖNÜŞTÜRME FONKSİYONLARI
# ==========================================
def parse_aks_range(aks_str):
    """Aks aralığını parse et ve liste olarak döndür"""
    if not aks_str:
        return []
    
    aks_str = aks_str.strip()
    
    # Harf aralığı (A-G)
    if '-' in aks_str and aks_str[0].isalpha():
        start, end = aks_str.split('-')
        start_letter = ord(start.strip().upper())
        end_letter = ord(end.strip().upper())
        
        if start_letter > end_letter:
            start_letter, end_letter = end_letter, start_letter
            
        return [chr(i) for i in range(start_letter, end_letter + 1)]
    
    # Sayı aralığı (1-3)
    elif '-' in aks_str:
        parts = aks_str.split('-')
        try:
            start_num = float(parts[0].strip())
            end_num = float(parts[1].strip())
            
            if start_num > end_num:
                start_num, end_num = end_num, start_num
            
            # Tam sayı kontrolü
            if start_num.is_integer() and end_num.is_integer():
                return [str(int(i)) for i in np.arange(start_num, end_num + 1)]
            else:
                return [str(i) for i in np.arange(start_num, end_num + 0.1, 0.5)]
        except:
            return []
    
    return []

def parse_kotlar(kot_str):
    """Kotları parse et ve liste olarak döndür"""
    if not kot_str:
        return []
    
    kot_list = [k.strip() for k in kot_str.split(',') if k.strip()]
    return kot_list

# ==========================================
# BÖLGE ADI OLUŞTURMA
# ==========================================
def generate_region_name(x_aks_list, y_aks_list, kot):
    """Aks ve kot bilgilerinden bölge adı oluştur"""
    if len(x_aks_list) >= 2 and len(y_aks_list) >= 2:
        x_start, x_end = x_aks_list[0], x_aks_list[-1]
        y_start, y_end = y_aks_list[0], y_aks_list[-1]
        return f"{x_start}-{x_end}/{y_start}-{y_end}/{kot}"
    return ""

def generate_regions(x_aks_list, y_aks_list, kot_list):
    """Tüm aks kombinasyonları ve kotlar için bölgeler oluştur"""
    regions = []
    
    if len(x_aks_list) < 2 or len(y_aks_list) < 2 or not kot_list:
        return regions
    
    # Her bir aks aralığı için
    for i in range(len(x_aks_list) - 1):
        for j in range(len(y_aks_list) - 1):
            x_start, x_end = x_aks_list[i], x_aks_list[i + 1]
            y_start, y_end = y_aks_list[j], y_aks_list[j + 1]
            
            for kot in kot_list:
                region_name = f"{x_start}-{x_end}/{y_start}-{y_end}/{kot}"
                regions.append({
                    "region_name": region_name,
                    "x_start": x_start,
                    "x_end": x_end,
                    "y_start": y_start,
                    "y_end": y_end,
                    "kot": kot
                })
    
    return regions

# ==========================================
# AKS VE KOT İŞLEME
# ==========================================
if st.button("Bölgeleri Oluştur", type="primary", use_container_width=True):
    if not x_aks_input or not y_aks_input or not kot_input:
        toast_warning("Uyarı", "Lütfen X Aksları, Y Aksları ve Kotları girin.")
        st.stop()
    
    # Parse et
    x_aks_list = parse_aks_range(x_aks_input)
    y_aks_list = parse_aks_range(y_aks_input)
    kot_list = parse_kotlar(kot_input)
    
    if len(x_aks_list) < 2:
        toast_error("Hata", "X Aksları en az 2 harf içermelidir. Örn: A-G")
        st.stop()
    
    if len(y_aks_list) < 2:
        toast_error("Hata", "Y Aksları en az 2 sayı içermelidir. Örn: 1-3")
        st.stop()
    
    if not kot_list:
        toast_error("Hata", "En az 1 kot girmelisiniz.")
        st.stop()
    
    # Bölgeleri oluştur
    regions = generate_regions(x_aks_list, y_aks_list, kot_list)
    
    if not regions:
        toast_error("Hata", "Bölge oluşturulamadı. Lütfen girdileri kontrol edin.")
        st.stop()
    
    # Mevcut verileri kontrol et
    with loading_spinner("Bölgeler oluşturuluyor..."):
        # Önce mevcut verileri sil
        try:
            supabase.table("project_area_progress").delete().eq("project_id", project_id).execute()
        except:
            pass
        
        # Yeni verileri kaydet
        try:
            for region in regions:
                region_data = {
                    "project_id": project_id,
                    "area_name": region["region_name"],
                    "block_name": f"{region['x_start']}-{region['x_end']}",
                    "aks_x": f"{region['x_start']}-{region['x_end']}",
                    "aks_y": f"{region['y_start']}-{region['y_end']}",
                    "level": region["kot"],
                    "area_type": "Belirsiz",
                    "area_size": 0.0,
                    "assigned_to": "",
                    "status": "not_started",
                    "progress_pct": 0.0,
                    "planned_start": None,
                    "planned_end": None,
                    "actual_start": None,
                    "actual_end": None,
                    "notes": ""
                }
                supabase.table("project_area_progress").insert(region_data).execute()
            
            time.sleep(0.3)
            toast_success("Başarılı", f"{len(regions)} bölge oluşturuldu!")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            toast_error("Hata", f"Kayıt sırasında hata oluştu: {e}")

# ==========================================
# MEVCUT VERİLERİ ÇEK
# ==========================================
@st.cache_data(ttl=300)
def get_area_progress(project_id):
    try:
        response = supabase.table("project_area_progress").select("*").eq("project_id", project_id).execute()
        return response.data if response.data else []
    except:
        return []

with loading_spinner("Veriler yükleniyor..."):
    existing_data = get_area_progress(project_id)
    time.sleep(0.3)

# Session state
if "area_df" not in st.session_state or st.session_state.get("current_project") != project_id:
    st.session_state.current_project = project_id
    if existing_data:
        st.session_state.area_df = pd.DataFrame(existing_data)
    else:
        st.session_state.area_df = pd.DataFrame(columns=[
            "area_name", "block_name", "aks_x", "aks_y", "level",
            "area_type", "area_size", "assigned_to", "status", "progress_pct",
            "planned_start", "planned_end", "actual_start", "actual_end", "notes"
        ])

# ==========================================
# VERİ DÜZENLEME TABLOSU
# ==========================================
if not st.session_state.area_df.empty:
    st.markdown("---")
    st.markdown("### Bölge Verileri Düzenle")
    st.caption("Aşağıdaki tabloda bölge bilgilerini güncelleyebilirsiniz.")

# Data Editor
edited_area_df = st.data_editor(
    st.session_state.area_df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "area_name": st.column_config.TextColumn("Bölge Adı", required=True),
        "block_name": st.column_config.TextColumn("Blok", disabled=True),
        "aks_x": st.column_config.TextColumn("X Aksları", disabled=True),
        "aks_y": st.column_config.TextColumn("Y Aksları", disabled=True),
        "level": st.column_config.TextColumn("Kot", disabled=True),
        "area_type": st.column_config.SelectboxColumn(
            "Alan Türü",
            options=["Belirsiz", "Daire", "Ofis", "Koridor", "Merdiven", "Asansör", "Depo", "Diğer"],
            default="Belirsiz"
        ),
        "area_size": st.column_config.NumberColumn("Büyüklük (m²)", min_value=0.0, step=0.5, format="%.1f"),
        "assigned_to": st.column_config.TextColumn("Sorumlu"),
        "status": st.column_config.SelectboxColumn(
            "Durum",
            options=["not_started", "in_progress", "completed", "delayed"],
            default="not_started"
        ),
        "progress_pct": st.column_config.NumberColumn("İlerleme %", min_value=0.0, max_value=100.0, step=0.5, format="%.1f%%"),
        "planned_start": st.column_config.DateColumn("Planlanan Başlangıç"),
        "planned_end": st.column_config.DateColumn("Planlanan Bitiş"),
        "actual_start": st.column_config.DateColumn("Gerçek Başlangıç"),
        "actual_end": st.column_config.DateColumn("Gerçek Bitiş"),
        "notes": st.column_config.TextColumn("Notlar")
    },
    key="area_grid",
    hide_index=True
)

st.session_state.area_df = edited_area_df

# ==========================================
# ÖZET VE GRAFİKLER
# ==========================================
if not edited_area_df.empty:
    st.markdown("---")
    st.markdown("### Bölgesel İlerleme Özeti")
    
    # Durum etiketlerini Türkçeleştir
    status_labels = {
        'not_started': 'Başlanmadı',
        'in_progress': 'Devam Ediyor',
        'completed': 'Tamamlandı',
        'delayed': 'Gecikti'
    }
    
    total_areas = len(edited_area_df)
    
    # Status dağılımı
    status_counts = edited_area_df['status'].value_counts().to_dict()
    completed = status_counts.get('completed', 0)
    in_progress = status_counts.get('in_progress', 0)
    delayed = status_counts.get('delayed', 0)
    not_started = status_counts.get('not_started', 0)
    
    avg_progress = edited_area_df['progress_pct'].mean() if not edited_area_df.empty else 0
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="animate-card" style="
            background-color: #141414;
            padding: 0.8rem;
            border-radius: 12px;
            border: 1px solid #262626;
            text-align: center;
        ">
            <p style="color: #737373; font-size: 0.6rem; margin: 0;">Toplam Bölge</p>
            <h4 style="color: #ffffff; margin: 0.2rem 0;">{total_areas}</h4>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        pct_completed = (completed/total_areas*100) if total_areas > 0 else 0
        st.markdown(f"""
        <div class="animate-card" style="
            background-color: #141414;
            padding: 0.8rem;
            border-radius: 12px;
            border: 1px solid #262626;
            text-align: center;
        ">
            <p style="color: #737373; font-size: 0.6rem; margin: 0;">Tamamlanan</p>
            <h4 style="color: #22c55e; margin: 0.2rem 0;">{completed}</h4>
            <p style="color: #737373; font-size: 0.6rem; margin: 0;">%{pct_completed:.1f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="animate-card" style="
            background-color: #141414;
            padding: 0.8rem;
            border-radius: 12px;
            border: 1px solid #262626;
            text-align: center;
        ">
            <p style="color: #737373; font-size: 0.6rem; margin: 0;">Devam Eden</p>
            <h4 style="color: #fbbf24; margin: 0.2rem 0;">{in_progress}</h4>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="animate-card" style="
            background-color: #141414;
            padding: 0.8rem;
            border-radius: 12px;
            border: 1px solid #262626;
            text-align: center;
        ">
            <p style="color: #737373; font-size: 0.6rem; margin: 0;">Geciken</p>
            <h4 style="color: #f87171; margin: 0.2rem 0;">{delayed}</h4>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="animate-card" style="
            background-color: #141414;
            padding: 0.8rem;
            border-radius: 12px;
            border: 1px solid #262626;
            text-align: center;
        ">
            <p style="color: #737373; font-size: 0.6rem; margin: 0;">Ortalama İlerleme</p>
            <h4 style="color: #3b82f6; margin: 0.2rem 0;">{avg_progress:.1f}%</h4>
        </div>
        """, unsafe_allow_html=True)
    
    # Grafikler
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # Blok bazında ilerleme (x aksları bazında)
        if 'block_name' in edited_area_df.columns and not edited_area_df.empty:
            block_summary = edited_area_df.groupby('block_name')['progress_pct'].mean().reset_index()
            if not block_summary.empty:
                fig = px.bar(
                    block_summary,
                    x='block_name',
                    y='progress_pct',
                    title='X Aksları Bazında Ortalama İlerleme',
                    color='block_name',
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    showlegend=False,
                    xaxis_title="X Aks Aralığı",
                    yaxis_title="Ortalama İlerleme (%)"
                )
                fig = animate_plotly(fig)
                st.plotly_chart(fig, use_container_width=True)
    
    with col_chart2:
        # Kot bazında ilerleme
        if 'level' in edited_area_df.columns and not edited_area_df.empty:
            level_summary = edited_area_df.groupby('level')['progress_pct'].mean().reset_index()
            level_summary = level_summary.sort_values('level')
            if not level_summary.empty:
                fig = px.bar(
                    level_summary,
                    x='level',
                    y='progress_pct',
                    title='Kot Bazında Ortalama İlerleme',
                    color='level',
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    showlegend=False,
                    xaxis_title="Kot",
                    yaxis_title="Ortalama İlerleme (%)"
                )
                fig = animate_plotly(fig)
                st.plotly_chart(fig, use_container_width=True)
    
    # Durum dağılımı pasta grafiği
    status_df = pd.DataFrame({
        'Durum': [status_labels.get(s, s) for s in edited_area_df['status']],
        'Adet': 1
    })
    status_summary = status_df.groupby('Durum').count().reset_index()
    
    if not status_summary.empty:
        fig = px.pie(
            status_summary,
            names='Durum',
            values='Adet',
            title='Durum Dağılımı',
            hole=0.4,
            color_discrete_sequence=['#94a3b8', '#fbbf24', '#22c55e', '#f87171']
        )
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        fig = animate_plotly(fig)
        st.plotly_chart(fig, use_container_width=True)

# ==========================================
# KAYDET BUTONU
# ==========================================
st.markdown("---")

col_save, col_reset = st.columns([3, 1])

with col_save:
    if st.button("Bölgesel Verileri Kaydet", type="primary", use_container_width=True):
        rows_to_save = edited_area_df.to_dict(orient="records") if not edited_area_df.empty else []
        clean_rows = [r for r in rows_to_save if str(r.get("area_name", "")).strip()]
        
        if clean_rows:
            try:
                with loading_spinner("Veriler kaydediliyor..."):
                    # NaN değerleri temizle
                    for r in clean_rows:
                        for key in ["area_size", "progress_pct"]:
                            if key in r:
                                if pd.isna(r.get(key)) or np.isinf(r.get(key, 0)):
                                    r[key] = 0.0
                        
                        # Tarih alanlarını temizle
                        for key in ["planned_start", "planned_end", "actual_start", "actual_end"]:
                            if key in r:
                                if pd.isna(r.get(key)):
                                    r[key] = None
                    
                    # Mevcut verileri sil
                    supabase.table("project_area_progress").delete().eq("project_id", project_id).execute()
                    
                    # Yeni verileri ekle
                    for r in clean_rows:
                        r["project_id"] = project_id
                        r.pop("id", None)
                        supabase.table("project_area_progress").insert(r).execute()
                    
                    time.sleep(0.3)
                toast_success("Başarılı", f"{len(clean_rows)} bölge kaydedildi!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                toast_error("Hata", f"Kayıt sırasında hata oluştu: {str(e)}")
        else:
            toast_warning("Uyarı", "Kaydedilecek veri bulunamadı.")

with col_reset:
    if st.button("Sayfayı Sıfırla", use_container_width=True):
        st.session_state.pop("area_df", None)
        st.session_state.pop("current_project", None)
        st.cache_data.clear()
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)