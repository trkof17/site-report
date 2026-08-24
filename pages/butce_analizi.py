# -*- coding: utf-8 -*-
"""
Created on Thu Aug 20 02:11:08 2026
@author: taric
Updated: 2026-08-21 - Formülasyon ile sapma hesaplama, gerçekleşen değer analizi eklendi
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import time
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
    page_title="SARCON Portal | Bütçe Analizi",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

apply_global_styles(is_login=False)
render_top_navbar()

st.markdown('<div class="page-content">', unsafe_allow_html=True)

st.markdown("""
<div style="border-left: 3px solid #3b82f6; padding-left: 0.8rem; margin-bottom: 1.5rem;">
    <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.3rem;">📊 Bütçe ve Analiz</h3>
    <p style="color: #737373; margin: 0; font-size: 0.8rem;">
        Bütçe girişi, sapma analizi ve gerçekleşen değer analizi (EVM)
        <br>Sapma = Planlanan - Gerçekleşen | Sapma % = (Sapma / Planlanan) × 100
    </p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 1. PROJE SEÇİMİ
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
# 2. VERİLERİ ÇEK
# ==========================================
@st.cache_data(ttl=300)
def get_project_budgets(project_id):
    try:
        response = supabase.table("project_budgets").select("*").eq("project_id", project_id).execute()
        return response.data if response.data else []
    except:
        return []

@st.cache_data(ttl=300)
def get_actual_costs(project_id):
    try:
        response = supabase.table("project_costs").select("*").eq("project_id", project_id).execute()
        return response.data if response.data else []
    except:
        return []

@st.cache_data(ttl=300)
def get_work_progress(project_id):
    try:
        response = supabase.table("daily_work_progress").select("*").eq("project_id", project_id).execute()
        return response.data if response.data else []
    except:
        return []

@st.cache_data(ttl=300)
def get_project_items(project_id):
    try:
        response = supabase.table("project_items").select("*").eq("project_id", project_id).execute()
        return response.data if response.data else []
    except:
        return []

with loading_spinner("Veriler yükleniyor..."):
    existing_budgets = get_project_budgets(project_id)
    actual_costs_data = get_actual_costs(project_id)
    work_data = get_work_progress(project_id)
    items_data = get_project_items(project_id)
    time.sleep(0.3)

df_actual = pd.DataFrame(actual_costs_data) if actual_costs_data else pd.DataFrame()
df_work = pd.DataFrame(work_data) if work_data else pd.DataFrame()
df_items = pd.DataFrame(items_data) if items_data else pd.DataFrame()

# ==========================================
# 3. SESSION STATE
# ==========================================
if "budget_df" not in st.session_state or st.session_state.get("current_project") != project_id:
    st.session_state.current_project = project_id
    if existing_budgets:
        df = pd.DataFrame(existing_budgets)
        
        # Gerçekleşen verileri hesapla (kategori bazında)
        if not df_actual.empty:
            for idx, row in df.iterrows():
                category = row.get("budget_category")
                if category:
                    actual_amount = df_actual[df_actual["cost_category"] == category]["total_cost"].sum()
                    df.loc[idx, "actual_amount"] = actual_amount
        else:
            df["actual_amount"] = 0
        
        # Sapma hesapla (formülasyon)
        df["planned_amount"] = df["planned_amount"].fillna(0)
        df["actual_amount"] = df["actual_amount"].fillna(0)
        df["variance"] = df["planned_amount"] - df["actual_amount"]
        df["variance_pct"] = np.where(
            df["planned_amount"] > 0,
            (df["variance"] / df["planned_amount"]) * 100,
            0
        )
        
        st.session_state.budget_df = df
    else:
        st.session_state.budget_df = pd.DataFrame(columns=[
            "budget_category", "budget_name", "planned_amount", 
            "actual_amount", "variance", "variance_pct", "notes"
        ])

# ==========================================
# 4. VERİ GİRİŞİ - EXCEL-LIKE
# ==========================================
st.markdown("### 📝 Bütçe Girdileri")
st.caption("📌 Planlanan bütçeyi girin. Gerçekleşen, sapma ve sapma % otomatik hesaplanır.")

edited_budget_df = st.data_editor(
    st.session_state.budget_df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "budget_category": st.column_config.SelectboxColumn(
            "Kategori",
            options=["İşçilik", "Makina", "Malzeme", "Alt Yüklenici", "Genel Gider"],
            required=True,
            width="medium"
        ),
        "budget_name": st.column_config.TextColumn(
            "Bütçe Kalemi",
            required=True,
            width="large"
        ),
        "planned_amount": st.column_config.NumberColumn(
            "Planlanan (TL)",
            min_value=0.0,
            step=100.0,
            format="%.2f",
            width="medium"
        ),
        "actual_amount": st.column_config.NumberColumn(
            "Gerçekleşen (TL)",
            disabled=True,
            format="%.2f",
            width="medium"
        ),
        "variance": st.column_config.NumberColumn(
            "Sapma (TL)",
            disabled=True,
            format="%.2f",
            width="medium"
        ),
        "variance_pct": st.column_config.NumberColumn(
            "Sapma %",
            disabled=True,
            format="%.1f%%",
            width="small"
        ),
        "notes": st.column_config.TextColumn(
            "Notlar",
            width="medium"
        )
    },
    key="budget_grid"
)

# ==========================================
# 5. OTOMATİK HESAPLAMALAR (FORMÜLASYON)
# ==========================================
if not edited_budget_df.empty:
    # Gerçekleşen değerleri kategori bazında hesapla
    if not df_actual.empty:
        for idx, row in edited_budget_df.iterrows():
            category = row.get("budget_category")
            if category:
                actual_amount = df_actual[df_actual["cost_category"] == category]["total_cost"].sum()
                edited_budget_df.at[idx, "actual_amount"] = actual_amount
            else:
                edited_budget_df.at[idx, "actual_amount"] = 0
    else:
        edited_budget_df["actual_amount"] = 0
    
    # Sapma hesapla (formülasyon)
    # Sapma = Planlanan - Gerçekleşen
    edited_budget_df["planned_amount"] = edited_budget_df["planned_amount"].fillna(0)
    edited_budget_df["actual_amount"] = edited_budget_df["actual_amount"].fillna(0)
    edited_budget_df["variance"] = edited_budget_df["planned_amount"] - edited_budget_df["actual_amount"]
    
    # Sapma % = (Sapma / Planlanan) × 100
    edited_budget_df["variance_pct"] = np.where(
        edited_budget_df["planned_amount"] > 0,
        (edited_budget_df["variance"] / edited_budget_df["planned_amount"]) * 100,
        0
    )

st.session_state.budget_df = edited_budget_df

# ==========================================
# 6. BÜTÇE ÖZETİ
# ==========================================
if not edited_budget_df.empty:
    st.markdown("---")
    
    df_summary = edited_budget_df.fillna(0)
    total_planned = df_summary["planned_amount"].sum()
    total_actual = df_summary["actual_amount"].sum()
    total_variance = total_planned - total_actual
    total_variance_pct = (total_variance / total_planned * 100) if total_planned > 0 else 0
    
    # Özet kartları
    st.markdown("### 📊 Bütçe Özeti")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="animate-card" style="
            background-color: #141414;
            padding: 1.2rem;
            border-radius: 12px;
            border: 1px solid #262626;
            text-align: center;
        ">
            <p style="color: #737373; font-size: 0.8rem; margin: 0;">📋 Toplam Planlanan</p>
            <h3 style="color: #3b82f6; margin: 0.3rem 0;">{total_planned:,.0f} TL</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="animate-card" style="
            background-color: #141414;
            padding: 1.2rem;
            border-radius: 12px;
            border: 1px solid #262626;
            text-align: center;
        ">
            <p style="color: #737373; font-size: 0.8rem; margin: 0;">📈 Toplam Gerçekleşen</p>
            <h3 style="color: #22c55e; margin: 0.3rem 0;">{total_actual:,.0f} TL</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="animate-card" style="
            background-color: #141414;
            padding: 1.2rem;
            border-radius: 12px;
            border: 1px solid #262626;
            text-align: center;
        ">
            <p style="color: #737373; font-size: 0.8rem; margin: 0;">📉 Toplam Sapma</p>
            <h3 style="color: {'#f87171' if total_variance < 0 else '#fbbf24'}; margin: 0.3rem 0;">{total_variance:,.0f} TL</h3>
            <p style="color: #737373; font-size: 0.8rem; margin: 0;">{total_variance_pct:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="animate-card" style="
            background-color: #141414;
            padding: 1.2rem;
            border-radius: 12px;
            border: 1px solid #262626;
            text-align: center;
        ">
            <p style="color: #737373; font-size: 0.8rem; margin: 0;">📊 Ortalama Sapma</p>
            <h3 style="color: {'#22c55e' if total_variance_pct >= 0 else '#f87171'}; margin: 0.3rem 0;">{total_variance_pct:.1f}%</h3>
        </div>
        """, unsafe_allow_html=True)
    
    # Kategori bazında özet
    category_summary = df_summary.groupby("budget_category")[["planned_amount", "actual_amount"]].sum().reset_index()
    category_summary["variance"] = category_summary["planned_amount"] - category_summary["actual_amount"]
    category_summary["variance_pct"] = np.where(
        category_summary["planned_amount"] > 0,
        (category_summary["variance"] / category_summary["planned_amount"]) * 100,
        0
    )
    
    # Kategori grafiği
    st.markdown("### 📊 Kategori Bazında Bütçe vs Gerçekleşen")
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Planlanan",
        x=category_summary["budget_category"],
        y=category_summary["planned_amount"],
        marker_color="#2563eb"
    ))
    fig.add_trace(go.Bar(
        name="Gerçekleşen",
        x=category_summary["budget_category"],
        y=category_summary["actual_amount"],
        marker_color="#34d399"
    ))
    
    fig.update_layout(
        barmode="group",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(font=dict(color="white")),
        xaxis=dict(tickfont=dict(color="white")),
        yaxis=dict(tickfont=dict(color="white")),
        title_font=dict(color="white")
    )
    
    # Animasyon ekle
    fig = animate_plotly(fig)
    st.plotly_chart(fig, use_container_width=True)
    
    # Sapma detayları
    with st.expander("📋 Kategori Bazında Sapma Detayları"):
        st.dataframe(
            category_summary,
            use_container_width=True,
            column_config={
                "budget_category": "Kategori",
                "planned_amount": "Planlanan (TL)",
                "actual_amount": "Gerçekleşen (TL)",
                "variance": "Sapma (TL)",
                "variance_pct": "Sapma %"
            }
        )

# ==========================================
# 7. GERÇEKLEŞEN DEĞER ANALİZİ (EVM)
# ==========================================
if not df_work.empty and not df_items.empty:
    st.markdown("---")
    st.markdown("### 📈 Gerçekleşen Değer Analizi (EVM)")
    
    # EVM hesaplamaları
    total_quantity = df_items["quantity"].sum() if "quantity" in df_items.columns else 0
    total_completed = df_items["completed_quantity"].sum() if "completed_quantity" in df_items.columns else 0
    total_unit_price = df_items["unit_price"].sum() if "unit_price" in df_items.columns else 0
    
    # Planlanan Değer (PV) = Planlanan işin bütçesi
    planned_value = total_quantity * total_unit_price if total_quantity > 0 else 0
    
    # Kazanılmış Değer (EV) = Tamamlanan işin bütçesi
    earned_value = total_completed * total_unit_price if total_completed > 0 else 0
    
    # Gerçekleşen Maliyet (AC) = Gerçekleşen maliyetler
    actual_cost = df_actual["total_cost"].sum() if not df_actual.empty else 0
    
    # Performans metrikleri
    cost_variance = earned_value - actual_cost
    schedule_variance = earned_value - planned_value
    cost_performance_index = earned_value / actual_cost if actual_cost > 0 else 0
    schedule_performance_index = earned_value / planned_value if planned_value > 0 else 0
    
    # EVM Özet kartları
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="animate-card" style="
            background-color: #141414;
            padding: 1rem;
            border-radius: 12px;
            border: 1px solid #262626;
            text-align: center;
        ">
            <p style="color: #737373; font-size: 0.7rem; margin: 0;">📊 PV</p>
            <h4 style="color: #3b82f6; margin: 0.2rem 0;">{planned_value:,.0f} TL</h4>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="animate-card" style="
            background-color: #141414;
            padding: 1rem;
            border-radius: 12px;
            border: 1px solid #262626;
            text-align: center;
        ">
            <p style="color: #737373; font-size: 0.7rem; margin: 0;">✅ EV</p>
            <h4 style="color: #22c55e; margin: 0.2rem 0;">{earned_value:,.0f} TL</h4>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="animate-card" style="
            background-color: #141414;
            padding: 1rem;
            border-radius: 12px;
            border: 1px solid #262626;
            text-align: center;
        ">
            <p style="color: #737373; font-size: 0.7rem; margin: 0;">💰 AC</p>
            <h4 style="color: #f87171; margin: 0.2rem 0;">{actual_cost:,.0f} TL</h4>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        cpi_color = "#22c55e" if cost_performance_index >= 1 else "#f87171"
        st.markdown(f"""
        <div class="animate-card" style="
            background-color: #141414;
            padding: 1rem;
            border-radius: 12px;
            border: 1px solid #262626;
            text-align: center;
        ">
            <p style="color: #737373; font-size: 0.7rem; margin: 0;">📈 CPI</p>
            <h4 style="color: {cpi_color}; margin: 0.2rem 0;">{cost_performance_index:.2f}</h4>
            <p style="color: #737373; font-size: 0.7rem; margin: 0;">{'✅ İyi' if cost_performance_index >= 1 else '⚠️ Kötü'}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # EVM grafiği
    evm_data = pd.DataFrame({
        "Metrik": ["Planlanan Değer (PV)", "Kazanılmış Değer (EV)", "Gerçekleşen Maliyet (AC)"],
        "Tutar": [planned_value, earned_value, actual_cost]
    })
    
    fig_evm = px.bar(
        evm_data,
        x="Metrik",
        y="Tutar",
        text="Tutar",
        color="Metrik",
        color_discrete_map={
            "Planlanan Değer (PV)": "#2563eb",
            "Kazanılmış Değer (EV)": "#34d399",
            "Gerçekleşen Maliyet (AC)": "#f87171"
        }
    )
    fig_evm.update_traces(
        texttemplate='%{text:,.0f} TL',
        textposition='outside',
        textfont=dict(color='#a3a3a3', size=11)
    )
    fig_evm.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        xaxis=dict(tickfont=dict(color="white")),
        yaxis=dict(tickfont=dict(color="white"))
    )
    
    # Animasyon ekle
    fig_evm = animate_plotly(fig_evm)
    st.plotly_chart(fig_evm, use_container_width=True)
    
    # EVM yorum - Toast olarak göster
    if cost_performance_index >= 1:
        toast_success("Maliyet Performansı", f"CPI: {cost_performance_index:.2f} - Maliyet hedefinin altında ✅")
    else:
        toast_warning("Maliyet Performansı", f"CPI: {cost_performance_index:.2f} - Maliyet hedefinin üstünde ⚠️")
    
    if schedule_performance_index >= 1:
        toast_success("Program Performansı", f"SPI: {schedule_performance_index:.2f} - Program hedefinin altında ✅")
    else:
        toast_warning("Program Performansı", f"SPI: {schedule_performance_index:.2f} - Program hedefinin üstünde ⚠️")
    
    st.markdown(f"""
    <div class="animate-card" style="
        background-color: #141414;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #262626;
        margin-top: 1rem;
    ">
        <p style="color: #737373; margin: 0.2rem 0;">📌 <strong style="color: #ffffff;">EVM Yorumu</strong></p>
        <p style="color: #737373; margin: 0.2rem 0;">• <strong style="color: #ffffff;">CPI:</strong> {cost_performance_index:.2f} → {'✅ Maliyet hedefinin altında' if cost_performance_index >= 1 else '⚠️ Maliyet hedefinin üstünde'}</p>
        <p style="color: #737373; margin: 0.2rem 0;">• <strong style="color: #ffffff;">SPI:</strong> {schedule_performance_index:.2f} → {'✅ Program hedefinin altında' if schedule_performance_index >= 1 else '⚠️ Program hedefinin üstünde'}</p>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 8. KAYDET
# ==========================================
st.markdown("---")

if st.button("💾 Bütçe Verilerini Kaydet", type="primary", use_container_width=True):
    rows_to_save = edited_budget_df.to_dict(orient="records") if not edited_budget_df.empty else []
    clean_rows = [r for r in rows_to_save if str(r.get("budget_name", "")).strip()]
    
    if clean_rows:
        try:
            with loading_spinner("Bütçe verileri kaydediliyor..."):
                # Temizleme
                for r in clean_rows:
                    r["project_id"] = project_id
                    r.pop("id", None)
                    
                    for key in ["planned_amount", "actual_amount", "variance", "variance_pct"]:
                        if pd.isna(r.get(key)) or np.isinf(r.get(key, 0)):
                            r[key] = 0.0
                    
                    if r.get("budget_category") == "":
                        r["budget_category"] = None
                    if r.get("notes") == "":
                        r["notes"] = None
                
                # Eski verileri sil
                supabase.table("project_budgets").delete().eq("project_id", project_id).execute()
                
                # Yeni verileri ekle
                for r in clean_rows:
                    supabase.table("project_budgets").insert(r).execute()
                
                toast_success("Başarılı", f"{len(clean_rows)} bütçe kalemi kaydedildi!")
                st.cache_data.clear()
                time.sleep(0.5)
                st.rerun()
            
        except Exception as e:
            toast_error("Hata", f"Kayıt sırasında hata oluştu: {e}")
    else:
        toast_warning("Uyarı", "Kaydedilecek veri bulunamadı.")

# ==========================================
# 9. KULLANIM KILAVUZU
# ==========================================
with st.expander("ℹ️ Bütçe Analizi Kullanım Kılavuzu"):
    st.markdown("""
    **📌 Bütçe Analizi Nasıl Kullanılır?**
    
    1. **Bütçe Kalemi Girin:** Kategori ve kalem adı girin.
    2. **Planlanan Tutarı Girin:** Bütçelenen tutarı girin.
    3. **Gerçekleşen Tutar:** Otomatik olarak Maliyet Girişi'nden çekilir.
    4. **Sapma:** Otomatik hesaplanır (Planlanan - Gerçekleşen).
    5. **Sapma %:** Otomatik hesaplanır (Sapma / Planlanan × 100).
    6. **EVM Analizi:** Gerçekleşen değer analizi otomatik gösterilir.
    
    **📊 EVM Metrikleri:**
    - **PV:** Planlanan Değer (Planlanan işin bütçesi)
    - **EV:** Kazanılmış Değer (Tamamlanan işin bütçesi)
    - **AC:** Gerçekleşen Maliyet
    - **CPI:** Maliyet Performans İndeksi (EV/AC) - 1'den büyük iyi
    - **SPI:** Program Performans İndeksi (EV/PV) - 1'den büyük iyi
    """)

st.markdown('</div>', unsafe_allow_html=True)