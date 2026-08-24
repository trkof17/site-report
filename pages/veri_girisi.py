# -*- coding: utf-8 -*-
"""
Created on Wed Aug 19 02:28:53 2026
@author: taric
Updated: 2026-08-24 - Kaynak girişine iş türü, WBS, birim fiyat/maliyet eklendi
"""

import streamlit as st
import datetime
import pandas as pd
import numpy as np
import time
from utils.db import (
    get_user_projects, create_project, get_previous_day_value, 
    save_daily_resources, get_work_progress_by_date, save_work_progress,
    save_other_expense, get_other_expenses
)
from utils.lists import (
    ENDIRECT_PERSONEL, DIRECT_PERSONEL, YAPI_MALZEME, DEMIRBASLAR, 
    SARF_MALZEMELER, MAKINA, IS_TURLERI, HARCAMA_TURLERI, WBS_KODLARI
)
from utils.styles import apply_global_styles
from utils.top_navbar import render_top_navbar
from utils.animations import (
    loading_spinner,
    toast_success,
    toast_error,
    toast_warning,
    toast_info,
)

st.set_page_config(
    page_title="SARCON Portal | Veri Girisi",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

apply_global_styles(is_login=False)
render_top_navbar()

st.markdown('<div class="page-content">', unsafe_allow_html=True)

# ==========================================
# BİRİM SABİTLEMELERİ
# ==========================================

RESOURCE_UNIT_OPTIONS = {
    "Endirekt Personel": ["Adam/Gün"],
    "Direkt Personel": ["Adam/Gün"],
    "Makina": ["Makina/Saat"],
    "Yapı Malzemesi": ["m²", "m³", "ton", "adet", "kg", "metre"],
    "Demirbaşlar": ["adet"],
    "Sarf Malzemeler": ["adet", "kg", "metre"]
}

WORK_UNIT_OPTIONS = ["m²", "m³", "ton", "adet", "kg", "metre"]

# ==========================================
# CTRL+S KISAYOLU İÇİN JAVASCRIPT
# ==========================================
st.markdown("""
<script>
document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        const buttons = document.querySelectorAll('button');
        for (let btn of buttons) {
            if (btn.textContent.includes('Tum Verileri Kaydet')) {
                btn.click();
                break;
            }
        }
    }
});
</script>
""", unsafe_allow_html=True)

# ==========================================
# 1. PROJE YÖNETİMİ
# ==========================================
with st.spinner("Projeler yukleniyor..."):
    projects, err = get_user_projects()
    time.sleep(0.3)

project_names = [p["project_name"] for p in projects] if projects else []

if "show_new_project_modal" not in st.session_state:
    st.session_state.show_new_project_modal = False

if not project_names or st.session_state.show_new_project_modal:
    st.markdown("""
    <div style="
        background-color: #141414; 
        padding: 1.2rem; 
        border-radius: 8px; 
        border: 1px solid #262626; 
        margin-bottom: 1.5rem;
    ">
        <h4 style="color: #ffffff; margin: 0 0 0.5rem 0;">Yeni Proje Olustur</h4>
        <p style="color: #a3a3a3; font-size: 0.8rem; margin: 0;">Form elemanlari arasinda Tab ile gezinebilir, Enter ile kaydedebilirsiniz.</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("new_project_form", clear_on_submit=True):
        pname = st.text_input("Proje Adi", placeholder="Orn: Kadikoy Konut Projesi")
        c1, c2 = st.columns(2)
        with c1:
            start = st.date_input("Baslangic Tarihi", datetime.date.today())
        with c2:
            end = st.date_input("Bitis Tarihi", datetime.date.today() + datetime.timedelta(days=365))
            
        btn_c1, btn_c2 = st.columns([1, 1])
        with btn_c1:
            submit = st.form_submit_button("Proje Kaydet", type="primary", use_container_width=True)
        with btn_c2:
            cancel = st.form_submit_button("Iptal", use_container_width=True)
            
        if submit:
            if pname:
                with st.spinner("Proje olusturuluyor..."):
                    proj, create_err = create_project(pname.strip(), str(start), str(end))
                    time.sleep(0.3)
                if proj:
                    st.success("Proje basariyla olusturuldu!")
                    st.session_state.show_new_project_modal = False
                    st.rerun()
                else:
                    st.error(f"Hata: {create_err}")
            else:
                st.warning("Lutfen proje adini girin.")
        if cancel:
            st.session_state.show_new_project_modal = False
            st.rerun()
            
    if not project_names:
        st.stop()

# --- BASLIK VE YENI PROJE BUTONU ---
head_col1, head_col2 = st.columns([3, 1])
with head_col1:
    st.markdown("""
    <div style="border-left: 3px solid #3b82f6; padding-left: 0.8rem;">
        <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.3rem;">Veri Girisi</h3>
        <p style="color: #737373; margin: 0; font-size: 0.8rem;">Gunluk kaynak ve is ilerleme kayitlari</p>
        <p style="color: #525252; margin: 0; font-size: 0.7rem;">Ctrl+S ile tum verileri kaydedebilirsiniz</p>
    </div>
    """, unsafe_allow_html=True)
with head_col2:
    st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
    if st.button("Yeni Proje Olustur", use_container_width=True):
        st.session_state.show_new_project_modal = True
        st.rerun()

st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

# --- PROJE VE TARIH SECIM ALANI ---
col_p1, col_p2 = st.columns([2, 2])
with col_p1:
    selected_project = st.selectbox("Aktif Proje", project_names, key="active_project_select")
    project_id = next(p["id"] for p in projects if p["project_name"] == selected_project)
with col_p2:
    report_date = st.date_input("Rapor Tarihi", datetime.date.today())

is_sunday = report_date.weekday() == 6
if is_sunday:
    st.warning("Pazar gunu: Tum kaynak ve ilerleme degerleri varsayilan olarak sifirlanacaktir.")

st.markdown("<hr style='border-color: #262626; margin: 1.2rem 0;'>", unsafe_allow_html=True)

# ==========================================
# 2. KAYNAK GIRISI (GÜNCELLENMİŞ)
# ==========================================
st.subheader("1. Kaynak Girisi")

resource_type = st.selectbox(
    "Kaynak Turu Secin",
    ["Endirekt Personel", "Direkt Personel", "Yapi Malzemesi", "Demirbaslar", "Sarf Malzemeler", "Makina"]
)

resource_map = {
    "Endirekt Personel": ENDIRECT_PERSONEL,
    "Direkt Personel": DIRECT_PERSONEL,
    "Yapi Malzemesi": YAPI_MALZEME,
    "Demirbaslar": DEMIRBASLAR,
    "Sarf Malzemeler": SARF_MALZEMELER,
    "Makina": MAKINA,
}

selected_items = resource_map.get(resource_type, [])

# -- ONCEKI GUN VERILERINI GETIR --
prev_day_data = {}
for item in selected_items:
    prev_val = get_previous_day_value(project_id, report_date, resource_type, item) if not is_sunday else 0
    if prev_val > 0:
        prev_day_data[item] = int(prev_val)

# -- SESSION STATE: KAYNAK SATIRLARI --
if "resource_rows" not in st.session_state or st.session_state.get("resource_type") != resource_type:
    st.session_state.resource_type = resource_type
    if prev_day_data:
        rows = []
        for k, v in prev_day_data.items():
            unit_options = RESOURCE_UNIT_OPTIONS.get(resource_type, ["-"])
            rows.append({
                "Kaynak": k, 
                "Adet": v, 
                "Birim": unit_options[0] if unit_options else "",
                "Is Turu": "",
                "WBS Kodu": "",
                "Birim Fiyat": 0.0,
                "Toplam Maliyet": 0.0,
                "Notlar": ""
            })
    else:
        unit_options = RESOURCE_UNIT_OPTIONS.get(resource_type, ["-"])
        rows = [{
            "Kaynak": "", 
            "Adet": 0, 
            "Birim": unit_options[0] if unit_options else "",
            "Is Turu": "",
            "WBS Kodu": "",
            "Birim Fiyat": 0.0,
            "Toplam Maliyet": 0.0,
            "Notlar": ""
        }]
    st.session_state.resource_rows = rows

# -- Kaynak tipi icin ozel etiketler --
type_labels = {
    "Endirekt Personel": "Personel",
    "Direkt Personel": "Personel",
    "Yapi Malzemesi": "Malzeme",
    "Demirbaslar": "Demirbas",
    "Sarf Malzemeler": "Sarf Malzeme",
    "Makina": "Makina"
}

label = type_labels.get(resource_type, "Kaynak")

# -- DROPDOWN + YENI EKLEME --
col_search, col_button = st.columns([4, 1])

with col_search:
    options = sorted(selected_items) + [f"Yeni {label} Ekle..."]
    
    selected_option = st.selectbox(
        f"{label} Ara / Sec",
        options=options,
        key=f"select_{resource_type}",
        label_visibility="collapsed",
        placeholder=f"{label} adi yazin veya listeden secin..."
    )
    
    if selected_option == f"Yeni {label} Ekle...":
        new_item = st.text_input(
            f"Yeni {label} Adi",
            placeholder=f"Orn: Yeni {label}",
            key=f"new_{resource_type}_input",
            label_visibility="collapsed"
        )
    else:
        new_item = None

with col_button:
    st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
    
    if st.button("Ekle", key=f"add_{resource_type}", use_container_width=True):
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
                    unit_options = RESOURCE_UNIT_OPTIONS.get(resource_type, ["-"])
                    st.session_state.resource_rows.append({
                        "Kaynak": item_name,
                        "Adet": 1,
                        "Birim": unit_options[0] if unit_options else "",
                        "Is Turu": "",
                        "WBS Kodu": "",
                        "Birim Fiyat": 0.0,
                        "Toplam Maliyet": 0.0,
                        "Notlar": ""
                    })
            st.rerun()
        
        elif selected_option and selected_option != f"Yeni {label} Ekle...":
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
                    unit_options = RESOURCE_UNIT_OPTIONS.get(resource_type, ["-"])
                    st.session_state.resource_rows.append({
                        "Kaynak": item_name,
                        "Adet": 1,
                        "Birim": unit_options[0] if unit_options else "",
                        "Is Turu": "",
                        "WBS Kodu": "",
                        "Birim Fiyat": 0.0,
                        "Toplam Maliyet": 0.0,
                        "Notlar": ""
                    })
            st.rerun()

# -- DATA EDITOR (GÜNCELLENMİŞ) --
custom_key = f"custom_{resource_type}"
custom_items = st.session_state.get(custom_key, [])
display_items = sorted(set(selected_items + custom_items))

# Birim seçenekleri
unit_options = RESOURCE_UNIT_OPTIONS.get(resource_type, ["-"])

# WBS kodları ve iş türleri için optionlar
wbs_options = WBS_KODLARI
is_turu_options = [""] + IS_TURLERI

# DataFrame oluştur ve maliyet hesapla
df_resources = pd.DataFrame(st.session_state.resource_rows)

# Toplam maliyet hesapla
if not df_resources.empty:
    df_resources["Toplam Maliyet"] = df_resources["Adet"].fillna(0) * df_resources["Birim Fiyat"].fillna(0)

edited_resources_df = st.data_editor(
    df_resources,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Kaynak": st.column_config.SelectboxColumn(
            "Kaynak / Malzeme",
            options=display_items,
            required=True
        ),
        "Adet": st.column_config.NumberColumn("Adet / Miktar", min_value=0, step=1, format="%d"),
        "Birim": st.column_config.SelectboxColumn(
            "Birim",
            options=unit_options,
            required=True
        ),
        "Is Turu": st.column_config.SelectboxColumn(
            "Is Turu",
            options=is_turu_options,
            required=False
        ),
        "WBS Kodu": st.column_config.SelectboxColumn(
            "WBS Kodu",
            options=wbs_options,
            required=False
        ),
        "Birim Fiyat": st.column_config.NumberColumn(
            "Birim Fiyat (AED)",
            min_value=0.0,
            step=0.01,
            format="%.2f"
        ),
        "Toplam Maliyet": st.column_config.NumberColumn(
            "Toplam Maliyet (AED)",
            min_value=0.0,
            step=0.01,
            format="%.2f",
            disabled=True
        ),
        "Notlar": st.column_config.TextColumn("Notlar / Aciklama")
    },
    key=f"res_grid_{resource_type}_{report_date}"
)

# Toplam maliyeti güncelle
if not edited_resources_df.empty:
    edited_resources_df["Toplam Maliyet"] = edited_resources_df["Adet"].fillna(0) * edited_resources_df["Birim Fiyat"].fillna(0)

# Session state'i güncelle
st.session_state.resource_rows = edited_resources_df.to_dict(orient="records")

# Kaynak özeti
if not edited_resources_df.empty:
    total_cost = edited_resources_df["Toplam Maliyet"].sum()
    total_units = edited_resources_df["Adet"].sum()
    st.markdown(f"""
    <div style="
        background-color: #141414; 
        padding: 0.8rem 1rem; 
        border-radius: 6px; 
        border: 1px solid #262626;
        margin-top: 0.5rem;
        display: flex;
        gap: 2rem;
    ">
        <span style="color: #a3a3a3;">Toplam Miktar: <strong style="color: #ffffff;">{total_units:,.0f}</strong></span>
        <span style="color: #a3a3a3;">Toplam Maliyet: <strong style="color: #3b82f6;">{total_cost:,.2f} AED</strong></span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='border-color: #262626; margin: 1.5rem 0;'>", unsafe_allow_html=True)

# ==========================================
# 3. IS ILERLEME
# ==========================================
st.subheader("2. Is Ilerleme")

with st.spinner("Veriler yukleniyor..."):
    existing_rows, _ = get_work_progress_by_date(project_id, report_date)
    time.sleep(0.3)

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
        "bolge": st.column_config.TextColumn("Bolge"),
        "blok": st.column_config.TextColumn("Blok"),
        "mahal": st.column_config.TextColumn("Mahal"),
        "aks_x": st.column_config.TextColumn("Aks-X"),
        "aks_y": st.column_config.TextColumn("Aks-Y"),
        "kot": st.column_config.TextColumn("Kot"),
        "is_turu": st.column_config.SelectboxColumn("Is Turu", options=IS_TURLERI, required=True),
        "yapilan_is": st.column_config.TextColumn("Yapilan Is"),
        "alt_yuklenici": st.column_config.TextColumn("Alt Yuklenici"),
        "birim": st.column_config.SelectboxColumn(
            "Birim",
            options=WORK_UNIT_OPTIONS,
            required=True
        ),
        "ilerleme_yuzdesi": st.column_config.NumberColumn("% Ilerleme", min_value=0.0, max_value=100.0, step=0.5, format="%.1f%%"),
        "kesif_miktari": st.column_config.NumberColumn("Kesif", min_value=0.0, step=1.0),
        "yapilan_miktar": st.column_config.NumberColumn("Yapilan", disabled=True, format="%.1f"),
        "wbs_kodu": st.column_config.TextColumn("WBS"),
        "butce_kodu": st.column_config.TextColumn("Butce")
    },
    key="work_grid"
)

# Yapilan miktar otomatik hesaplanir
if not edited_work_df.empty:
    edited_work_df["yapilan_miktar"] = (edited_work_df["kesif_miktari"].fillna(0) * edited_work_df["ilerleme_yuzdesi"].fillna(0)) / 100.0

st.session_state.work_df = edited_work_df

st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

# ==========================================
# 4. "DİĞER" HARCAMALAR
# ==========================================
st.subheader("3. Diger Harcamalar")

with st.expander("Diger Harcama Ekle", expanded=False):
    with st.form("other_expense_form"):
        col1, col2 = st.columns(2)
        with col1:
            harcama_turu = st.selectbox("Harcama Turu", HARCAMA_TURLERI)
            tarih = st.date_input("Harcama Tarihi", report_date)
            tutar = st.number_input("Tutar (AED)", min_value=0.0, step=1.0, format="%.2f")
        with col2:
            wbs_kodu = st.selectbox("Ilgili WBS Kodu", [""] + WBS_KODLARI)
            aciklama = st.text_area("Aciklama", placeholder="Harcama detayi...")
        
        submit_expense = st.form_submit_button("Harcamayi Ekle", type="primary")
        
        if submit_expense:
            if aciklama and tutar > 0:
                expense_data = {
                    "project_id": project_id,
                    "tarih": str(tarih),
                    "harcama_turu": harcama_turu,
                    "aciklama": aciklama,
                    "tutar": tutar,
                    "wbs_kodu": wbs_kodu
                }
                with st.spinner("Harcama kaydediliyor..."):
                    ok, err = save_other_expense(expense_data)
                    time.sleep(0.3)
                if ok:
                    st.success("Harcama kaydedildi!")
                    st.rerun()
                else:
                    st.error(f"Harcama kaydedilemedi: {err}")
            else:
                st.warning("Lutfen aciklama ve tutar girin.")

# Geçmiş harcamaları göster
with st.spinner("Harcamalar yukleniyor..."):
    expenses, _ = get_other_expenses(project_id, report_date)
    time.sleep(0.3)

if expenses:
    st.markdown("#### Bugunun Harcamalari")
    df_expenses = pd.DataFrame(expenses)
    df_display = df_expenses[["harcama_turu", "aciklama", "tutar", "wbs_kodu"]]
    df_display.columns = ["Harcama Turu", "Aciklama", "Tutar (AED)", "WBS Kodu"]
    st.dataframe(df_display, use_container_width=True)
    
    total_expense = df_expenses["tutar"].sum()
    st.markdown(f"""
    <div style="
        background-color: #141414; 
        padding: 0.8rem 1rem; 
        border-radius: 6px; 
        border: 1px solid #262626;
        margin-top: 0.5rem;
    ">
        <span style="color: #a3a3a3;">Toplam Diger Harcama: <strong style="color: #3b82f6;">{total_expense:,.2f} AED</strong></span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='border-color: #262626; margin: 1.5rem 0;'>", unsafe_allow_html=True)

# ==========================================
# 5. TUM VERILERI KAYDET - DÜZELTİLDİ
# ==========================================

# Kaydetme butonu
col_save1, col_save2, col_save3 = st.columns([2, 1, 1])
with col_save1:
    if st.button("Tum Verileri Kaydet (Ctrl+S)", type="primary", use_container_width=True):
        # 1. Kaynak verilerini hazırla
        resource_payload = {}
        if not edited_resources_df.empty:
            for _, row in edited_resources_df.iterrows():
                if row["Kaynak"] and row["Adet"] > 0:
                    resource_key = row["Kaynak"]
                    resource_data = {
                        "miktar": int(row["Adet"]),
                        "birim": row.get("Birim", ""),
                        "is_turu": row.get("Is Turu", ""),
                        "wbs_kodu": row.get("WBS Kodu", ""),
                        "birim_fiyat": float(row.get("Birim Fiyat", 0)),
                        "toplam_maliyet": float(row.get("Toplam Maliyet", 0)),
                        "notlar": row.get("Notlar", "")
                    }
                    resource_payload[resource_key] = resource_data
        
        success = True
        
        # 2. Kaynak verilerini kaydet
        if resource_payload:
            with st.spinner("Kaynak verileri kaydediliyor..."):
                ok, err = save_daily_resources(project_id, report_date, resource_type, resource_payload)
                time.sleep(0.3)
            if not ok:
                st.error(f"Kaynak verisi kaydedilemedi: {err}")
                success = False
            else:
                st.success("Kaynak verileri kaydedildi!")
        else:
            st.info("Kaynak verisi girilmedi.")
        
        # 3. İş ilerleme verilerini kaydet
        if success:
            rows_to_save = edited_work_df.to_dict(orient="records") if not edited_work_df.empty else []
            clean_rows = []
            
            for r in rows_to_save:
                if not str(r.get("yapilan_is", "")).strip():
                    continue
                
                for key in ["kesif_miktari", "yapilan_miktar", "ilerleme_yuzdesi"]:
                    val = r.get(key, 0)
                    if pd.isna(val) or np.isinf(val):
                        r[key] = 0.0
                    else:
                        r[key] = float(val) if val is not None else 0.0
                
                r["bolge"] = str(r.get("bolge", "")) if r.get("bolge") else ""
                r["blok"] = str(r.get("blok", "")) if r.get("blok") else ""
                r["mahal"] = str(r.get("mahal", "")) if r.get("mahal") else ""
                r["aks_x"] = str(r.get("aks_x", "")) if r.get("aks_x") else ""
                r["aks_y"] = str(r.get("aks_y", "")) if r.get("aks_y") else ""
                r["kot"] = str(r.get("kot", "")) if r.get("kot") else ""
                r["is_turu"] = str(r.get("is_turu", "")) if r.get("is_turu") else ""
                r["yapilan_is"] = str(r.get("yapilan_is", "")) if r.get("yapilan_is") else ""
                r["alt_yuklenici"] = str(r.get("alt_yuklenici", "")) if r.get("alt_yuklenici") else ""
                r["birim"] = str(r.get("birim", "")) if r.get("birim") else ""
                r["wbs_kodu"] = str(r.get("wbs_kodu", "")) if r.get("wbs_kodu") else ""
                r["butce_kodu"] = str(r.get("butce_kodu", "")) if r.get("butce_kodu") else ""
                
                clean_rows.append(r)
            
            if clean_rows:
                with st.spinner("Is ilerleme verileri kaydediliyor..."):
                    ok_w, err_w = save_work_progress(project_id, report_date, clean_rows)
                    time.sleep(0.3)
                if not ok_w:
                    st.error(f"Is ilerleme verisi kaydedilemedi: {err_w}")
                else:
                    st.success("Is ilerleme verileri kaydedildi!")
            else:
                st.info("Is ilerleme verisi girilmedi.")

st.markdown('</div>', unsafe_allow_html=True)