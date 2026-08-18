# -*- coding: utf-8 -*-
"""
Created on Wed Aug 19 02:28:53 2026

@author: taric
"""

import streamlit as st
import datetime
import pandas as pd
from utils.db import (
    get_user_projects, create_project, get_previous_day_value, 
    save_daily_resources, get_work_progress_by_date, save_work_progress, get_previous_day_progress
)
from utils.lists import (
    ENDIRECT_PERSONEL, DIRECT_PERSONEL, YAPI_MALZEME, DEMIRBASLAR, 
    SARF_MALZEMELER, MAKINA, IS_TURLERI
)
from utils.styles import apply_global_styles, render_top_navbar

st.set_page_config(
    page_title="SARCON Portal | Veri Girişi",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

apply_global_styles(is_login=False)
render_top_navbar()

# --- 1. PROJE YÖNETİMİ & DİNAMİK YENİ PROJE MODALI ---
projects, err = get_user_projects()
project_names = [p["project_name"] for p in projects] if projects else []

if "show_new_project_modal" not in st.session_state:
    st.session_state.show_new_project_modal = False

if not project_names or st.session_state.show_new_project_modal:
    st.markdown("""
    <div style="background-color: #141414; padding: 1.2rem; border-radius: 8px; border: 1px solid #262626; margin-bottom: 1.5rem;">
        <h4 style="color: #ffffff; margin: 0 0 0.5rem 0;">Yeni Proje Oluştur</h4>
        <p style="color: #a3a3a3; font-size: 0.8rem; margin: 0;">Form elemanları arasında Tab ile gezinebilir, Enter ile kaydedebilirsiniz.</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("new_project_form", clear_on_submit=True):
        pname = st.text_input("Proje Adı", placeholder="Örn: Kadıköy Konut Projesi")
        c1, c2 = st.columns(2)
        with c1:
            start = st.date_input("Başlangıç Tarihi", datetime.date.today())
        with c2:
            end = st.date_input("Bitiş Tarihi", datetime.date.today() + datetime.timedelta(days=365))
            
        btn_c1, btn_c2 = st.columns([1, 1])
        with btn_c1:
            submit = st.form_submit_button("Proje Kaydet", type="primary", use_container_width=True)
        with btn_c2:
            cancel = st.form_submit_button("İptal", use_container_width=True)
            
        if submit:
            if pname:
                proj, create_err = create_project(pname.strip(), str(start), str(end))
                if proj:
                    st.success("Proje başarıyla oluşturuldu!")
                    st.session_state.show_new_project_modal = False
                    st.rerun()
                else:
                    st.error(f"Hata: {create_err}")
            else:
                st.warning("Lütfen proje adını girin.")
        if cancel:
            st.session_state.show_new_project_modal = False
            st.rerun()
            
    if not project_names:
        st.stop()

# --- BAŞLIK VE YENİ PROJE BUTONU ---
head_col1, head_col2 = st.columns([3, 1])
with head_col1:
    st.markdown("""
    <div style="border-left: 3px solid #3b82f6; padding-left: 0.8rem;">
        <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.3rem;">Veri Girişi</h3>
        <p style="color: #737373; margin: 0; font-size: 0.8rem;">Günlük kaynak ve iş ilerleme kayıtları</p>
    </div>
    """, unsafe_allow_html=True)
with head_col2:
    st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
    if st.button("Yeni Proje Oluştur", use_container_width=True):
        st.session_state.show_new_project_modal = True
        st.rerun()

st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

# --- PROJE VE TARİH SEÇİM ALANI ---
col_p1, col_p2 = st.columns([2, 2])
with col_p1:
    selected_project = st.selectbox("Aktif Proje", project_names, key="active_project_select")
    project_id = next(p["id"] for p in projects if p["project_name"] == selected_project)
with col_p2:
    report_date = st.date_input("Rapor Tarihi", datetime.date.today())

is_sunday = report_date.weekday() == 6
if is_sunday:
    st.warning("Pazar günü: Tüm kaynak ve ilerleme değerleri varsayılan olarak sıfırlanacaktır.")

st.markdown("<hr style='border-color: #262626; margin: 1.2rem 0;'>", unsafe_allow_html=True)

# ==========================================
# 2. KAYNAK GİRİŞİ (Tüm Türler İçin Dropdown + Yeni Ekleme)
# ==========================================
st.subheader("1. Kaynak Girişi")

resource_type = st.selectbox(
    "Kaynak Türü Seçin",
    ["Endirekt Personel", "Direkt Personel", "Yapı Malzemesi", "Demirbaşlar", "Sarf Malzemeler", "Makina"]
)

resource_map = {
    "Endirekt Personel": ENDIRECT_PERSONEL,
    "Direkt Personel": DIRECT_PERSONEL,
    "Yapı Malzemesi": YAPI_MALZEME,
    "Demirbaşlar": DEMIRBASLAR,
    "Sarf Malzemeler": SARF_MALZEMELER,
    "Makina": MAKINA,
}

selected_items = resource_map.get(resource_type, [])

# -- ÖNCEKİ GÜN VERİLERİNİ GETİR --
prev_day_data = {}
for item in selected_items:
    prev_val = get_previous_day_value(project_id, report_date, resource_type, item) if not is_sunday else 0
    if prev_val > 0:
        prev_day_data[item] = int(prev_val)

# -- SESSION STATE: KAYNAK SATIRLARI --
if "resource_rows" not in st.session_state or st.session_state.get("resource_type") != resource_type:
    st.session_state.resource_type = resource_type
    if prev_day_data:
        rows = [{"Kaynak": k, "Adet": v, "Birim": "", "Notlar": ""} for k, v in prev_day_data.items()]
    else:
        rows = [{"Kaynak": "", "Adet": 0, "Birim": "", "Notlar": ""}]
    st.session_state.resource_rows = rows

# -- Kaynak tipi için özel etiketler --
type_labels = {
    "Endirekt Personel": "Personel",
    "Direkt Personel": "Personel",
    "Yapı Malzemesi": "Malzeme",
    "Demirbaşlar": "Demirbaş",
    "Sarf Malzemeler": "Sarf Malzeme",
    "Makina": "Makina"
}

label = type_labels.get(resource_type, "Kaynak")

# -- DROPDOWN + YENİ EKLEME: Tüm kaynak türleri için --
col_search, col_button = st.columns([4, 1])

with col_search:
    options = sorted(selected_items) + [f"➕ Yeni {label} Ekle..."]
    
    selected_option = st.selectbox(
        f"{label} Ara / Seç",
        options=options,
        key=f"select_{resource_type}",
        label_visibility="collapsed",
        placeholder=f"{label} adı yazın veya listeden seçin..."
    )
    
    if selected_option == f"➕ Yeni {label} Ekle...":
        new_item = st.text_input(
            f"Yeni {label} Adı",
            placeholder=f"Örn: Yeni {label}",
            key=f"new_{resource_type}_input",
            label_visibility="collapsed"
        )
    else:
        new_item = None

with col_button:
    st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
    
    if st.button("➕ Ekle", key=f"add_{resource_type}", use_container_width=True):
        if new_item and new_item.strip():
            custom_key = f"custom_{resource_type}"
            if custom_key not in st.session_state:
                st.session_state[custom_key] = []
            if new_item.strip() not in st.session_state[custom_key]:
                st.session_state[custom_key].append(new_item.strip())
            
            item_name = new_item.strip()
            exists = False
            for row in st.session_state.resource_rows:
                if row["Kaynak"] == item_name:
                    row["Adet"] += 1
                    exists = True
                    break
            if not exists:
                empty_found = False
                for row in st.session_state.resource_rows:
                    if row["Kaynak"] == "":
                        row["Kaynak"] = item_name
                        row["Adet"] = 1
                        empty_found = True
                        break
                if not empty_found:
                    st.session_state.resource_rows.append({"Kaynak": item_name, "Adet": 1, "Birim": "", "Notlar": ""})
            st.rerun()
        
        elif selected_option and selected_option != f"➕ Yeni {label} Ekle...":
            item_name = selected_option
            exists = False
            for row in st.session_state.resource_rows:
                if row["Kaynak"] == item_name:
                    row["Adet"] += 1
                    exists = True
                    break
            if not exists:
                empty_found = False
                for row in st.session_state.resource_rows:
                    if row["Kaynak"] == "":
                        row["Kaynak"] = item_name
                        row["Adet"] = 1
                        empty_found = True
                        break
                if not empty_found:
                    st.session_state.resource_rows.append({"Kaynak": item_name, "Adet": 1, "Birim": "", "Notlar": ""})
            st.rerun()

# -- DATA EDITOR --
custom_key = f"custom_{resource_type}"
custom_items = st.session_state.get(custom_key, [])
display_items = sorted(set(selected_items + custom_items))

edited_resources_df = st.data_editor(
    pd.DataFrame(st.session_state.resource_rows),
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Kaynak": st.column_config.SelectboxColumn(
            "Kaynak / Malzeme",
            options=display_items,
            required=True
        ),
        "Adet": st.column_config.NumberColumn("Adet / Miktar", min_value=0, step=1, format="%d"),
        "Birim": st.column_config.TextColumn("Birim"),
        "Notlar": st.column_config.TextColumn("Notlar / Açıklama")
    },
    key=f"res_grid_{resource_type}_{report_date}"
)

st.session_state.resource_rows = edited_resources_df.to_dict(orient="records")

st.markdown("<hr style='border-color: #262626; margin: 1.5rem 0;'>", unsafe_allow_html=True)

# ==========================================
# 3. İŞ İLERLEME (NCR KALDIRILDI)
# ==========================================
st.subheader("2. İş İlerleme")

existing_rows, _ = get_work_progress_by_date(project_id, report_date)

if "work_df" not in st.session_state or st.session_state.get("current_date") != report_date:
    st.session_state.current_date = report_date
    if existing_rows:
        st.session_state.work_df = pd.DataFrame(existing_rows)
    else:
        prev_rows, _ = get_work_progress_by_date(project_id, report_date - datetime.timedelta(days=1))
        if prev_rows and not is_sunday:
            for r in prev_rows:
                r["ilerleme_yuzdesi"] = 0.0
                r["yapilan_miktar"] = 0.0
            st.session_state.work_df = pd.DataFrame(prev_rows)
        else:
            st.session_state.work_df = pd.DataFrame(columns=[
                "bolge", "blok", "mahal", "aks_x", "aks_y", "kot", "is_turu", 
                "yapilan_is", "alt_yuklenici", "birim", "ilerleme_yuzdesi", 
                "kesif_miktari", "yapilan_miktar", "wbs_kodu", "butce_kodu"
            ])

edited_work_df = st.data_editor(
    st.session_state.work_df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "bolge": st.column_config.TextColumn("Bölge"),
        "blok": st.column_config.TextColumn("Blok"),
        "mahal": st.column_config.TextColumn("Mahal"),
        "aks_x": st.column_config.TextColumn("Aks-X"),
        "aks_y": st.column_config.TextColumn("Aks-Y"),
        "kot": st.column_config.TextColumn("Kot"),
        "is_turu": st.column_config.SelectboxColumn("İş Türü", options=IS_TURLERI, required=True),
        "yapilan_is": st.column_config.TextColumn("Yapılan İş"),
        "alt_yuklenici": st.column_config.TextColumn("Alt Yüklenici"),
        "birim": st.column_config.TextColumn("Birim"),
        "ilerleme_yuzdesi": st.column_config.NumberColumn("% İlerleme", min_value=0.0, max_value=100.0, step=0.5, format="%.1f%%"),
        "kesif_miktari": st.column_config.NumberColumn("Keşif", min_value=0.0, step=1.0),
        "yapilan_miktar": st.column_config.NumberColumn("Yapılan", disabled=True, format="%.1f"),
        "wbs_kodu": st.column_config.TextColumn("WBS"),
        "butce_kodu": st.column_config.TextColumn("Bütçe")
    },
    key="work_grid"
)

# Yapılan miktar otomatik hesaplanır (NCR kontrolü KALDIRILDI)
if not edited_work_df.empty:
    edited_work_df["yapilan_miktar"] = (edited_work_df["kesif_miktari"].fillna(0) * edited_work_df["ilerleme_yuzdesi"].fillna(0)) / 100.0

st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

# ==========================================
# 4. TÜM VERİLERİ KAYDET
# ==========================================
if st.button("Tüm Verileri Kaydet", type="primary", use_container_width=True):
    # Kaynak verilerini kaydet
    resource_payload = {}
    for _, row in edited_resources_df.iterrows():
        if row["Kaynak"] and row["Adet"] > 0:
            resource_payload[row["Kaynak"]] = int(row["Adet"])
    
    success = True
    if resource_payload:
        ok, err = save_daily_resources(project_id, report_date, resource_type, resource_payload)
        if not ok:
            st.error(f"Kaynak verisi kaydedilemedi: {err}")
            success = False
        else:
            st.success("Kaynak verileri kaydedildi!")
    else:
        st.info("Kaynak verisi girilmedi.")
    
    # İş ilerleme verilerini kaydet
    if success:
        rows_to_save = edited_work_df.to_dict(orient="records") if not edited_work_df.empty else []
        clean_rows = [r for r in rows_to_save if str(r.get("yapilan_is", "")).strip()]
        
        if clean_rows:
            ok_w, err_w = save_work_progress(project_id, report_date, clean_rows)
            if not ok_w:
                st.error(f"İş ilerleme verisi kaydedilemedi: {err_w}")
            else:
                st.success("İş ilerleme verileri kaydedildi!")
        else:
            st.info("İş ilerleme verisi girilmedi.")
        
        st.balloons()