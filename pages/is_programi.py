# -*- coding: utf-8 -*-
"""
Created on Thu Aug 20 05:42:55 2026
@author: taric
Updated: 2026-08-24 - Veri tipi düzeltmeleri, otomatik tarih hesaplama, predecessor validasyonu
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import time
import numpy as np
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
    page_title="SARCON Portal | Is Programi",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

apply_global_styles(is_login=False)
render_top_navbar()

st.markdown('<div class="page-content">', unsafe_allow_html=True)

# ==========================================
# BASLIK
# ==========================================
st.markdown("""
<div style="border-left: 3px solid #3b82f6; padding-left: 0.8rem; margin-bottom: 1.5rem;">
    <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.3rem;">Is Programi (Gantt Semasi)</h3>
    <p style="color: #737373; margin: 0; font-size: 0.8rem;">
        Aktivite girisi, otomatik tarih hesaplama, baglantilar, kaynak atama ve milestone yönetimi
    </p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# PROJE SECIMI
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
# MEVCUT VERILERI CEK
# ==========================================
@st.cache_data(ttl=300)
def get_schedule(project_id):
    try:
        response = supabase.table("project_schedule").select("*").eq("project_id", project_id).execute()
        return response.data if response.data else []
    except:
        return []

with loading_spinner("Veriler yukleniyor..."):
    existing_data = get_schedule(project_id)
    time.sleep(0.3)

# ==========================================
# SESSION STATE - TABLO YAPISI
# ==========================================
if "schedule_df" not in st.session_state or st.session_state.get("current_project") != project_id:
    st.session_state.current_project = project_id
    if existing_data:
        # Veri tiplerini dönüştür
        df = pd.DataFrame(existing_data)
        
        # activity_code'u string'e çevir
        if "activity_code" in df.columns:
            df["activity_code"] = df["activity_code"].astype(str)
        if "predecessor" in df.columns:
            df["predecessor"] = df["predecessor"].astype(str)
        if "parent_code" in df.columns:
            df["parent_code"] = df["parent_code"].astype(str)
            
        # Tarihleri datetime'a çevir
        for col in ["start_date", "end_date", "milestone_date"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
        
        st.session_state.schedule_df = df
    else:
        st.session_state.schedule_df = pd.DataFrame(columns=[
            "activity_code",      # Aktivite Kodu
            "activity_name",      # Aktivite Adi
            "parent_code",        # Ust Aktivite Kodu (hiyerarsi icin)
            "level",              # Seviye (0=Ana, 1=Alt, 2=Alt-Alt)
            "start_date",         # Baslangic
            "end_date",           # Bitis (otomatik hesaplanacak)
            "duration",           # Sure (gun)
            "predecessor",        # Onceki Aktivite Kodu
            "link_type",          # Baglanti Tipi (FS, SS, FF)
            "link_lag",           # Baglanti Gecikmesi (gun)
            "progress_pct",       # Ilerleme %
            "responsible",        # Sorumlu
            "resource_type",      # Kaynak Turu
            "resource_name",      # Kaynak Adi
            "resource_quantity",  # Kaynak Miktari
            "is_milestone",       # Milestone mu?
            "milestone_date",     # Milestone Tarihi
            "notes"               # Notlar
        ])

# ==========================================
# OTOMATIK TARIH HESAPLAMA FONKSIYONLARI
# ==========================================
def calculate_end_date(start_date, duration):
    """Start date ve duration'dan end date hesapla"""
    if pd.isna(start_date) or pd.isna(duration):
        return None
    if isinstance(start_date, str):
        try:
            start_date = pd.to_datetime(start_date)
        except:
            return None
    return start_date + timedelta(days=int(duration))

def calculate_dates_with_predecessors(df):
    """Predecessor ve duration bilgilerine göre tüm tarihleri otomatik hesapla"""
    if df.empty:
        return df
    
    df = df.copy()
    
    # Önce mevcut start_date'leri koru
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["end_date"] = pd.to_datetime(df["end_date"])
    
    # Predecessor'u olan ve olmayan aktiviteleri ayır
    df_with_pred = df[df["predecessor"].notna() & (df["predecessor"] != "") & (df["predecessor"] != "nan")]
    df_no_pred = df[df["predecessor"].isna() | (df["predecessor"] == "") | (df["predecessor"] == "nan")]
    
    # Predecessor'u olmayan aktiviteler için sadece duration'u kullan
    for idx in df_no_pred.index:
        if pd.notna(df.loc[idx, "start_date"]) and pd.notna(df.loc[idx, "duration"]):
            df.loc[idx, "end_date"] = calculate_end_date(df.loc[idx, "start_date"], df.loc[idx, "duration"])
    
    # Predecessor'u olan aktiviteler için otomatik hesaplama
    # Bunun için basit bir scheduler mantığı - önce tüm aktiviteleri sırala
    processed = []
    max_iterations = len(df) * 2  # Döngü koruması
    
    for _ in range(max_iterations):
        for idx in df_with_pred.index:
            if idx in processed:
                continue
                
            pred_code = df.loc[idx, "predecessor"]
            if pd.isna(pred_code) or pred_code == "":
                continue
                
            # Predecessor aktivitesini bul
            pred_row = df[df["activity_code"] == pred_code]
            if pred_row.empty:
                continue
                
            pred_idx = pred_row.index[0]
            
            # Predecessor'un end_date'i hesaplanmış mı?
            if pd.isna(df.loc[pred_idx, "end_date"]) and pd.isna(df.loc[pred_idx, "start_date"]):
                # Predecessor'un tarihleri henüz hesaplanmamış, sıra bekle
                continue
            
            # Predecessor'un end_date'ini kullan
            if pd.notna(df.loc[pred_idx, "end_date"]):
                pred_end = df.loc[pred_idx, "end_date"]
            else:
                # Eğer end_date yoksa start_date + duration kullan
                if pd.notna(df.loc[pred_idx, "start_date"]) and pd.notna(df.loc[pred_idx, "duration"]):
                    pred_end = calculate_end_date(df.loc[pred_idx, "start_date"], df.loc[pred_idx, "duration"])
                else:
                    continue
            
            # Link tipine göre hesaplama
            link_type = df.loc[idx, "link_type"] if pd.notna(df.loc[idx, "link_type"]) else "FS"
            link_lag = float(df.loc[idx, "link_lag"]) if pd.notna(df.loc[idx, "link_lag"]) else 0
            
            if link_type == "FS":  # Finish to Start
                df.loc[idx, "start_date"] = pred_end + timedelta(days=int(link_lag))
            elif link_type == "SS":  # Start to Start
                df.loc[idx, "start_date"] = df.loc[pred_idx, "start_date"] + timedelta(days=int(link_lag))
            elif link_type == "FF":  # Finish to Finish
                df.loc[idx, "start_date"] = pred_end - timedelta(days=int(df.loc[idx, "duration"])) + timedelta(days=int(link_lag))
                if pd.isna(df.loc[idx, "duration"]):
                    df.loc[idx, "duration"] = 1
            
            # End_date'i hesapla
            if pd.notna(df.loc[idx, "start_date"]) and pd.notna(df.loc[idx, "duration"]):
                df.loc[idx, "end_date"] = calculate_end_date(df.loc[idx, "start_date"], df.loc[idx, "duration"])
            
            processed.append(idx)
    
    return df

# ==========================================
# DATA EDITOR - EXCEL-LIKE GIRIS
# ==========================================
st.markdown("### Aktivite Girdileri")

# Mevcut dataframe'i hazırla
current_df = st.session_state.schedule_df.copy()

# Veri tiplerini düzenle
for col in current_df.columns:
    if col in ["activity_code", "predecessor", "parent_code"]:
        current_df[col] = current_df[col].astype(str)
    if col in ["level", "duration", "link_lag", "progress_pct", "resource_quantity"]:
        current_df[col] = pd.to_numeric(current_df[col], errors='coerce')

edited_schedule_df = st.data_editor(
    current_df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "activity_code": st.column_config.TextColumn("Kod", required=False, width="small"),
        "activity_name": st.column_config.TextColumn("Aktivite Adi", required=True, width="large"),
        "parent_code": st.column_config.TextColumn("Ust Kod", width="small"),
        "level": st.column_config.NumberColumn("Seviye", min_value=0, max_value=2, step=1, width="small"),
        "start_date": st.column_config.DateColumn("Baslangic", width="medium"),
        "end_date": st.column_config.DateColumn("Bitis (Otomatik)", width="medium", disabled=True),
        "duration": st.column_config.NumberColumn("Sure (gun)", min_value=0, step=1, width="small"),
        "predecessor": st.column_config.TextColumn("Onceki Aktivite", width="small"),
        "link_type": st.column_config.SelectboxColumn(
            "Baglanti Tipi",
            options=["FS", "SS", "FF"],
            width="small"
        ),
        "link_lag": st.column_config.NumberColumn("Gecikme (gun)", min_value=0, step=1, width="small"),
        "progress_pct": st.column_config.NumberColumn("Ilerleme %", min_value=0.0, max_value=100.0, step=0.5, format="%.1f%%", width="medium"),
        "responsible": st.column_config.TextColumn("Sorumlu", width="medium"),
        "resource_type": st.column_config.SelectboxColumn(
            "Kaynak Turu",
            options=["Endirekt Personel", "Direkt Personel", "Makina", "Yapi Malzemesi", "Demirbaslar", "Sarf Malzemeler"],
            width="medium"
        ),
        "resource_name": st.column_config.TextColumn("Kaynak Adi", width="medium"),
        "resource_quantity": st.column_config.NumberColumn("Kaynak Miktari", min_value=0.0, step=0.1, width="small"),
        "is_milestone": st.column_config.CheckboxColumn("Milestone", width="small"),
        "milestone_date": st.column_config.DateColumn("Milestone Tarihi", width="medium"),
        "notes": st.column_config.TextColumn("Notlar", width="medium")
    },
    key="schedule_grid"
)

# Aktivite kodlarını güncelle (boş olanları doldur)
if not edited_schedule_df.empty:
    # Boş activity_code'ları doldur
    idx = 1
    for i in range(len(edited_schedule_df)):
        if pd.isna(edited_schedule_df.iloc[i]["activity_code"]) or str(edited_schedule_df.iloc[i]["activity_code"]) == "" or str(edited_schedule_df.iloc[i]["activity_code"]) == "nan":
            edited_schedule_df.at[edited_schedule_df.index[i], "activity_code"] = f"ACT{idx:03d}"
            idx += 1
        elif str(edited_schedule_df.iloc[i]["activity_code"]) == "nan":
            edited_schedule_df.at[edited_schedule_df.index[i], "activity_code"] = f"ACT{idx:03d}"
            idx += 1

# ==========================================
# OTOMATIK TARIH HESAPLAMA
# ==========================================
if not edited_schedule_df.empty:
    # End_date'leri otomatik hesapla
    df_for_calc = edited_schedule_df.copy()
    
    # Tarihleri datetime'a çevir
    if "start_date" in df_for_calc.columns:
        df_for_calc["start_date"] = pd.to_datetime(df_for_calc["start_date"])
    if "end_date" in df_for_calc.columns:
        df_for_calc["end_date"] = pd.to_datetime(df_for_calc["end_date"])
    
    # Duration'u sayısal yap
    if "duration" in df_for_calc.columns:
        df_for_calc["duration"] = pd.to_numeric(df_for_calc["duration"], errors='coerce')
    
    # Önce mevcut end_date'leri hesapla (eğer başlangıç varsa)
    for idx in df_for_calc.index:
        if pd.notna(df_for_calc.loc[idx, "start_date"]) and pd.notna(df_for_calc.loc[idx, "duration"]):
            df_for_calc.loc[idx, "end_date"] = calculate_end_date(
                df_for_calc.loc[idx, "start_date"], 
                df_for_calc.loc[idx, "duration"]
            )
    
    # Predecessor'ları kullanarak tarihleri güncelle
    df_for_calc = calculate_dates_with_predecessors(df_for_calc)
    
    # Güncellenen verileri ana dataframe'e aktar
    for col in ["start_date", "end_date"]:
        if col in df_for_calc.columns:
            edited_schedule_df[col] = df_for_calc[col]

# Session state'i güncelle
st.session_state.schedule_df = edited_schedule_df

# ==========================================
# HIYERARSIK GOSTERIM - BULUNAN VERILERI OZETLE
# ==========================================
if not edited_schedule_df.empty:
    st.markdown("---")
    
    df_filtered = edited_schedule_df[edited_schedule_df["activity_name"].notna()]
    
    if not df_filtered.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        total_activities = len(df_filtered)
        main_count = len(df_filtered[df_filtered["level"] == 0]) if "level" in df_filtered.columns else 0
        sub_count = len(df_filtered[df_filtered["level"] == 1]) if "level" in df_filtered.columns else 0
        milestone_count = df_filtered["is_milestone"].sum() if "is_milestone" in df_filtered.columns else 0
        
        with col1:
            st.markdown(f"""
            <div class="animate-card" style="
                background-color: #141414;
                padding: 0.8rem;
                border-radius: 12px;
                border: 1px solid #262626;
                text-align: center;
            ">
                <p style="color: #737373; font-size: 0.6rem; margin: 0;">Toplam Aktivite</p>
                <h4 style="color: #ffffff; margin: 0.2rem 0;">{total_activities}</h4>
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
                <p style="color: #737373; font-size: 0.6rem; margin: 0;">Ana Is</p>
                <h4 style="color: #3b82f6; margin: 0.2rem 0;">{main_count}</h4>
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
                <p style="color: #737373; font-size: 0.6rem; margin: 0;">Alt Is</p>
                <h4 style="color: #60a5fa; margin: 0.2rem 0;">{sub_count}</h4>
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
                <p style="color: #737373; font-size: 0.6rem; margin: 0;">Milestone</p>
                <h4 style="color: #f59e0b; margin: 0.2rem 0;">{milestone_count}</h4>
            </div>
            """, unsafe_allow_html=True)

# ==========================================
# GANTT SEMASI
# ==========================================
if not edited_schedule_df.empty:
    st.markdown("---")
    st.markdown("### Gantt Semasi")
    
    df = edited_schedule_df.copy()
    df = df[df["activity_name"].notna()]
    
    if not df.empty and "start_date" in df.columns and "end_date" in df.columns:
        df["start_date"] = pd.to_datetime(df["start_date"])
        df["end_date"] = pd.to_datetime(df["end_date"])
        
        # Duration hesapla (eğer boşsa)
        df["duration"] = df.apply(
            lambda row: (row["end_date"] - row["start_date"]).days if pd.notna(row["start_date"]) and pd.notna(row["end_date"]) else row.get("duration", 0),
            axis=1
        )
        
        # Sadece başlangıç ve bitiş tarihi olan aktiviteleri göster
        df_valid = df[df["start_date"].notna() & df["end_date"].notna()]
        
        if not df_valid.empty:
            # Renk skalası: seviyeye göre
            color_map = {0: "#3b82f6", 1: "#60a5fa", 2: "#93c5fd"}
            df_valid["color"] = df_valid["level"].map(color_map).fillna("#3b82f6")
            
            # Milestone'ları ayrı göster
            milestone_df = df_valid[df_valid["is_milestone"] == True]
            non_milestone_df = df_valid[df_valid["is_milestone"] != True]
            
            # Aktivite adlarını temizle
            non_milestone_df["activity_name"] = non_milestone_df["activity_name"].fillna("")
            
            if not non_milestone_df.empty:
                fig = px.timeline(
                    non_milestone_df,
                    x_start="start_date",
                    x_end="end_date",
                    y="activity_name",
                    color="level",
                    title="Proje Gantt Semasi",
                    labels={
                        "activity_name": "Aktivite",
                        "level": "Seviye",
                        "progress_pct": "Ilerleme %"
                    },
                    color_continuous_scale=["#3b82f6", "#60a5fa", "#93c5fd"]
                )
                
                # Milestone'ları ekle (nokta olarak)
                if not milestone_df.empty:
                    fig.add_scatter(
                        x=milestone_df["start_date"],
                        y=milestone_df["activity_name"],
                        mode="markers",
                        marker=dict(symbol="diamond", size=15, color="#f59e0b"),
                        name="Milestone"
                    )
                
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    height=max(400, len(df_valid) * 40),
                    showlegend=True,
                    xaxis=dict(title="Tarih", tickfont=dict(color="white")),
                    yaxis=dict(title="Aktivite", tickfont=dict(color="white")),
                    legend=dict(font=dict(color="white"))
                )
                
                fig = animate_plotly(fig)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Gantt şeması oluşturulacak geçerli aktivite bulunamadı.")

# ==========================================
# CSV IMPORT / EXPORT
# ==========================================
st.markdown("---")
st.markdown("### Import / Export")

col_imp, col_exp = st.columns(2)

with col_imp:
    st.markdown("#### CSV'den Ice Aktar")
    uploaded_file = st.file_uploader("CSV dosyasi secin", type=["csv"], key="schedule_import")
    
    if uploaded_file is not None:
        try:
            imported_df = pd.read_csv(uploaded_file)
            
            # Beklenen kolonlar
            expected_cols = [
                "activity_code", "activity_name", "parent_code", "level",
                "start_date", "duration", "predecessor",  # end_date yok, otomatik hesaplanacak
                "link_type", "link_lag", "progress_pct", "responsible",
                "resource_type", "resource_name", "resource_quantity",
                "is_milestone", "milestone_date", "notes"
            ]
            
            # Eksik kolonları ekle
            for col in expected_cols:
                if col not in imported_df.columns:
                    imported_df[col] = None
            
            # Veri tiplerini dönüştür
            if "activity_code" in imported_df.columns:
                imported_df["activity_code"] = imported_df["activity_code"].astype(str)
            if "predecessor" in imported_df.columns:
                imported_df["predecessor"] = imported_df["predecessor"].astype(str)
            if "parent_code" in imported_df.columns:
                imported_df["parent_code"] = imported_df["parent_code"].astype(str)
            
            # Tarihleri dönüştür
            if "start_date" in imported_df.columns:
                imported_df["start_date"] = pd.to_datetime(imported_df["start_date"])
            if "milestone_date" in imported_df.columns:
                imported_df["milestone_date"] = pd.to_datetime(imported_df["milestone_date"])
            
            # end_date'i otomatik hesapla
            if "duration" in imported_df.columns and "start_date" in imported_df.columns:
                imported_df["duration"] = pd.to_numeric(imported_df["duration"], errors='coerce')
                imported_df["end_date"] = imported_df.apply(
                    lambda row: calculate_end_date(row["start_date"], row["duration"]) 
                    if pd.notna(row["start_date"]) and pd.notna(row["duration"]) 
                    else None,
                    axis=1
                )
            
            # Predecessor kontrolü - sadece geçerli activity_code'lar ile sınırla
            if "predecessor" in imported_df.columns and "activity_code" in imported_df.columns:
                valid_codes = set(imported_df["activity_code"].dropna().astype(str))
                imported_df["predecessor"] = imported_df["predecessor"].apply(
                    lambda x: x if pd.isna(x) or str(x) in valid_codes else None
                )
            
            st.session_state.schedule_df = imported_df[expected_cols + ["end_date"]]
            toast_success("Basarili", f"{len(imported_df)} satir ice aktarildi!")
            st.rerun()
            
        except Exception as e:
            toast_error("Hata", f"CSV okuma hatasi: {e}")

with col_exp:
    st.markdown("#### CSV'ye Disa Aktar")
    
    if not edited_schedule_df.empty:
        # Export için start_date, duration ve end_date'i içer
        export_df = edited_schedule_df.copy()
        
        # Tarihleri string formatına çevir
        for col in ["start_date", "end_date", "milestone_date"]:
            if col in export_df.columns:
                export_df[col] = export_df[col].dt.strftime("%Y-%m-%d") if not export_df[col].empty else export_df[col]
        
        csv_data = export_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="CSV Indir",
            data=csv_data,
            file_name=f"is_programi_{selected_project}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        toast_info("Bilgi", "Dis aktarilacak veri yok.")

# ==========================================
# KAYDET
# ==========================================
st.markdown("---")

if st.button("Is Programini Kaydet", type="primary", use_container_width=True):
    rows_to_save = edited_schedule_df.to_dict(orient="records") if not edited_schedule_df.empty else []
    clean_rows = [r for r in rows_to_save if str(r.get("activity_name", "")).strip()]
    
    if clean_rows:
        try:
            with loading_spinner("Veriler kaydediliyor..."):
                # Tarihleri string'e çevir
                for r in clean_rows:
                    r["project_id"] = project_id
                    r.pop("id", None)
                    
                    if r.get("start_date") and hasattr(r["start_date"], "isoformat"):
                        r["start_date"] = r["start_date"].isoformat()
                    if r.get("end_date") and hasattr(r["end_date"], "isoformat"):
                        r["end_date"] = r["end_date"].isoformat()
                    if r.get("milestone_date") and hasattr(r["milestone_date"], "isoformat"):
                        r["milestone_date"] = r["milestone_date"].isoformat()
                    
                    # Null değerleri düzenle
                    for key in ["duration", "level", "link_lag", "progress_pct", "resource_quantity"]:
                        if pd.isna(r.get(key)):
                            r[key] = None
                    
                    # Milestone kontrolü
                    if r.get("is_milestone") is None:
                        r["is_milestone"] = False
                    
                    # Predecessor kontrolü - geçersiz kodları temizle
                    if r.get("predecessor") and pd.isna(r["predecessor"]):
                        r["predecessor"] = None
                    elif r.get("predecessor") == "nan":
                        r["predecessor"] = None
                
                # Eski verileri sil
                supabase.table("project_schedule").delete().eq("project_id", project_id).execute()
                
                # Yeni verileri ekle
                for r in clean_rows:
                    supabase.table("project_schedule").insert(r).execute()
                
                time.sleep(0.3)
            toast_success("Basarili", f"{len(clean_rows)} aktivite kaydedildi!")
            st.cache_data.clear()
            st.rerun()
            
        except Exception as e:
            toast_error("Hata", f"Kayit hatasi: {e}")
    else:
        toast_warning("Uyari", "Kaydedilecek veri bulunamadi.")
        
st.markdown('</div>', unsafe_allow_html=True)