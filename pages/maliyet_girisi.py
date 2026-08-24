# -*- coding: utf-8 -*-
"""
Created on Thu Aug 20 02:09:27 2026
@author: taric
Updated: 2026-08-24 - Manuel Gider Girisi, Stok/Malzeme Entegrasyonu, Excel Import/Export gelistirildi
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
import io
from datetime import datetime
from utils.db import supabase, get_user_projects
from utils.styles import apply_global_styles
from utils.top_navbar import render_top_navbar
from utils.animations import (
    loading_spinner,
    toast_success,
    toast_error,
    toast_warning,
    toast_info
)

st.set_page_config(
    page_title="SARCON Portal | Maliyet Girisi",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

apply_global_styles(is_login=False)
render_top_navbar()

st.markdown('<div class="page-content">', unsafe_allow_html=True)

st.markdown("""
<div style="border-left: 3px solid #3b82f6; padding-left: 0.8rem; margin-bottom: 1.5rem;">
    <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.3rem;">Maliyet Girisi</h3>
    <p style="color: #737373; margin: 0; font-size: 0.8rem;">
        WBS kod secin, maliyet kalemlerini girin, manuel gider ekleyin, stok takibi yapin
    </p>
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
    toast_warning("Uyari", "Henuz bir proje olusturmadiniz. Veri Girisi sayfasindan proje olusturun.")
    st.stop()

selected_project = st.selectbox("Proje Secin", project_names)
project_id = next(p["id"] for p in projects if p["project_name"] == selected_project)

# ==========================================
# 2. VERI CEKME FONKSIYONLARI
# ==========================================
@st.cache_data(ttl=300)
def get_project_items(project_id):
    try:
        response = supabase.table("project_items").select("*").eq("project_id", project_id).execute()
        return response.data if response.data else []
    except:
        return []

@st.cache_data(ttl=300)
def get_project_resources(project_id):
    try:
        response = supabase.table("project_resources").select("*").eq("project_id", project_id).execute()
        return response.data if response.data else []
    except:
        return []

@st.cache_data(ttl=300)
def get_project_work_types(project_id):
    try:
        response = supabase.table("project_work_types").select("*").eq("project_id", project_id).execute()
        return response.data if response.data else []
    except:
        return []

@st.cache_data(ttl=300)
def get_project_stock(project_id):
    try:
        response = supabase.table("project_stock").select("*").eq("project_id", project_id).execute()
        return response.data if response.data else []
    except:
        return []

@st.cache_data(ttl=300)
def get_project_costs(project_id):
    try:
        response = supabase.table("project_costs").select("*").eq("project_id", project_id).execute()
        return response.data if response.data else []
    except:
        return []

with loading_spinner("Veriler yukleniyor..."):
    items_data = get_project_items(project_id)
    resources_data = get_project_resources(project_id)
    work_types_data = get_project_work_types(project_id)
    stock_data = get_project_stock(project_id)
    existing_costs = get_project_costs(project_id)
    time.sleep(0.3)

items_df = pd.DataFrame(items_data) if items_data else pd.DataFrame()
resources_df = pd.DataFrame(resources_data) if resources_data else pd.DataFrame()
work_types_df = pd.DataFrame(work_types_data) if work_types_data else pd.DataFrame()
stock_df = pd.DataFrame(stock_data) if stock_data else pd.DataFrame()

# ==========================================
# 3. WBS KODLARINI DUZENLE
# ==========================================
wbs_list = []
wbs_map = {}

if not items_df.empty:
    wbs_col = None
    for col in ["wbs_kodu", "wbs_code", "wbs"]:
        if col in items_df.columns:
            wbs_col = col
            break
    
    if wbs_col:
        items_with_wbs = items_df[items_df[wbs_col].notna() & (items_df[wbs_col] != '')]
        for _, row in items_with_wbs.iterrows():
            wbs_code = row.get(wbs_col, '')
            if wbs_code:
                wbs_list.append(wbs_code)
                wbs_map[wbs_code] = {
                    'item_name': row.get('item_name', ''),
                    'unit': row.get('unit', ''),
                    'quantity': row.get('quantity', 0),
                    'pos_no': row.get('pos_no', '')
                }

if not wbs_list:
    for _, row in items_df.iterrows():
        item_name = row.get('item_name', '')
        if item_name:
            wbs_list.append(item_name)
            wbs_map[item_name] = {
                'item_name': item_name,
                'unit': row.get('unit', ''),
                'quantity': row.get('quantity', 0),
                'pos_no': row.get('pos_no', '')
            }

wbs_list = sorted(list(set(wbs_list)))

# ==========================================
# 4. SESSION STATE - ANA MALIYET TABLOSU
# ==========================================
COLS = [
    "wbs_code", "cost_name", "unit_price", "nakliye", "iscilik",
    "other_costs", "total_unit_cost", "quantity", "total_cost",
    "cost_category", "is_prolongation", "prolongation_cost",
    "source_type", "notes"
]

if "costs_df" not in st.session_state or st.session_state.get("current_project") != project_id:
    st.session_state.current_project = project_id
    if existing_costs:
        df = pd.DataFrame(existing_costs)
        for col in COLS:
            if col not in df.columns:
                df[col] = None
        if "total_price" in df.columns:
            df["total_cost"] = df["total_price"]
        st.session_state.costs_df = df[COLS]
    else:
        st.session_state.costs_df = pd.DataFrame(columns=COLS)

# ==========================================
# 5. SESSION STATE - MANUEL GIDERLER
# ==========================================
MANUAL_COLS = [
    "gider_adi", "miktar", "birim_fiyat", "toplam", "kategori", "tarih", "aciklama"
]

if "manual_giderler" not in st.session_state or st.session_state.get("manual_project") != project_id:
    st.session_state.manual_project = project_id
    st.session_state.manual_giderler = []

# ==========================================
# 6. SESSION STATE - STOK
# ==========================================
STOCK_COLS = [
    "stock_name", "quantity", "unit_price", "total_value", "category",
    "supplier", "purchase_date", "location", "notes"
]

if "stock_df" not in st.session_state or st.session_state.get("stock_project") != project_id:
    st.session_state.stock_project = project_id
    if not stock_df.empty:
        st.session_state.stock_df = stock_df[STOCK_COLS] if all(c in stock_df.columns for c in STOCK_COLS) else pd.DataFrame(columns=STOCK_COLS)
    else:
        st.session_state.stock_df = pd.DataFrame(columns=STOCK_COLS)

# ==========================================
# 7. OTOMATIK AKTARIM (KAYNAKLAR)
# ==========================================
auto_imported = []

if not resources_df.empty:
    for _, resource in resources_df.iterrows():
        resource_name = resource.get('resource_name', '')
        if resource_name:
            existing = st.session_state.costs_df[
                (st.session_state.costs_df['cost_name'] == resource_name) &
                (st.session_state.costs_df['source_type'] == 'auto')
            ]
            if existing.empty:
                new_row = {
                    'wbs_code': resource.get('wbs_code', ''),
                    'cost_name': resource_name,
                    'unit_price': float(resource.get('unit_price', 0)),
                    'nakliye': 0,
                    'iscilik': 0,
                    'other_costs': 0,
                    'total_unit_cost': float(resource.get('unit_price', 0)),
                    'quantity': float(resource.get('quantity', 0)),
                    'total_cost': float(resource.get('unit_price', 0)) * float(resource.get('quantity', 0)),
                    'cost_category': 'Malzeme',
                    'is_prolongation': False,
                    'prolongation_cost': 0,
                    'source_type': 'auto',
                    'notes': 'Veri girisinden otomatik aktarildi'
                }
                auto_imported.append(new_row)

if not work_types_df.empty:
    for _, wt in work_types_df.iterrows():
        work_name = wt.get('work_name', '')
        if work_name:
            existing = st.session_state.costs_df[
                (st.session_state.costs_df['cost_name'] == work_name) &
                (st.session_state.costs_df['source_type'] == 'auto')
            ]
            if existing.empty:
                new_row = {
                    'wbs_code': wt.get('wbs_code', ''),
                    'cost_name': work_name,
                    'unit_price': float(wt.get('unit_price', 0)),
                    'nakliye': 0,
                    'iscilik': 0,
                    'other_costs': 0,
                    'total_unit_cost': float(wt.get('unit_price', 0)),
                    'quantity': float(wt.get('quantity', 0)),
                    'total_cost': float(wt.get('unit_price', 0)) * float(wt.get('quantity', 0)),
                    'cost_category': 'Iscilik',
                    'is_prolongation': False,
                    'prolongation_cost': 0,
                    'source_type': 'auto',
                    'notes': 'Veri girisinden otomatik aktarildi'
                }
                auto_imported.append(new_row)

if auto_imported:
    auto_df = pd.DataFrame(auto_imported)
    st.session_state.costs_df = pd.concat([st.session_state.costs_df, auto_df], ignore_index=True)

# ==========================================
# 8. SEKMELER
# ==========================================
tab1, tab2, tab3 = st.tabs([
    "📊 Maliyet Kalemleri",
    "➕ Manuel Giderler",
    "📦 Stok/Malzeme"
])

# ==========================================
# TAB 1: MALIYET KALEMLERI
# ==========================================
with tab1:
    st.markdown("### Maliyet Girdileri")
    st.caption("WBS kod secin -> Birim maliyet, nakliye, iscilik ve diger giderleri girin. Toplamlar otomatik hesaplanir.")
    
    wbs_options = [""] + wbs_list
    for idx, row in st.session_state.costs_df.iterrows():
        if pd.isna(row.get('wbs_code')) or row.get('wbs_code') == '':
            continue
        if row.get('wbs_code') not in wbs_options:
            wbs_options.append(row.get('wbs_code'))
    
    wbs_options = sorted(list(set(wbs_options)))
    
    edited_costs_df = st.data_editor(
        st.session_state.costs_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "wbs_code": st.column_config.SelectboxColumn(
                "WBS Kodu",
                options=wbs_options,
                required=False,
                width="medium"
            ),
            "cost_name": st.column_config.TextColumn(
                "Maliyet Kalemi",
                required=True,
                width="large"
            ),
            "unit_price": st.column_config.NumberColumn(
                "Birim Maliyet (TL)",
                min_value=0.0,
                step=0.01,
                format="%.2f",
                width="medium"
            ),
            "nakliye": st.column_config.NumberColumn(
                "Nakliye (TL)",
                min_value=0.0,
                step=0.01,
                format="%.2f",
                width="medium"
            ),
            "iscilik": st.column_config.NumberColumn(
                "Tasima Iscilik (TL)",
                min_value=0.0,
                step=0.01,
                format="%.2f",
                width="medium"
            ),
            "other_costs": st.column_config.NumberColumn(
                "Diger Giderler (TL)",
                min_value=0.0,
                step=0.01,
                format="%.2f",
                width="medium"
            ),
            "total_unit_cost": st.column_config.NumberColumn(
                "Toplam Birim Maliyet (TL)",
                disabled=True,
                format="%.2f",
                width="medium"
            ),
            "quantity": st.column_config.NumberColumn(
                "Kesif Metraji",
                min_value=0.0,
                step=0.1,
                format="%.2f",
                width="medium"
            ),
            "total_cost": st.column_config.NumberColumn(
                "Toplam Maliyet (TL)",
                disabled=True,
                format="%.2f",
                width="medium"
            ),
            "cost_category": st.column_config.SelectboxColumn(
                "Maliyet Kategorisi",
                options=["Iscilik", "Makina", "Malzeme", "Alt Yuklenici", "Nakliye", "Genel Gider", "Gecikme Maliyeti"],
                required=True,
                width="medium"
            ),
            "is_prolongation": st.column_config.CheckboxColumn(
                "Gecikme Maliyeti",
                width="small"
            ),
            "prolongation_cost": st.column_config.NumberColumn(
                "Gecikme Tutari (TL)",
                min_value=0.0,
                step=0.01,
                format="%.2f",
                width="medium"
            ),
            "source_type": st.column_config.TextColumn(
                "Kaynak Tipi",
                width="small",
                disabled=True
            ),
            "notes": st.column_config.TextColumn(
                "Notlar",
                width="medium"
            )
        },
        key="costs_grid"
    )
    
    # Otomatik hesaplamalar
    if not edited_costs_df.empty:
        edited_costs_df["total_unit_cost"] = (
            edited_costs_df["unit_price"].fillna(0) +
            edited_costs_df["nakliye"].fillna(0) +
            edited_costs_df["iscilik"].fillna(0) +
            edited_costs_df["other_costs"].fillna(0)
        )
        
        edited_costs_df["total_cost"] = (
            edited_costs_df["total_unit_cost"] * edited_costs_df["quantity"].fillna(0) +
            edited_costs_df["prolongation_cost"].fillna(0)
        )
        
        for idx, row in edited_costs_df.iterrows():
            wbs = row.get("wbs_code")
            if wbs and wbs in wbs_map:
                if pd.isna(row.get("quantity")) or row.get("quantity") == 0:
                    edited_costs_df.at[idx, "quantity"] = wbs_map[wbs].get("quantity", 0)
                if pd.isna(row.get("cost_name")) or row.get("cost_name") == "":
                    edited_costs_df.at[idx, "cost_name"] = wbs_map[wbs].get("item_name", "")
    
    st.session_state.costs_df = edited_costs_df

# ==========================================
# TAB 2: MANUEL GIDERLER
# ==========================================
with tab2:
    st.markdown("### Manuel Gider Girisi")
    st.caption("Otomatik hesaplanmayan, özel gider kalemlerini ekleyin")
    
    # Gider ekleme formu
    with st.expander("Yeni Gider Ekle", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            gider_adi = st.text_input("Gider Adi", placeholder="Örn: Özel İmalat", key="gider_adi")
        with col2:
            gider_miktar = st.number_input("Miktar", min_value=0.0, step=0.5, key="gider_miktar")
        with col3:
            gider_birim = st.number_input("Birim Fiyat (TL)", min_value=0.0, step=1.0, key="gider_birim")
        with col4:
            gider_kategori = st.selectbox(
                "Kategori",
                ["İşçilik", "Malzeme", "Ekipman", "Nakliye", "Genel Gider", "Özel İmalat", "Diğer"],
                key="gider_kategori"
            )
        
        col1b, col2b = st.columns(2)
        with col1b:
            gider_tarih = st.date_input("Tarih", datetime.now(), key="gider_tarih")
        with col2b:
            gider_aciklama = st.text_input("Açıklama", placeholder="Detaylı açıklama", key="gider_aciklama")
        
        if st.button("Gider Ekle", use_container_width=True, key="add_manual_expense"):
            if gider_adi:
                toplam = gider_miktar * gider_birim
                st.session_state.manual_giderler.append({
                    "gider_adi": gider_adi,
                    "miktar": gider_miktar,
                    "birim_fiyat": gider_birim,
                    "toplam": toplam,
                    "kategori": gider_kategori,
                    "tarih": str(gider_tarih),
                    "aciklama": gider_aciklama
                })
                toast_success("Başarılı", f"'{gider_adi}' gideri eklendi!")
                st.rerun()
            else:
                toast_warning("Uyarı", "Lütfen gider adı girin.")
    
    # Gider listesi
    if st.session_state.manual_giderler:
        st.markdown("### Eklenen Giderler")
        
        df_manual = pd.DataFrame(st.session_state.manual_giderler)
        st.dataframe(df_manual, use_container_width=True, hide_index=True)
        
        # Toplam gider
        toplam_manuel = df_manual["toplam"].sum()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Toplam Manuel Gider", f"{toplam_manuel:,.2f} TL")
        with col2:
            st.metric("Gider Sayısı", len(df_manual))
        with col3:
            # Kategori bazlı
            if len(df_manual) > 0:
                kategori_top = df_manual.groupby("kategori")["toplam"].sum().sort_values(ascending=False)
                if not kategori_top.empty:
                    st.metric("En Büyük Kategori", f"{kategori_top.index[0]}", f"{kategori_top.iloc[0]:,.2f} TL")
        
        # Kategori bazlı dağılım
        with st.expander("Kategori Bazlı Dağılım"):
            if len(df_manual) > 0:
                kategori_df = df_manual.groupby("kategori").agg({
                    "toplam": "sum",
                    "gider_adi": "count"
                }).reset_index()
                kategori_df.columns = ["Kategori", "Toplam Tutar", "Gider Sayısı"]
                st.dataframe(kategori_df, use_container_width=True, hide_index=True)
        
        # Silme butonu
        if st.button("Tüm Manuel Giderleri Temizle", use_container_width=True, key="clear_manual"):
            st.session_state.manual_giderler = []
            toast_info("Bilgi", "Tüm manuel giderler temizlendi.")
            st.rerun()
    else:
        st.info("Henüz manuel gider eklenmemiş.")

# ==========================================
# TAB 3: STOK/MALZEME
# ==========================================
with tab3:
    st.markdown("### Stok ve Malzeme Yönetimi")
    st.caption("Malzeme envanterini takip edin, miktar ve değer bilgilerini girin")
    
    # Stok ekleme formu
    with st.expander("Yeni Malzeme Ekle", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            stock_name = st.text_input("Malzeme Adı", placeholder="Örn: Bosch Matkap Ucu", key="stock_name")
            stock_category = st.selectbox(
                "Kategori",
                ["Sarf Malzeme", "Alet Ekipman", "Hırdavat", "Elektrik", "Diğer"],
                key="stock_category"
            )
        with col2:
            stock_quantity = st.number_input("Miktar", min_value=0.0, step=0.5, key="stock_quantity")
            stock_unit_price = st.number_input("Birim Fiyat (TL)", min_value=0.0, step=1.0, key="stock_unit_price")
        with col3:
            stock_supplier = st.text_input("Tedarikçi", placeholder="Tedarikçi adı", key="stock_supplier")
            stock_location = st.text_input("Lokasyon", placeholder="Depo/Raf", key="stock_location")
        
        stock_notes = st.text_area("Notlar", placeholder="Malzeme hakkında ek bilgiler", key="stock_notes")
        
        if st.button("Malzemeyi Ekle", use_container_width=True, key="add_stock"):
            if stock_name:
                total_value = stock_quantity * stock_unit_price
                new_stock = {
                    "stock_name": stock_name,
                    "quantity": stock_quantity,
                    "unit_price": stock_unit_price,
                    "total_value": total_value,
                    "category": stock_category,
                    "supplier": stock_supplier,
                    "purchase_date": str(datetime.now().date()),
                    "location": stock_location,
                    "notes": stock_notes
                }
                st.session_state.stock_df = pd.concat([
                    st.session_state.stock_df,
                    pd.DataFrame([new_stock])
                ], ignore_index=True)
                toast_success("Başarılı", f"'{stock_name}' stok eklendi!")
                st.rerun()
            else:
                toast_warning("Uyarı", "Lütfen malzeme adı girin.")
    
    # Stok listesi
    if not st.session_state.stock_df.empty:
        st.markdown("### Mevcut Stoklar")
        
        edited_stock_df = st.data_editor(
            st.session_state.stock_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "stock_name": st.column_config.TextColumn("Malzeme Adı", required=True),
                "quantity": st.column_config.NumberColumn("Miktar", min_value=0.0, step=0.5),
                "unit_price": st.column_config.NumberColumn("Birim Fiyat (TL)", min_value=0.0, step=1.0, format="%.2f"),
                "total_value": st.column_config.NumberColumn("Toplam Değer (TL)", disabled=True, format="%.2f"),
                "category": st.column_config.SelectboxColumn(
                    "Kategori",
                    options=["Sarf Malzeme", "Alet Ekipman", "Hırdavat", "Elektrik", "Diğer"]
                ),
                "supplier": st.column_config.TextColumn("Tedarikçi"),
                "purchase_date": st.column_config.DateColumn("Alım Tarihi"),
                "location": st.column_config.TextColumn("Lokasyon"),
                "notes": st.column_config.TextColumn("Notlar")
            },
            key="stock_grid"
        )
        
        # Total value hesapla
        if not edited_stock_df.empty:
            edited_stock_df["total_value"] = edited_stock_df["quantity"].fillna(0) * edited_stock_df["unit_price"].fillna(0)
        
        st.session_state.stock_df = edited_stock_df
        
        # Stok özeti
        st.markdown("### Stok Özeti")
        col1, col2, col3, col4 = st.columns(4)
        
        total_items = len(edited_stock_df)
        total_stock_value = edited_stock_df["total_value"].sum() if not edited_stock_df.empty else 0
        avg_unit_price = edited_stock_df["unit_price"].mean() if not edited_stock_df.empty else 0
        
        with col1:
            st.metric("Toplam Malzeme", total_items)
        with col2:
            st.metric("Toplam Stok Değeri", f"{total_stock_value:,.2f} TL")
        with col3:
            st.metric("Ortalama Birim Fiyat", f"{avg_unit_price:,.2f} TL")
        with col4:
            # Kategori dağılımı
            if not edited_stock_df.empty:
                kategori_sayisi = edited_stock_df["category"].nunique()
                st.metric("Kategori Sayısı", kategori_sayisi)
        
        # Kategori bazlı stok dağılımı
        with st.expander("Kategori Bazlı Stok Dağılımı"):
            if not edited_stock_df.empty:
                kategori_stok = edited_stock_df.groupby("category").agg({
                    "total_value": "sum",
                    "stock_name": "count"
                }).reset_index()
                kategori_stok.columns = ["Kategori", "Toplam Değer", "Malzeme Sayısı"]
                st.dataframe(kategori_stok, use_container_width=True, hide_index=True)
        
        # Stoktan maliyete aktar butonu
        if st.button("Seçili Malzemeleri Maliyete Aktar", use_container_width=True, key="stock_to_cost"):
            if not edited_stock_df.empty:
                # Tüm stok kalemlerini maliyet tablosuna aktar
                for _, row in edited_stock_df.iterrows():
                    stock_name = row.get("stock_name", "")
                    if stock_name:
                        existing = st.session_state.costs_df[
                            (st.session_state.costs_df["cost_name"] == stock_name) &
                            (st.session_state.costs_df["source_type"] == "stock")
                        ]
                        if existing.empty:
                            new_row = {
                                "wbs_code": "",
                                "cost_name": stock_name,
                                "unit_price": float(row.get("unit_price", 0)),
                                "nakliye": 0,
                                "iscilik": 0,
                                "other_costs": 0,
                                "total_unit_cost": float(row.get("unit_price", 0)),
                                "quantity": float(row.get("quantity", 0)),
                                "total_cost": float(row.get("total_value", 0)),
                                "cost_category": "Malzeme",
                                "is_prolongation": False,
                                "prolongation_cost": 0,
                                "source_type": "stock",
                                "notes": f"Stoktan aktarıldı - {row.get('category', '')}"
                            }
                            st.session_state.costs_df = pd.concat([
                                st.session_state.costs_df,
                                pd.DataFrame([new_row])
                            ], ignore_index=True)
                
                toast_success("Başarılı", "Stok kalemleri maliyete aktarıldı!")
                st.rerun()
    else:
        st.info("Henüz stok kaydı yok. 'Yeni Malzeme Ekle' ile başlayın.")

# ==========================================
# 9. OZET METRIKLER (TÜM TABLOLAR)
# ==========================================
st.markdown("---")
st.markdown("### Genel Maliyet Özeti")

total_cost = st.session_state.costs_df["total_cost"].sum() if not st.session_state.costs_df.empty else 0
total_manual = sum([g["toplam"] for g in st.session_state.manual_giderler]) if st.session_state.manual_giderler else 0
total_stock = st.session_state.stock_df["total_value"].sum() if not st.session_state.stock_df.empty else 0

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
        <p style="color: #737373; font-size: 0.6rem; margin: 0;">Toplam Maliyet</p>
        <h4 style="color: #22c55e; margin: 0.2rem 0;">{total_cost + total_manual:,.2f} TL</h4>
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
        <p style="color: #737373; font-size: 0.6rem; margin: 0;">Manuel Giderler</p>
        <h4 style="color: #f59e0b; margin: 0.2rem 0;">{total_manual:,.2f} TL</h4>
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
        <p style="color: #737373; font-size: 0.6rem; margin: 0;">Stok Değeri</p>
        <h4 style="color: #3b82f6; margin: 0.2rem 0;">{total_stock:,.2f} TL</h4>
    </div>
    """, unsafe_allow_html=True)

with col4:
    total_entries = len(st.session_state.costs_df) + len(st.session_state.manual_giderler) + len(st.session_state.stock_df)
    st.markdown(f"""
    <div class="animate-card" style="
        background-color: #141414;
        padding: 0.8rem;
        border-radius: 12px;
        border: 1px solid #262626;
        text-align: center;
    ">
        <p style="color: #737373; font-size: 0.6rem; margin: 0;">Toplam Kalem</p>
        <h4 style="color: #ffffff; margin: 0.2rem 0;">{total_entries}</h4>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 10. EXCEL IMPORT / EXPORT
# ==========================================
st.markdown("---")
st.markdown("### Excel İşlemleri")

col_imp, col_exp = st.columns(2)

with col_imp:
    st.markdown("#### Excel'den İçe Aktar")
    uploaded_file = st.file_uploader(
        "Excel dosyası seçin",
        type=['xlsx', 'xls'],
        key="cost_import"
    )
    
    if uploaded_file is not None:
        if st.button("Excel'i İçe Aktar", key="import_btn"):
            try:
                import_df = pd.read_excel(uploaded_file)
                
                if "wbs_code" in import_df.columns:
                    valid_wbs = set(wbs_list)
                    import_df = import_df[import_df["wbs_code"].isin(valid_wbs) | import_df["wbs_code"].isna()]
                    
                    if import_df.empty:
                        toast_warning("Uyarı", "Bu projeye ait WBS kodu bulunamadı.")
                    else:
                        imported_count = 0
                        for _, row in import_df.iterrows():
                            wbs_code = row.get("wbs_code", "")
                            cost_name = row.get("cost_name", "")
                            
                            if not cost_name:
                                continue
                            
                            existing_idx = st.session_state.costs_df[
                                (st.session_state.costs_df["wbs_code"] == wbs_code) &
                                (st.session_state.costs_df["cost_name"] == cost_name)
                            ].index
                            
                            new_row = {
                                "wbs_code": wbs_code,
                                "cost_name": cost_name,
                                "unit_price": float(row.get("unit_price", 0)),
                                "nakliye": float(row.get("nakliye", 0)),
                                "iscilik": float(row.get("iscilik", 0)),
                                "other_costs": float(row.get("other_costs", 0)),
                                "quantity": float(row.get("quantity", 0)),
                                "cost_category": row.get("cost_category", "Genel Gider"),
                                "is_prolongation": bool(row.get("is_prolongation", False)),
                                "prolongation_cost": float(row.get("prolongation_cost", 0)),
                                "source_type": "manual",
                                "notes": row.get("notes", "Excel'den iç aktarıldı")
                            }
                            
                            if existing_idx.empty:
                                st.session_state.costs_df = pd.concat([
                                    st.session_state.costs_df,
                                    pd.DataFrame([new_row])
                                ], ignore_index=True)
                            else:
                                for col in new_row:
                                    st.session_state.costs_df.at[existing_idx[0], col] = new_row[col]
                            imported_count += 1
                        
                        toast_success("Başarılı", f"{imported_count} satır iç aktarıldı!")
                        st.rerun()
                else:
                    toast_error("Hata", "Excel'de 'wbs_code' sütunu bulunamadı!")
                    
            except Exception as e:
                toast_error("Hata", f"Excel okuma hatası: {e}")

with col_exp:
    st.markdown("#### Excel'e Dışa Aktar")
    
    all_data = st.session_state.costs_df.copy()
    
    if not all_data.empty or st.session_state.manual_giderler or not st.session_state.stock_df.empty:
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Maliyet kalemleri
            if not all_data.empty:
                all_data.to_excel(writer, sheet_name='Maliyetler', index=False)
            
            # Manuel giderler
            if st.session_state.manual_giderler:
                df_manual = pd.DataFrame(st.session_state.manual_giderler)
                df_manual.to_excel(writer, sheet_name='Manuel Giderler', index=False)
            
            # Stoklar
            if not st.session_state.stock_df.empty:
                st.session_state.stock_df.to_excel(writer, sheet_name='Stoklar', index=False)
            
            # Özet
            summary_data = {
                "Toplam Maliyet": [all_data["total_cost"].sum() if not all_data.empty else 0],
                "Toplam Manuel Gider": [sum([g["toplam"] for g in st.session_state.manual_giderler]) if st.session_state.manual_giderler else 0],
                "Toplam Stok Değeri": [st.session_state.stock_df["total_value"].sum() if not st.session_state.stock_df.empty else 0]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Özet', index=False)
            
            workbook = writer.book
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_length = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_length
        
        output.seek(0)
        
        st.download_button(
            label="Excel Dosyasını İndir",
            data=output.getvalue(),
            file_name=f"maliyet_{selected_project}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    else:
        st.info("Dışa aktarılacak veri yok.")

# ==========================================
# 11. KAYDET
# ==========================================
st.markdown("---")

if st.button("Tüm Verileri Kaydet", type="primary", use_container_width=True):
    try:
        saved_count = 0
        
        with loading_spinner("Veriler kaydediliyor..."):
            # 1. Maliyet kalemlerini kaydet
            if not st.session_state.costs_df.empty:
                cost_rows = st.session_state.costs_df.to_dict(orient="records")
                clean_costs = [r for r in cost_rows if str(r.get("cost_name", "")).strip()]
                
                if clean_costs:
                    supabase.table("project_costs").delete().eq("project_id", project_id).execute()
                    for r in clean_costs:
                        r["project_id"] = project_id
                        r.pop("id", None)
                        
                        for key in ["unit_price", "nakliye", "iscilik", "other_costs", 
                                   "total_unit_cost", "quantity", "total_cost", "prolongation_cost"]:
                            if pd.isna(r.get(key)) or np.isinf(r.get(key, 0)):
                                r[key] = 0.0
                        
                        for key in ["wbs_code", "cost_name", "cost_category", "notes", "source_type"]:
                            if r.get(key) == "":
                                r[key] = None
                        
                        if r.get("is_prolongation") is None:
                            r["is_prolongation"] = False
                        
                        r["total_price"] = r.get("total_cost", 0)
                        supabase.table("project_costs").insert(r).execute()
                    saved_count += len(clean_costs)
            
            # 2. Manuel giderleri kaydet
            if st.session_state.manual_giderler:
                manual_data = {
                    "project_id": project_id,
                    "giderler": st.session_state.manual_giderler,
                    "updated_at": str(datetime.now())
                }
                supabase.table("project_manual_expenses").delete().eq("project_id", project_id).execute()
                supabase.table("project_manual_expenses").insert(manual_data).execute()
                saved_count += len(st.session_state.manual_giderler)
            
            # 3. Stokları kaydet
            if not st.session_state.stock_df.empty:
                stock_rows = st.session_state.stock_df.to_dict(orient="records")
                clean_stock = [r for r in stock_rows if str(r.get("stock_name", "")).strip()]
                
                if clean_stock:
                    supabase.table("project_stock").delete().eq("project_id", project_id).execute()
                    for r in clean_stock:
                        r["project_id"] = project_id
                        r.pop("id", None)
                        
                        for key in ["quantity", "unit_price", "total_value"]:
                            if pd.isna(r.get(key)) or np.isinf(r.get(key, 0)):
                                r[key] = 0.0
                        
                        r["purchase_date"] = str(r.get("purchase_date", datetime.now().date()))
                        supabase.table("project_stock").insert(r).execute()
                    saved_count += len(clean_stock)
            
            time.sleep(0.3)
        
        toast_success("Başarılı", f"{saved_count} kayıt başarıyla kaydedildi!")
        st.cache_data.clear()
        st.rerun()
        
    except Exception as e:
        toast_error("Hata", f"Kayıt sırasında hata oluştu: {str(e)}")

# ==========================================
# 12. BILGI ALANI
# ==========================================
with st.expander("Kullanım Kılavuzu"):
    st.markdown("""
    **Maliyet Girişi Nasıl Kullanılır?**
    
    **1. Maliyet Kalemleri (Tab 1)**
    - WBS Kodu seçin (Keşif sayfasından gelir)
    - Birim maliyet, nakliye, işçilik ve diğer giderleri girin
    - Toplamlar otomatik hesaplanır
    - Gecikme maliyeti için kutucuğu işaretleyin
    
    **2. Manuel Giderler (Tab 2)**
    - Otomatik hesaplanmayan özel gider kalemlerini ekleyin
    - Gider adı, miktar, birim fiyat ve kategori girin
    - Tarih ve açıklama ekleyebilirsiniz
    
    **3. Stok/Malzeme (Tab 3)**
    - Malzeme envanterini takip edin
    - Miktar, birim fiyat, tedarikçi ve lokasyon girin
    - Stoktan maliyete aktar butonu ile kolayca taşıyın
    
    **Excel İşlemleri**
    - Dışa aktar: Tüm verileri (maliyet, manuel gider, stok) Excel'e aktarır
    - İçe aktar: Sadece aynı projeye ait WBS kodları ile eşleşen verileri alır
    """)

st.markdown('</div>', unsafe_allow_html=True)