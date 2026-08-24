# -*- coding: utf-8 -*-
"""
Created on Thu Aug 20 02:16:00 2026
@author: taric
Updated: 2026-08-22 - Animasyonlar eklendi, ikonlar kaldırıldı
"""

import streamlit as st
import datetime
import pandas as pd
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
    page_title="SARCON Portal | Gelismis Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

apply_global_styles(is_login=False)
render_top_navbar()

st.markdown('<div class="page-content">', unsafe_allow_html=True)

st.markdown("""
<div style="border-left: 3px solid #3b82f6; padding-left: 0.8rem; margin-bottom: 1.5rem;">
    <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.3rem;">Gelismis Dashboard</h3>
    <p style="color: #737373; margin: 0; font-size: 0.8rem;">Proje verileri arasindaki korelasyonlari ve trendleri analiz edin</p>
</div>
""", unsafe_allow_html=True)

# Proje secimi
with loading_spinner("Projeler yukleniyor..."):
    projects, err = get_user_projects()
    time.sleep(0.3)

project_names = [p["project_name"] for p in projects] if projects else []

if not project_names:
    toast_warning("Uyari", "Henuz bir proje olusturmadiniz.")
    st.stop()

selected_project = st.selectbox("Proje Secin", project_names)
project_id = next(p["id"] for p in projects if p["project_name"] == selected_project)

# Verileri cek
@st.cache_data(ttl=300)
def get_all_project_data(project_id):
    try:
        reports = supabase.table("daily_reports").select("*").eq("project_id", project_id).execute()
        resources = supabase.table("daily_resources").select("*").eq("project_id", project_id).execute()
        work = supabase.table("daily_work_progress").select("*").eq("project_id", project_id).execute()
        items = supabase.table("project_items").select("*").eq("project_id", project_id).execute()
        costs = supabase.table("project_costs").select("*").eq("project_id", project_id).execute()
        
        return {
            'reports': reports.data if reports.data else [],
            'resources': resources.data if resources.data else [],
            'work': work.data if work.data else [],
            'items': items.data if items.data else [],
            'costs': costs.data if costs.data else []
        }
    except Exception as e:
        toast_error("Hata", f"Veriler alinamadi: {e}")
        return None

with loading_spinner("Veriler yukleniyor..."):
    data = get_all_project_data(project_id)
    time.sleep(0.3)

if not data:
    st.stop()

df_reports = pd.DataFrame(data['reports']) if data['reports'] else pd.DataFrame()
df_resources = pd.DataFrame(data['resources']) if data['resources'] else pd.DataFrame()
df_work = pd.DataFrame(data['work']) if data['work'] else pd.DataFrame()
df_items = pd.DataFrame(data['items']) if data['items'] else pd.DataFrame()
df_costs = pd.DataFrame(data['costs']) if data['costs'] else pd.DataFrame()

if df_reports.empty and df_resources.empty and df_work.empty:
    toast_info("Bilgi", "Henuz bu projeye ait veri bulunmuyor.")
    st.stop()

# Tarih filtreleri
col_f1, col_f2 = st.columns(2)
with col_f1:
    date_range = st.selectbox(
        "Zaman Araligi",
        ["Son 7 Gun", "Son 30 Gun", "Son 90 Gun", "Tumu"],
        index=1
    )
with col_f2:
    view_type = st.selectbox(
        "Gorunum",
        ["Kumulatif", "Aylik", "Haftalik"]
    )

if date_range != "Tumu" and not df_reports.empty:
    days = int(date_range.split()[1])
    cutoff = pd.Timestamp(datetime.date.today() - datetime.timedelta(days=days))
    df_reports['report_date'] = pd.to_datetime(df_reports['report_date'])
    df_reports = df_reports[df_reports['report_date'] >= cutoff]

st.markdown("---")

# 1. ISCILIK VS MALIYET KORELASYONU
if not df_reports.empty:
    st.markdown("### Iscilik vs Maliyet Korelasyonu")
    
    daily_summary = df_reports.groupby('report_date').agg({
        'actual_manpower': 'sum',
        'cost': 'sum'
    }).reset_index()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily_summary['report_date'],
        y=daily_summary['actual_manpower'],
        name='Is cilik (saat)',
        yaxis='y1',
        line=dict(color='#2563eb')
    ))
    fig.add_trace(go.Scatter(
        x=daily_summary['report_date'],
        y=daily_summary['cost'],
        name='Maliyet (TL)',
        yaxis='y2',
        line=dict(color='#34d399')
    ))
    
    fig.update_layout(
        title='Is cilik ve Maliyet Trendi',
        yaxis=dict(title='Is cilik (saat)', color='#2563eb'),
        yaxis2=dict(title='Maliyet (TL)', overlaying='y', side='right', color='#34d399'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        hovermode='x unified'
    )
    
    fig = animate_plotly(fig)
    st.plotly_chart(fig, use_container_width=True)

# 2. KAYNAK DAGILIMI
if not df_resources.empty:
    st.markdown("### Kaynak Dagilimi")
    
    col1, col2 = st.columns(2)
    
    with col1:
        category_summary = df_resources.groupby('category')['value'].sum().reset_index()
        if not category_summary.empty:
            fig = px.pie(
                category_summary,
                names='category',
                values='value',
                title='Kategori Bazinda Kaynak Dagilimi',
                hole=0.4,
                color_discrete_sequence=['#2563eb', '#38bdf8', '#34d399', '#facc15', '#f87171']
            )
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            fig = animate_plotly(fig)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        endirect = df_resources[df_resources['category'] == 'Endirekt Personel']['value'].sum()
        direct = df_resources[df_resources['category'] == 'Direkt Personel']['value'].sum()
        
        if endirect > 0 or direct > 0:
            fig = go.Figure(data=[
                go.Bar(name='Endirekt', x=['Personel'], y=[endirect], marker_color='#2563eb'),
                go.Bar(name='Direkt', x=['Personel'], y=[direct], marker_color='#34d399')
            ])
            fig.update_layout(
                title='Endirekt vs Direkt Personel',
                barmode='group',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                showlegend=True
            )
            fig = animate_plotly(fig)
            st.plotly_chart(fig, use_container_width=True)

# 3. IS ILERLEME ANALIZI
if not df_work.empty:
    st.markdown("### Is Ilerleme Analizi")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if 'is_turu' in df_work.columns:
            trade_summary = df_work.groupby('is_turu')['ilerleme_yuzdesi'].mean().reset_index()
            fig = px.bar(
                trade_summary,
                x='is_turu',
                y='ilerleme_yuzdesi',
                title='Is Turu Bazinda Ortalama Ilerleme',
                color='is_turu',
                color_discrete_sequence=['#2563eb', '#38bdf8', '#34d399', '#facc15', '#f87171']
            )
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
            fig = animate_plotly(fig)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if 'ilerleme_yuzdesi' in df_work.columns:
            fig = px.histogram(
                df_work,
                x='ilerleme_yuzdesi',
                nbins=10,
                title='Ilerleme Yuzdesi Dagilimi',
                color_discrete_sequence=['#2563eb']
            )
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            fig = animate_plotly(fig)
            st.plotly_chart(fig, use_container_width=True)

# 4. BUTCE VS GERCEKLESEN
if not df_costs.empty and not df_items.empty:
    st.markdown("### Butce vs Gerceklesen")
    
    total_quantity = df_items['quantity'].sum() if not df_items.empty else 0
    total_unit_price = df_items['unit_price'].sum() if not df_items.empty else 0
    budget_total = total_quantity * total_unit_price
    
    actual_total = df_costs['total_price'].sum() if not df_costs.empty else 0
    
    variance = budget_total - actual_total
    variance_pct = (variance / budget_total * 100) if budget_total > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="animate-card" style="
            background-color: #141414;
            padding: 1rem;
            border-radius: 12px;
            border: 1px solid #262626;
            text-align: center;
        ">
            <p style="color: #737373; font-size: 0.7rem; margin: 0;">Kesif (Butce)</p>
            <h3 style="color: #3b82f6; margin: 0.2rem 0;">{budget_total:,.0f} TL</h3>
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
            <p style="color: #737373; font-size: 0.7rem; margin: 0;">Gerceklesen</p>
            <h3 style="color: #22c55e; margin: 0.2rem 0;">{actual_total:,.0f} TL</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        variance_color = "#f87171" if variance < 0 else "#fbbf24"
        st.markdown(f"""
        <div class="animate-card" style="
            background-color: #141414;
            padding: 1rem;
            border-radius: 12px;
            border: 1px solid #262626;
            text-align: center;
        ">
            <p style="color: #737373; font-size: 0.7rem; margin: 0;">Sapma</p>
            <h3 style="color: {variance_color}; margin: 0.2rem 0;">{variance:,.0f} TL</h3>
            <p style="color: #737373; font-size: 0.7rem; margin: 0;">{variance_pct:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    fig = go.Figure(data=[
        go.Bar(name='Butce', x=['Toplam'], y=[budget_total], marker_color='#2563eb'),
        go.Bar(name='Gerceklesen', x=['Toplam'], y=[actual_total], marker_color='#34d399')
    ])
    fig.update_layout(
        title='Butce vs Gerceklesen',
        barmode='group',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=True
    )
    fig = animate_plotly(fig)
    st.plotly_chart(fig, use_container_width=True)

# 5. ILERLEME vs MALIYET KORELASYONU
if not df_work.empty and not df_reports.empty:
    st.markdown("### Ilerleme vs Maliyet Korelasyonu")
    
    df_work['week'] = pd.to_datetime(df_work['report_date']).dt.isocalendar().week
    weekly_progress = df_work.groupby('week')['ilerleme_yuzdesi'].mean().reset_index()
    
    df_reports['week'] = pd.to_datetime(df_reports['report_date']).dt.isocalendar().week
    weekly_cost = df_reports.groupby('week')['cost'].sum().reset_index()
    
    if not weekly_progress.empty and not weekly_cost.empty:
        merged = pd.merge(weekly_progress, weekly_cost, on='week', how='inner')
        
        fig = px.scatter(
            merged,
            x='ilerleme_yuzdesi',
            y='cost',
            title='Ilerleme vs Maliyet Korelasyonu',
            labels={'ilerleme_yuzdesi': 'Ilerleme (%)', 'cost': 'Maliyet (TL)'},
            trendline='ols',
            color_discrete_sequence=['#2563eb']
        )
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        fig = animate_plotly(fig)
        st.plotly_chart(fig, use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)