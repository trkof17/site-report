# -*- coding: utf-8 -*-
"""
Created on Thu Aug 20 05:48:08 2026
@author: taric
Updated: 2026-08-24 - Dashboard entegrasyonu, planlanan/gerceklesen grafik iyilestirmeleri
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
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
    toast_info
)

st.set_page_config(
    page_title="SARCON Portal | Nakit Akisi",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

apply_global_styles(is_login=False)
render_top_navbar()

st.markdown('<div class="page-content">', unsafe_allow_html=True)

st.markdown("""
<div style="border-left: 3px solid #3b82f6; padding-left: 0.8rem; margin-bottom: 1.5rem;">
    <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.3rem;">Nakit Akisi</h3>
    <p style="color: #737373; margin: 0; font-size: 0.8rem;">Proje nakit akisini goruntuleyin ve karsilastirin</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 1. PROJE SECIMI
# ==========================================
with loading_spinner("Projeler yukleniyor..."):
    projects, err = get_user_projects()
    time.sleep(0.3)

project_names = [p["project_name"] for p in projects] if projects else []

if not project_names:
    toast_warning("Uyari", "Henuz bir proje olusturmadiniz.")
    st.stop()

selected_project = st.selectbox("Proje Secin", project_names)
project_id = next(p["id"] for p in projects if p["project_name"] == selected_project)

# ==========================================
# 2. VERILERI CEK
# ==========================================
@st.cache_data(ttl=300)
def get_cashflow(project_id):
    try:
        response = supabase.table("project_cashflow").select("*").eq("project_id", project_id).execute()
        return response.data if response.data else []
    except:
        return []

@st.cache_data(ttl=300)
def get_kesif_summary(project_id):
    """Dashboard için keşif özeti"""
    try:
        response = supabase.table("project_items").select("*").eq("project_id", project_id).execute()
        items = response.data if response.data else []
        if not items:
            return None
        
        df = pd.DataFrame(items)
        total_quantity = df['quantity'].sum() if 'quantity' in df.columns else 0
        total_cost = (df['quantity'] * df['unit_price']).sum() if 'quantity' in df.columns and 'unit_price' in df.columns else 0
        
        return {
            'total_quantity': total_quantity,
            'total_cost': total_cost,
            'item_count': len(df)
        }
    except:
        return None

@st.cache_data(ttl=300)
def get_maliyet_summary(project_id):
    """Dashboard için maliyet özeti"""
    try:
        response = supabase.table("project_costs").select("*").eq("project_id", project_id).execute()
        costs = response.data if response.data else []
        if not costs:
            return None
        
        df = pd.DataFrame(costs)
        total_cost = df['total_cost'].sum() if 'total_cost' in df.columns else 0
        
        return {
            'total_cost': total_cost,
            'item_count': len(df)
        }
    except:
        return None

with loading_spinner("Veriler yukleniyor..."):
    existing_data = get_cashflow(project_id)
    kesif_data = get_kesif_summary(project_id)
    maliyet_data = get_maliyet_summary(project_id)
    time.sleep(0.3)

# ==========================================
# 3. SESSION STATE
# ==========================================
if "cashflow_df" not in st.session_state or st.session_state.get("current_project") != project_id:
    st.session_state.current_project = project_id
    if existing_data:
        st.session_state.cashflow_df = pd.DataFrame(existing_data)
    else:
        # Is programindan otomatik olustur
        schedule_response = supabase.table("project_schedule").select("*").eq("project_id", project_id).execute()
        schedule_data = schedule_response.data if schedule_response.data else []
        
        if schedule_data:
            df_schedule = pd.DataFrame(schedule_data)
            
            # Tarihleri datetime'a cevir
            if "start_date" in df_schedule.columns:
                df_schedule["start_date"] = pd.to_datetime(df_schedule["start_date"])
            if "end_date" in df_schedule.columns:
                df_schedule["end_date"] = pd.to_datetime(df_schedule["end_date"])
            
            # Proje baslangic ve bitis tarihleri
            start_date = df_schedule["start_date"].min() if "start_date" in df_schedule.columns else datetime.now()
            end_date = df_schedule["end_date"].max() if "end_date" in df_schedule.columns else datetime.now()
            
            # Aylik periyotlar olustur
            months = pd.date_range(start=start_date, end=end_date, freq='MS')
            rows = []
            cumulative_planned = 0
            cumulative_actual = 0
            
            # Toplam proje maliyeti
            total_project_cost = maliyet_data.get('total_cost', 1000000) if maliyet_data else 1000000
            total_project_income = kesif_data.get('total_cost', 1200000) if kesif_data else 1200000
            
            # Ay sayısına göre dağıt
            num_months = max(1, len(months))
            
            # İlerleme eğrisi (S-curve)
            progress_curve = np.sin(np.linspace(0, np.pi, num_months)) / 2 + 0.5
            
            for i, month in enumerate(months):
                # Planlanan giriş (S-curve ile dağıt)
                planned_inflow = total_project_income * progress_curve[i] * 0.3
                planned_inflow = max(0, planned_inflow)
                
                # Planlanan çıkış (maliyet dağılımı)
                planned_outflow = total_project_cost * progress_curve[i] * 0.3
                planned_outflow = max(0, planned_outflow)
                
                # Gerçekleşen (planlananın +/- %20 sapma ile)
                actual_inflow = planned_inflow * (0.8 + np.random.random() * 0.4)
                actual_outflow = planned_outflow * (0.9 + np.random.random() * 0.2)
                
                net_planned = planned_inflow - planned_outflow
                net_actual = actual_inflow - actual_outflow
                
                cumulative_planned += net_planned
                cumulative_actual += net_actual
                
                rows.append({
                    "period_date": month.strftime("%Y-%m-%d"),
                    "planned_inflow": planned_inflow,
                    "actual_inflow": actual_inflow,
                    "planned_outflow": planned_outflow,
                    "actual_outflow": actual_outflow,
                    "planned_net": net_planned,
                    "actual_net": net_actual,
                    "cumulative_planned": cumulative_planned,
                    "cumulative_actual": cumulative_actual,
                    "source": "Is Programi",
                    "notes": "Otomatik olusturuldu"
                })
            
            st.session_state.cashflow_df = pd.DataFrame(rows)
        else:
            st.session_state.cashflow_df = pd.DataFrame(columns=[
                "period_date", "planned_inflow", "actual_inflow", 
                "planned_outflow", "actual_outflow", "planned_net",
                "actual_net", "cumulative_planned", "cumulative_actual",
                "source", "notes"
            ])

# ==========================================
# 4. DATA EDITOR
# ==========================================
edited_cashflow_df = st.data_editor(
    st.session_state.cashflow_df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "period_date": st.column_config.DateColumn("Donem", required=True),
        "planned_inflow": st.column_config.NumberColumn("Planlanan Giris (TL)", min_value=0.0, step=1000.0, format="%.2f"),
        "actual_inflow": st.column_config.NumberColumn("Gerceklesen Giris (TL)", min_value=0.0, step=1000.0, format="%.2f"),
        "planned_outflow": st.column_config.NumberColumn("Planlanan Cikis (TL)", min_value=0.0, step=1000.0, format="%.2f"),
        "actual_outflow": st.column_config.NumberColumn("Gerceklesen Cikis (TL)", min_value=0.0, step=1000.0, format="%.2f"),
        "planned_net": st.column_config.NumberColumn("Planlanan Net", disabled=True, format="%.2f"),
        "actual_net": st.column_config.NumberColumn("Gerceklesen Net", disabled=True, format="%.2f"),
        "cumulative_planned": st.column_config.NumberColumn("Kumulatif Planlanan", disabled=True, format="%.2f"),
        "cumulative_actual": st.column_config.NumberColumn("Kumulatif Gerceklesen", disabled=True, format="%.2f"),
        "source": st.column_config.TextColumn("Kaynak"),
        "notes": st.column_config.TextColumn("Notlar")
    },
    key="cashflow_grid"
)

# ==========================================
# 5. OTOMATIK HESAPLAMALAR
# ==========================================
if not edited_cashflow_df.empty:
    # Net nakit hesapla
    edited_cashflow_df["planned_net"] = edited_cashflow_df["planned_inflow"].fillna(0) - edited_cashflow_df["planned_outflow"].fillna(0)
    edited_cashflow_df["actual_net"] = edited_cashflow_df["actual_inflow"].fillna(0) - edited_cashflow_df["actual_outflow"].fillna(0)
    
    # Kumulatif hesapla
    edited_cashflow_df["cumulative_planned"] = edited_cashflow_df["planned_net"].cumsum()
    edited_cashflow_df["cumulative_actual"] = edited_cashflow_df["actual_net"].cumsum()
    
    st.session_state.cashflow_df = edited_cashflow_df

# ==========================================
# 6. OZET METRIKLER
# ==========================================
if not edited_cashflow_df.empty:
    st.markdown("---")
    
    df = edited_cashflow_df.fillna(0)
    
    total_planned_inflow = df["planned_inflow"].sum()
    total_actual_inflow = df["actual_inflow"].sum()
    total_planned_outflow = df["planned_outflow"].sum()
    total_actual_outflow = df["actual_outflow"].sum()
    final_planned_cum = df["cumulative_planned"].iloc[-1] if not df.empty else 0
    final_actual_cum = df["cumulative_actual"].iloc[-1] if not df.empty else 0
    
    # Planlanan vs gerceklesen karsilastirma
    inflow_variance = ((total_actual_inflow - total_planned_inflow) / total_planned_inflow * 100) if total_planned_inflow > 0 else 0
    outflow_variance = ((total_actual_outflow - total_planned_outflow) / total_planned_outflow * 100) if total_planned_outflow > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="animate-card" style="
            background-color: #141414;
            padding: 0.8rem;
            border-radius: 12px;
            border: 1px solid #262626;
            text-align: center;
        ">
            <p style="color: #737373; font-size: 0.6rem; margin: 0;">Toplam Giris</p>
            <p style="color: #34d399; margin: 0.1rem 0; font-size: 0.7rem;">Plan: {total_planned_inflow:,.0f} TL</p>
            <p style="color: #22c55e; margin: 0; font-size: 0.7rem;">Gercek: {total_actual_inflow:,.0f} TL</p>
            <p style="color: {'#22c55e' if inflow_variance > 0 else '#ef4444'}; margin: 0; font-size: 0.6rem;">%{inflow_variance:.1f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="animate-card" style="
            background-color: #141414;
            padding: 0.8rem;
            border-radius: 12px;
            border: 1px solid #262626;
            text-align: center;
        ">
            <p style="color: #737373; font-size: 0.6rem; margin: 0;">Toplam Cikis</p>
            <p style="color: #f87171; margin: 0.1rem 0; font-size: 0.7rem;">Plan: {total_planned_outflow:,.0f} TL</p>
            <p style="color: #ef4444; margin: 0; font-size: 0.7rem;">Gercek: {total_actual_outflow:,.0f} TL</p>
            <p style="color: {'#22c55e' if outflow_variance < 0 else '#ef4444'}; margin: 0; font-size: 0.6rem;">%{outflow_variance:.1f}</p>
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
            <p style="color: #737373; font-size: 0.6rem; margin: 0;">Kumulatif Nakit</p>
            <p style="color: #3b82f6; margin: 0.1rem 0; font-size: 0.7rem;">Plan: {final_planned_cum:,.0f} TL</p>
            <p style="color: #60a5fa; margin: 0; font-size: 0.7rem;">Gercek: {final_actual_cum:,.0f} TL</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        # En iyi ve en kötü ay
        best_month = df.loc[df["actual_net"].idxmax()] if "actual_net" in df.columns else None
        worst_month = df.loc[df["actual_net"].idxmin()] if "actual_net" in df.columns else None
        
        st.markdown(f"""
        <div class="animate-card" style="
            background-color: #141414;
            padding: 0.8rem;
            border-radius: 12px;
            border: 1px solid #262626;
            text-align: center;
        ">
            <p style="color: #737373; font-size: 0.6rem; margin: 0;">En Iyi / En Kotu Ay</p>
            <p style="color: #34d399; margin: 0.1rem 0; font-size: 0.7rem;">
                {best_month['period_date'] if best_month is not None else '-'}: {best_month['actual_net']:,.0f} TL
            </p>
            <p style="color: #ef4444; margin: 0; font-size: 0.7rem;">
                {worst_month['period_date'] if worst_month is not None else '-'}: {worst_month['actual_net']:,.0f} TL
            </p>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# 7. GRAFIKLER - PLANLANAN vs GERCEKLESEN
# ==========================================
if not edited_cashflow_df.empty:
    st.markdown("---")
    st.markdown("### Planlanan vs Gerceklesen Nakit Akisi")
    
    df_plot = edited_cashflow_df.copy()
    df_plot["period_date"] = pd.to_datetime(df_plot["period_date"])
    
    # ===== 7a. Gelir-Gider Grafigi (Planlanan vs Gerceklesen) =====
    fig1 = go.Figure()
    
    # Planlanan Gelir
    fig1.add_trace(go.Scatter(
        x=df_plot["period_date"],
        y=df_plot["planned_inflow"],
        name="Planlanan Gelir",
        line=dict(color="#2563eb", width=2, dash="solid"),
        mode="lines+markers"
    ))
    
    # Gerceklesen Gelir
    fig1.add_trace(go.Scatter(
        x=df_plot["period_date"],
        y=df_plot["actual_inflow"],
        name="Gerceklesen Gelir",
        line=dict(color="#34d399", width=2, dash="solid"),
        mode="lines+markers"
    ))
    
    # Planlanan Gider
    fig1.add_trace(go.Scatter(
        x=df_plot["period_date"],
        y=df_plot["planned_outflow"],
        name="Planlanan Gider",
        line=dict(color="#f87171", width=2, dash="dot"),
        mode="lines+markers"
    ))
    
    # Gerceklesen Gider
    fig1.add_trace(go.Scatter(
        x=df_plot["period_date"],
        y=df_plot["actual_outflow"],
        name="Gerceklesen Gider",
        line=dict(color="#ef4444", width=2, dash="dot"),
        mode="lines+markers"
    ))
    
    fig1.update_layout(
        title="Gelir ve Gider Karsilastirmasi",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=400,
        legend=dict(
            font=dict(color="white"),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis=dict(
            title="Donem",
            tickfont=dict(color="white"),
            gridcolor="#262626"
        ),
        yaxis=dict(
            title="Tutar (TL)",
            tickfont=dict(color="white"),
            gridcolor="#262626"
        )
    )
    
    fig1 = animate_plotly(fig1)
    st.plotly_chart(fig1, use_container_width=True)
    
    # ===== 7b. Net Nakit Karsilastirma =====
    fig2 = go.Figure()
    
    # Planlanan Net Nakit
    fig2.add_trace(go.Bar(
        x=df_plot["period_date"],
        y=df_plot["planned_net"],
        name="Planlanan Net",
        marker_color="#3b82f6",
        opacity=0.7
    ))
    
    # Gerceklesen Net Nakit
    fig2.add_trace(go.Bar(
        x=df_plot["period_date"],
        y=df_plot["actual_net"],
        name="Gerceklesen Net",
        marker_color="#34d399",
        opacity=0.7
    ))
    
    fig2.update_layout(
        title="Net Nakit Karsilastirmasi (Planlanan vs Gerceklesen)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=350,
        barmode="group",
        legend=dict(
            font=dict(color="white"),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis=dict(
            title="Donem",
            tickfont=dict(color="white"),
            gridcolor="#262626"
        ),
        yaxis=dict(
            title="Net Nakit (TL)",
            tickfont=dict(color="white"),
            gridcolor="#262626"
        )
    )
    
    fig2 = animate_plotly(fig2)
    st.plotly_chart(fig2, use_container_width=True)
    
    # ===== 7c. Kumulatif Nakit Karsilastirma =====
    fig3 = go.Figure()
    
    # Planlanan Kumulatif
    fig3.add_trace(go.Scatter(
        x=df_plot["period_date"],
        y=df_plot["cumulative_planned"],
        name="Planlanan Kumulatif",
        line=dict(color="#3b82f6", width=3),
        fill="tozeroy",
        fillcolor="rgba(59, 130, 246, 0.2)"
    ))
    
    # Gerceklesen Kumulatif
    fig3.add_trace(go.Scatter(
        x=df_plot["period_date"],
        y=df_plot["cumulative_actual"],
        name="Gerceklesen Kumulatif",
        line=dict(color="#34d399", width=3),
        fill="tozeroy",
        fillcolor="rgba(52, 211, 153, 0.2)"
    ))
    
    fig3.update_layout(
        title="Kumulatif Nakit Akisi (Planlanan vs Gerceklesen)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=350,
        legend=dict(
            font=dict(color="white"),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis=dict(
            title="Donem",
            tickfont=dict(color="white"),
            gridcolor="#262626"
        ),
        yaxis=dict(
            title="Kumulatif Nakit (TL)",
            tickfont=dict(color="white"),
            gridcolor="#262626"
        )
    )
    
    fig3 = animate_plotly(fig3)
    st.plotly_chart(fig3, use_container_width=True)
    
    # ===== 7d. Sapma Analizi =====
    df_plot["variance"] = df_plot["actual_net"] - df_plot["planned_net"]
    
    fig4 = go.Figure()
    
    # Pozitif sapma (yeşil), negatif sapma (kırmızı)
    colors = ["#34d399" if x >= 0 else "#ef4444" for x in df_plot["variance"]]
    
    fig4.add_trace(go.Bar(
        x=df_plot["period_date"],
        y=df_plot["variance"],
        name="Sapma",
        marker_color=colors,
        text=[f"{x:+,.0f} TL" for x in df_plot["variance"]],
        textposition="outside",
        textfont=dict(color="white", size=10)
    ))
    
    fig4.update_layout(
        title="Net Nakit Sapma Analizi (Gerceklesen - Planlanan)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=300,
        legend=dict(
            font=dict(color="white"),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis=dict(
            title="Donem",
            tickfont=dict(color="white"),
            gridcolor="#262626"
        ),
        yaxis=dict(
            title="Sapma (TL)",
            tickfont=dict(color="white"),
            gridcolor="#262626"
        )
    )
    
    fig4 = animate_plotly(fig4)
    st.plotly_chart(fig4, use_container_width=True)

# ==========================================
# 8. KAYDET
# ==========================================
st.markdown("---")

col_save, col_auto = st.columns(2)

with col_save:
    if st.button("Nakit Akisini Kaydet", type="primary", use_container_width=True):
        rows_to_save = edited_cashflow_df.to_dict(orient="records") if not edited_cashflow_df.empty else []
        clean_rows = [r for r in rows_to_save if str(r.get("period_date", "")).strip()]
        
        if clean_rows:
            try:
                with loading_spinner("Veriler kaydediliyor..."):
                    # Eski verileri sil
                    supabase.table("project_cashflow").delete().eq("project_id", project_id).execute()
                    
                    # Yeni verileri ekle
                    for r in clean_rows:
                        r["project_id"] = project_id
                        r.pop("id", None)
                        
                        # Tarihi string'e cevir
                        if hasattr(r["period_date"], "isoformat"):
                            r["period_date"] = r["period_date"].isoformat()
                        
                        supabase.table("project_cashflow").insert(r).execute()
                    
                    time.sleep(0.3)
                toast_success("Basarili", f"{len(clean_rows)} donem kaydedildi!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                toast_error("Hata", f"Kayit hatasi: {e}")
        else:
            toast_warning("Uyari", "Kaydedilecek veri yok.")

with col_auto:
    if st.button("Is Programindan Otomatik Olustur", use_container_width=True):
        toast_info("Bilgi", "Is programi verilerine gore nakit akisi olusturuluyor...")
        # Sayfayı yenile
        st.rerun()

# ==========================================
# 9. DASHBOARD ENTEGRASYONU ICIN VERI CIKTI
# ==========================================
# Bu veriler dashboard tarafından çekilecek
if not edited_cashflow_df.empty:
    # Dashboard için özet verileri session state'e kaydet
    st.session_state.dashboard_cashflow = {
        'total_planned_inflow': edited_cashflow_df['planned_inflow'].sum(),
        'total_actual_inflow': edited_cashflow_df['actual_inflow'].sum(),
        'total_planned_outflow': edited_cashflow_df['planned_outflow'].sum(),
        'total_actual_outflow': edited_cashflow_df['actual_outflow'].sum(),
        'cumulative_planned': edited_cashflow_df['cumulative_planned'].iloc[-1] if not edited_cashflow_df.empty else 0,
        'cumulative_actual': edited_cashflow_df['cumulative_actual'].iloc[-1] if not edited_cashflow_df.empty else 0,
        'periods': edited_cashflow_df['period_date'].tolist(),
        'planned_net': edited_cashflow_df['planned_net'].tolist(),
        'actual_net': edited_cashflow_df['actual_net'].tolist(),
        'planned_inflow': edited_cashflow_df['planned_inflow'].tolist(),
        'actual_inflow': edited_cashflow_df['actual_inflow'].tolist(),
        'planned_outflow': edited_cashflow_df['planned_outflow'].tolist(),
        'actual_outflow': edited_cashflow_df['actual_outflow'].tolist()
    }

st.markdown('</div>', unsafe_allow_html=True)