# -*- coding: utf-8 -*-
"""
Created on Thu Aug 20 05:13:10 2026
@author: taric
Updated: 2026-08-24 - Kalite Kontrol modülü olarak yeniden yapılandırıldı
NCR, Checklist, Uygunsuzluk Yönetimi, QA, MAR kontrolü eklendi
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime
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
    page_title="SARCON Portal | Kalite Kontrol",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

apply_global_styles(is_login=False)
render_top_navbar()

st.markdown('<div class="page-content">', unsafe_allow_html=True)

st.markdown("""
<div style="border-left: 3px solid #3b82f6; padding-left: 0.8rem; margin-bottom: 1.5rem;">
    <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.3rem;">Kalite Kontrol Yönetimi</h3>
    <p style="color: #737373; margin: 0; font-size: 0.8rem;">
        NCR, Checklist, Uygunsuzluk Yönetimi, Quality Assurance ve MAR kontrolü
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
# SEKMELER
# ==========================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 NCR", 
    "✅ Checklist", 
    "⚠️ Uygunsuzluk", 
    "🔍 Kalite Güvencesi",
    "📦 MAR Kontrolü"
])

# ==========================================
# TAB 1: NCR (Non-Conformance Report)
# ==========================================
with tab1:
    st.markdown("### Uygun Olmayan Durum Raporu (NCR)")
    st.caption("Projedeki uygun olmayan durumları, sapmaları ve kusurları takip edin")
    
    @st.cache_data(ttl=300)
    def get_ncr_data(project_id):
        try:
            response = supabase.table("project_ncr").select("*").eq("project_id", project_id).execute()
            return response.data if response.data else []
        except:
            return []
    
    with loading_spinner("NCR verileri yükleniyor..."):
        existing_ncr = get_ncr_data(project_id)
        time.sleep(0.3)
    
    if "ncr_df" not in st.session_state or st.session_state.get("ncr_project") != project_id:
        st.session_state.ncr_project = project_id
        if existing_ncr:
            st.session_state.ncr_df = pd.DataFrame(existing_ncr)
        else:
            st.session_state.ncr_df = pd.DataFrame(columns=[
                "ncr_no", "title", "description", "category", "priority",
                "status", "assigned_to", "detected_date", "target_date",
                "closure_date", "root_cause", "corrective_action", "notes"
            ])
    
    ncr_df = st.data_editor(
        st.session_state.ncr_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "ncr_no": st.column_config.TextColumn("NCR No", required=True),
            "title": st.column_config.TextColumn("Başlık", required=True),
            "description": st.column_config.TextColumn("Açıklama"),
            "category": st.column_config.SelectboxColumn(
                "Kategori",
                options=["Malzeme", "İşçilik", "Proses", "Dokümantasyon", "Tasarım", "Diğer"]
            ),
            "priority": st.column_config.SelectboxColumn(
                "Öncelik",
                options=["Düşük", "Orta", "Yüksek", "Kritik"]
            ),
            "status": st.column_config.SelectboxColumn(
                "Durum",
                options=["Açık", "İncelemede", "Düzeltmede", "Kapalı", "Reddedildi"]
            ),
            "assigned_to": st.column_config.TextColumn("Sorumlu"),
            "detected_date": st.column_config.DateColumn("Tespit Tarihi"),
            "target_date": st.column_config.DateColumn("Hedef Tarih"),
            "closure_date": st.column_config.DateColumn("Kapanış Tarihi"),
            "root_cause": st.column_config.TextColumn("Kök Neden"),
            "corrective_action": st.column_config.TextColumn("Düzeltici Faaliyet"),
            "notes": st.column_config.TextColumn("Notlar")
        },
        key="ncr_grid"
    )
    
    st.session_state.ncr_df = ncr_df
    
    # NCR Özet
    if not ncr_df.empty:
        st.markdown("#### NCR Özeti")
        col1, col2, col3, col4 = st.columns(4)
        
        total_ncr = len(ncr_df)
        open_ncr = len(ncr_df[ncr_df["status"] == "Açık"])
        in_progress_ncr = len(ncr_df[ncr_df["status"].isin(["İncelemede", "Düzeltmede"])])
        closed_ncr = len(ncr_df[ncr_df["status"] == "Kapalı"])
        
        with col1:
            st.metric("Toplam NCR", total_ncr)
        with col2:
            st.metric("Açık NCR", open_ncr, delta_color="off")
        with col3:
            st.metric("Devam Eden", in_progress_ncr)
        with col4:
            st.metric("Kapanan", closed_ncr)

# ==========================================
# TAB 2: CHECKLIST
# ==========================================
with tab2:
    st.markdown("### Kalite Kontrol Checklist")
    st.caption("İş kalemleri için yapılacak kontrolleri ve kabul kriterlerini tanımlayın")
    
    @st.cache_data(ttl=300)
    def get_checklist_data(project_id):
        try:
            response = supabase.table("project_checklist").select("*").eq("project_id", project_id).execute()
            return response.data if response.data else []
        except:
            return []
    
    with loading_spinner("Checklist verileri yükleniyor..."):
        existing_checklist = get_checklist_data(project_id)
        time.sleep(0.3)
    
    if "checklist_df" not in st.session_state or st.session_state.get("checklist_project") != project_id:
        st.session_state.checklist_project = project_id
        if existing_checklist:
            st.session_state.checklist_df = pd.DataFrame(existing_checklist)
        else:
            st.session_state.checklist_df = pd.DataFrame(columns=[
                "checklist_no", "work_item", "control_item", "acceptance_criteria",
                "method", "frequency", "responsible", "status", "notes"
            ])
    
    checklist_df = st.data_editor(
        st.session_state.checklist_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "checklist_no": st.column_config.TextColumn("Kontrol No", required=True),
            "work_item": st.column_config.TextColumn("İş Kalemi", required=True),
            "control_item": st.column_config.TextColumn("Kontrol Konusu", required=True),
            "acceptance_criteria": st.column_config.TextColumn("Kabul Kriteri"),
            "method": st.column_config.SelectboxColumn(
                "Kontrol Yöntemi",
                options=["Görsel", "Ölçüm", "Test", "Belge", "Onay"]
            ),
            "frequency": st.column_config.SelectboxColumn(
                "Sıklık",
                options=["Her İş", "Günlük", "Haftalık", "Aylık", "Parti"]
            ),
            "responsible": st.column_config.TextColumn("Sorumlu"),
            "status": st.column_config.SelectboxColumn(
                "Durum",
                options=["Aktif", "Pasif", "İptal"]
            ),
            "notes": st.column_config.TextColumn("Notlar")
        },
        key="checklist_grid"
    )
    
    st.session_state.checklist_df = checklist_df

# ==========================================
# TAB 3: UYGUNSUZLUK YÖNETİMİ
# ==========================================
with tab3:
    st.markdown("### Uygunsuzluk Yönetimi")
    st.caption("Tespit edilen uygunsuzlukları, düzeltici ve önleyici faaliyetleri takip edin")
    
    @st.cache_data(ttl=300)
    def get_nonconformity_data(project_id):
        try:
            response = supabase.table("project_nonconformity").select("*").eq("project_id", project_id).execute()
            return response.data if response.data else []
        except:
            return []
    
    with loading_spinner("Uygunsuzluk verileri yükleniyor..."):
        existing_nc = get_nonconformity_data(project_id)
        time.sleep(0.3)
    
    if "nonconformity_df" not in st.session_state or st.session_state.get("nc_project") != project_id:
        st.session_state.nc_project = project_id
        if existing_nc:
            st.session_state.nonconformity_df = pd.DataFrame(existing_nc)
        else:
            st.session_state.nonconformity_df = pd.DataFrame(columns=[
                "nc_no", "description", "type", "severity", "source",
                "status", "assigned_to", "detected_date", "corrective_action",
                "preventive_action", "verification_date", "notes"
            ])
    
    nonconformity_df = st.data_editor(
        st.session_state.nonconformity_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "nc_no": st.column_config.TextColumn("Uygunsuzluk No", required=True),
            "description": st.column_config.TextColumn("Açıklama", required=True),
            "type": st.column_config.SelectboxColumn(
                "Tür",
                options=["Malzeme", "İşçilik", "Proses", "Sistem", "Doküman", "Diğer"]
            ),
            "severity": st.column_config.SelectboxColumn(
                "Şiddet",
                options=["Kritik", "Önemli", "Orta", "Düşük"]
            ),
            "source": st.column_config.SelectboxColumn(
                "Kaynak",
                options=["İç Kontrol", "Müşteri", "Denetim", "Tedarikçi", "Diğer"]
            ),
            "status": st.column_config.SelectboxColumn(
                "Durum",
                options=["Açık", "Düzeltici Faaliyette", "Kontrol Altında", "Kapalı"]
            ),
            "assigned_to": st.column_config.TextColumn("Sorumlu"),
            "detected_date": st.column_config.DateColumn("Tespit Tarihi"),
            "corrective_action": st.column_config.TextColumn("Düzeltici Faaliyet"),
            "preventive_action": st.column_config.TextColumn("Önleyici Faaliyet"),
            "verification_date": st.column_config.DateColumn("Doğrulama Tarihi"),
            "notes": st.column_config.TextColumn("Notlar")
        },
        key="nonconformity_grid"
    )
    
    st.session_state.nonconformity_df = nonconformity_df

# ==========================================
# TAB 4: KALİTE GÜVENCESİ
# ==========================================
with tab4:
    st.markdown("### Kalite Güvence Sistemi")
    st.caption("Kalite planı, prosedürler, kontroller ve kalite kayıtları yönetimi")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        #### Kalite Dokümanları
        
        | Doküman Türü | Durum |
        |--------------|-------|
        | Kalite El Kitabı | ✅ Mevcut |
        | Prosedürler | ⏳ Güncelleniyor |
        | Çalışma Talimatları | ⏳ Güncelleniyor |
        | Kalite Planı | ✅ Mevcut |
        | Test Planları | ⏳ Güncelleniyor |
        """)
    
    with col2:
        st.markdown("""
        #### Kalite Göstergeleri
        
        | Gösterge | Değer | Hedef |
        |----------|-------|-------|
        | Kalite Maliyeti | %2.5 | <%3 |
        | Uygunluk Oranı | %94 | >%95 |
        | Düzeltici Faaliyet Süresi | 8 gün | <7 gün |
        | Müşteri Memnuniyeti | 4.2/5 | >4.0 |
        """)
    
    st.markdown("#### Kalite Kayıtları")
    
    # Kalite kayıtları için örnek veri
    qa_data = pd.DataFrame({
        "Kayıt Türü": ["Muayene", "Test", "Kontrol", "Denetim", "Sertifika"],
        "Sayı": [45, 23, 67, 12, 34],
        "Uygun": [42, 20, 58, 10, 32],
        "Uygun Değil": [3, 3, 9, 2, 2],
        "Uygunluk %": [93.3, 87.0, 86.6, 83.3, 94.1]
    })
    
    st.dataframe(qa_data, use_container_width=True)

# ==========================================
# TAB 5: MAR KONTROLÜ
# ==========================================
with tab5:
    st.markdown("### MAR (Material Approval Request) Kontrolü")
    st.caption("Malzeme onay talepleri, teknik şartname uygunluk takibi ve test sonuçları")
    
    @st.cache_data(ttl=300)
    def get_mar_data(project_id):
        try:
            response = supabase.table("project_mar").select("*").eq("project_id", project_id).execute()
            return response.data if response.data else []
        except:
            return []
    
    with loading_spinner("MAR verileri yükleniyor..."):
        existing_mar = get_mar_data(project_id)
        time.sleep(0.3)
    
    if "mar_df" not in st.session_state or st.session_state.get("mar_project") != project_id:
        st.session_state.mar_project = project_id
        if existing_mar:
            st.session_state.mar_df = pd.DataFrame(existing_mar)
        else:
            st.session_state.mar_df = pd.DataFrame(columns=[
                "mar_no", "material_name", "specification", "supplier",
                "test_results", "compliance_status", "approval_status",
                "submission_date", "approval_date", "expiry_date", "notes"
            ])
    
    # MAR özet bilgileri
    if not st.session_state.mar_df.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        total_mar = len(st.session_state.mar_df)
        approved_mar = len(st.session_state.mar_df[st.session_state.mar_df["approval_status"] == "Onaylandı"])
        pending_mar = len(st.session_state.mar_df[st.session_state.mar_df["approval_status"] == "Bekliyor"])
        rejected_mar = len(st.session_state.mar_df[st.session_state.mar_df["approval_status"] == "Reddedildi"])
        
        with col1:
            st.metric("Toplam MAR", total_mar)
        with col2:
            st.metric("Onaylandı", approved_mar, delta_color="normal")
        with col3:
            st.metric("Bekliyor", pending_mar, delta_color="off")
        with col4:
            st.metric("Reddedildi", rejected_mar, delta_color="inverse")
        
        st.markdown("---")
    
    mar_df = st.data_editor(
        st.session_state.mar_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "mar_no": st.column_config.TextColumn("MAR No", required=True),
            "material_name": st.column_config.TextColumn("Malzeme Adı", required=True),
            "specification": st.column_config.TextColumn("Teknik Şartname"),
            "supplier": st.column_config.TextColumn("Tedarikçi"),
            "test_results": st.column_config.TextColumn("Test Sonuçları"),
            "compliance_status": st.column_config.SelectboxColumn(
                "Uygunluk",
                options=["Uygun", "Uygun Değil", "Kısmi Uygun", "Test Gerekiyor"]
            ),
            "approval_status": st.column_config.SelectboxColumn(
                "Onay Durumu",
                options=["Bekliyor", "Onaylandı", "Reddedildi", "Şartlı Onay"]
            ),
            "submission_date": st.column_config.DateColumn("Başvuru Tarihi"),
            "approval_date": st.column_config.DateColumn("Onay Tarihi"),
            "expiry_date": st.column_config.DateColumn("Son Kullanma Tarihi"),
            "notes": st.column_config.TextColumn("Notlar")
        },
        key="mar_grid"
    )
    
    st.session_state.mar_df = mar_df

# ==========================================
# KAYDET BUTONU
# ==========================================
st.markdown("---")

col_save, col_reset = st.columns([3, 1])

with col_save:
    if st.button("Tüm Verileri Kaydet", type="primary", use_container_width=True):
        saved_count = 0
        
        try:
            with loading_spinner("Veriler kaydediliyor..."):
                # NCR kaydet
                if "ncr_df" in st.session_state and not st.session_state.ncr_df.empty:
                    ncr_rows = st.session_state.ncr_df.to_dict(orient="records")
                    clean_ncr = [r for r in ncr_rows if str(r.get("title", "")).strip()]
                    if clean_ncr:
                        supabase.table("project_ncr").delete().eq("project_id", project_id).execute()
                        for r in clean_ncr:
                            r["project_id"] = project_id
                            r.pop("id", None)
                            supabase.table("project_ncr").insert(r).execute()
                        saved_count += len(clean_ncr)
                
                # Checklist kaydet
                if "checklist_df" in st.session_state and not st.session_state.checklist_df.empty:
                    checklist_rows = st.session_state.checklist_df.to_dict(orient="records")
                    clean_checklist = [r for r in checklist_rows if str(r.get("checklist_no", "")).strip()]
                    if clean_checklist:
                        supabase.table("project_checklist").delete().eq("project_id", project_id).execute()
                        for r in clean_checklist:
                            r["project_id"] = project_id
                            r.pop("id", None)
                            supabase.table("project_checklist").insert(r).execute()
                        saved_count += len(clean_checklist)
                
                # Uygunsuzluk kaydet
                if "nonconformity_df" in st.session_state and not st.session_state.nonconformity_df.empty:
                    nc_rows = st.session_state.nonconformity_df.to_dict(orient="records")
                    clean_nc = [r for r in nc_rows if str(r.get("nc_no", "")).strip()]
                    if clean_nc:
                        supabase.table("project_nonconformity").delete().eq("project_id", project_id).execute()
                        for r in clean_nc:
                            r["project_id"] = project_id
                            r.pop("id", None)
                            supabase.table("project_nonconformity").insert(r).execute()
                        saved_count += len(clean_nc)
                
                # MAR kaydet
                if "mar_df" in st.session_state and not st.session_state.mar_df.empty:
                    mar_rows = st.session_state.mar_df.to_dict(orient="records")
                    clean_mar = [r for r in mar_rows if str(r.get("mar_no", "")).strip()]
                    if clean_mar:
                        supabase.table("project_mar").delete().eq("project_id", project_id).execute()
                        for r in clean_mar:
                            r["project_id"] = project_id
                            r.pop("id", None)
                            supabase.table("project_mar").insert(r).execute()
                        saved_count += len(clean_mar)
                
                time.sleep(0.5)
            
            toast_success("Başarılı", f"{saved_count} kayıt başarıyla kaydedildi!")
            st.cache_data.clear()
            st.rerun()
            
        except Exception as e:
            toast_error("Hata", f"Kayıt sırasında hata oluştu: {str(e)}")

with col_reset:
    if st.button("Sayfayı Sıfırla", use_container_width=True):
        for key in ["ncr_df", "checklist_df", "nonconformity_df", "mar_df"]:
            st.session_state.pop(key, None)
        st.cache_data.clear()
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)