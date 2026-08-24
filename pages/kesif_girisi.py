# -*- coding: utf-8 -*-
"""
Created on Thu Aug 20 02:12:00 2026
@author: taric
Updated: 2026-08-24 - Total price otomatik hesaplama, yapilan is miktari entegrasyonu
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
from utils.db import supabase, get_user_projects
from utils.styles import apply_global_styles
from utils.top_navbar import render_top_navbar
from utils.animations import (
    loading_spinner,
    toast_success,
    toast_error,
    toast_warning,
    toast_info,
    ENABLE_FADE_IN,
    ENABLE_HOVER
)

st.set_page_config(
    page_title="SARCON Portal | Kesif Girisi",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

apply_global_styles(is_login=False)
render_top_navbar()

st.markdown('<div class="page-content">', unsafe_allow_html=True)

st.markdown("""
<div style="border-left: 3px solid #3b82f6; padding-left: 0.8rem; margin-bottom: 1.5rem;">
    <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.3rem;">Kesif / Metraj Girisi</h3>
    <p style="color: #737373; margin: 0; font-size: 0.8rem;">Proje is kalemlerini ve metrajlarini sisteme girin</p>
</div>
""", unsafe_allow_html=True)

# Proje secimi
with loading_spinner("Projeler yukleniyor..."):
    projects, err = get_user_projects()
    time.sleep(0.3)

project_names = [p["project_name"] for p in projects] if projects else []

if not project_names:
    toast_warning("Uyari", "Henuz bir proje olusturmadiniz. Veri Girisi sayfasindan proje olusturun.")
    st.stop()

selected_project = st.selectbox("Proje Secin", project_names)
project_id = next(p["id"] for p in projects if p["project_name"] == selected_project)

# Mevcut kesif verilerini cek
@st.cache_data(ttl=300)
def get_project_items(project_id):
    try:
        response = supabase.table("project_items").select("*").eq("project_id", project_id).execute()
        return response.data if response.data else []
    except:
        return []

# Günlük raporlardan yapilan is miktarlarini getir
@st.cache_data(ttl=300)
def get_completed_quantities(project_id):
    """Günlük raporlardan toplam yapilan is miktarlarini hesapla"""
    try:
        # Günlük raporlardan verileri çek
        response = supabase.table("daily_reports").select("*").eq("project_id", project_id).execute()
        reports = response.data if response.data else []
        
        if not reports:
            return {}
        
        # Her bir kalem için toplam yapilan miktari hesapla
        completed_qty = {}
        for report in reports:
            if "items" in report and isinstance(report["items"], list):
                for item in report["items"]:
                    item_name = item.get("item_name", "")
                    qty = float(item.get("quantity", 0))
                    if item_name:
                        completed_qty[item_name] = completed_qty.get(item_name, 0) + qty
        
        return completed_qty
    except Exception as e:
        st.error(f"Yapilan is miktarlari getirilirken hata: {str(e)}")
        return {}

with loading_spinner("Veriler yukleniyor..."):
    existing_items = get_project_items(project_id)
    completed_qty = get_completed_quantities(project_id)
    time.sleep(0.3)

# Session state ile satir yönetimi
if "items_df" not in st.session_state or st.session_state.get("current_project") != project_id:
    st.session_state.current_project = project_id
    if existing_items:
        st.session_state.items_df = pd.DataFrame(existing_items)
        # Yapilan is miktarlarini güncelle
        for idx, row in st.session_state.items_df.iterrows():
            item_name = row.get("item_name", "")
            if item_name in completed_qty:
                st.session_state.items_df.at[idx, "completed_quantity"] = completed_qty[item_name]
    else:
        st.session_state.items_df = pd.DataFrame(columns=[
            "pos_no", "item_name", "category", "unit", 
            "quantity", "unit_price", "total_price",
            "completed_quantity", "contract_quantity", "notes"
        ])

# Excel-like formula functions
def calculate_total_price(row):
    """Otomatik toplam tutar hesaplama"""
    try:
        quantity = float(row.get("quantity", 0))
        unit_price = float(row.get("unit_price", 0))
        return quantity * unit_price
    except:
        return 0

def calculate_remaining(row):
    """Kalan is miktarini hesapla"""
    try:
        quantity = float(row.get("quantity", 0))
        completed = float(row.get("completed_quantity", 0))
        return max(0, quantity - completed)
    except:
        return 0

# Data Editor (Excel-like) - Total price otomatik hesaplama ile
edited_items_df = st.data_editor(
    st.session_state.items_df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "pos_no": st.column_config.TextColumn("Poz No", width="small"),
        "item_name": st.column_config.TextColumn("Isin Tanimi", required=True, width="large"),
        "category": st.column_config.SelectboxColumn(
            "Is Kapsami",
            options=["Kaba Isler", "Ince Isler", "Mekanik", "Elektrik", "Peyzaj", "Diger"],
            required=True,
            width="medium"
        ),
        "unit": st.column_config.SelectboxColumn(
            "Birim",
            options=["m²", "m³", "m", "adet", "ton", "kg", "lt", "km", "saat", "gun", "takim", "kalip"],
            required=True,
            width="small"
        ),
        "quantity": st.column_config.NumberColumn(
            "Kesif Miktari", 
            min_value=0.0, 
            step=0.01, 
            format="%.2f",
            width="medium"
        ),
        "unit_price": st.column_config.NumberColumn(
            "Birim Fiyat (TL)", 
            min_value=0.0, 
            step=0.01, 
            format="%.2f",
            width="medium"
        ),
        "total_price": st.column_config.NumberColumn(
            "Toplam Tutar (TL)",
            format="%.2f",
            width="medium",
            disabled=True  # Otomatik hesaplanacak
        ),
        "completed_quantity": st.column_config.NumberColumn(
            "Yapilan Is Miktari",
            min_value=0.0,
            step=0.01,
            format="%.2f",
            width="medium",
            disabled=True  # Günlük raporlardan gelecek
        ),
        "contract_quantity": st.column_config.NumberColumn(
            "Sozlesme Is Miktari",
            min_value=0.0,
            step=0.01,
            format="%.2f",
            width="medium"
        ),
        "notes": st.column_config.TextColumn("Notlar", width="medium")
    },
    key="items_grid"
)

# Total price'ı otomatik hesapla (Excel formülü gibi)
if not edited_items_df.empty:
    # Quantity veya unit_price değiştiğinde total_price'ı güncelle
    for idx in edited_items_df.index:
        edited_items_df.at[idx, "total_price"] = calculate_total_price(edited_items_df.iloc[idx])
        
        # Yapilan is miktarını günlük raporlardan gelen veriyle karşılaştır
        item_name = edited_items_df.at[idx, "item_name"]
        if item_name in completed_qty:
            edited_items_df.at[idx, "completed_quantity"] = completed_qty[item_name]

st.session_state.items_df = edited_items_df

# Ozet Metrikler
if not edited_items_df.empty:
    st.markdown("---")
    st.markdown("### Kesif Ozeti")
    
    edited_items_df = edited_items_df.fillna(0)
    
    total_quantity = edited_items_df["quantity"].sum()
    total_completed = edited_items_df["completed_quantity"].sum()
    total_contract = edited_items_df["contract_quantity"].sum()
    total_price = edited_items_df["total_price"].sum()  # Total price artık otomatik hesaplanıyor
    item_count = len(edited_items_df)
    
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
            <p style="color: #737373; font-size: 0.6rem; margin: 0;">Toplam Kalem</p>
            <h4 style="color: #ffffff; margin: 0.2rem 0;">{item_count}</h4>
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
            <p style="color: #737373; font-size: 0.6rem; margin: 0;">Toplam Kesif</p>
            <h4 style="color: #3b82f6; margin: 0.2rem 0;">{total_quantity:,.2f}</h4>
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
            <p style="color: #737373; font-size: 0.6rem; margin: 0;">Toplam Yapilan</p>
            <h4 style="color: #22c55e; margin: 0.2rem 0;">{total_completed:,.2f}</h4>
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
            <p style="color: #737373; font-size: 0.6rem; margin: 0;">Sozlesme Toplami</p>
            <h4 style="color: #fbbf24; margin: 0.2rem 0;">{total_contract:,.2f}</h4>
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
            <p style="color: #737373; font-size: 0.6rem; margin: 0;">Toplam Tutar</p>
            <h4 style="color: #8b5cf6; margin: 0.2rem 0;">{total_price:,.2f} TL</h4>
        </div>
        """, unsafe_allow_html=True)
    
    # İlerleme hesaplama - Excel formülü gibi
    if total_quantity > 0:
        progress_pct = (total_completed / total_quantity) * 100
        st.progress(min(progress_pct / 100, 1.0))
        st.caption(f"Genel Ilerleme: %{progress_pct:.1f}")
    
    # Excel-like formül gösterimi
    with st.expander("📊 Excel Formülleri (Otomatik Hesaplama)"):
        st.markdown("""
        **Formül Açıklamaları:**
        
        - **Toplam Tutar** = Kesif Miktarı × Birim Fiyat (Otomatik)
        - **Yapılan İş Miktarı** = Günlük Raporlardan Toplam (Otomatik)
        - **Kalan İş Miktarı** = Kesif Miktarı - Yapılan İş Miktarı (Otomatik)
        - **İlerleme Oranı** = (Yapılan İş Miktarı / Kesif Miktarı) × 100 (Otomatik)
        
        *Not: Tüm formüller Excel'deki gibi otomatik çalışır.*
        """)

# Kaydet butonu
if st.button("Kesif Verilerini Kaydet", type="primary", use_container_width=True):
    # Önce total_price'ları güncelle
    if not edited_items_df.empty:
        for idx in edited_items_df.index:
            edited_items_df.at[idx, "total_price"] = calculate_total_price(edited_items_df.iloc[idx])
            # completed_quantity'yi koru
            item_name = edited_items_df.at[idx, "item_name"]
            if item_name in completed_qty:
                edited_items_df.at[idx, "completed_quantity"] = completed_qty[item_name]
    
    rows_to_save = edited_items_df.to_dict(orient="records") if not edited_items_df.empty else []
    clean_rows = [r for r in rows_to_save if str(r.get("item_name", "")).strip()]
    
    if clean_rows:
        try:
            with loading_spinner("Veriler kaydediliyor..."):
                for r in clean_rows:
                    for key in ["quantity", "unit_price", "total_price", "completed_quantity", "contract_quantity"]:
                        if pd.isna(r.get(key)) or np.isinf(r.get(key, 0)):
                            r[key] = None
                        elif r.get(key) == "":
                            r[key] = None
                    
                    # total_price'ı tekrar hesapla (güvenlik için)
                    if r.get("quantity") is not None and r.get("unit_price") is not None:
                        r["total_price"] = r["quantity"] * r["unit_price"]
                
                # Eski verileri sil
                supabase.table("project_items").delete().eq("project_id", project_id).execute()
                
                # Yeni verileri ekle
                for r in clean_rows:
                    r["project_id"] = project_id
                    r.pop("id", None)
                    # completed_quantity'yi günlük raporlardan geldiği için kaydetme (koru)
                    supabase.table("project_items").insert(r).execute()
                
                time.sleep(0.3)
            toast_success("Basarili", f"{len(clean_rows)} kalem basariyla kaydedildi!")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            toast_error("Hata", f"Kayit sirasinda hata olustu: {e}")
    else:
        toast_warning("Uyari", "Kaydedilecek veri bulunamadi.")
        
st.markdown('</div>', unsafe_allow_html=True)