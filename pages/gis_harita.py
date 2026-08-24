# -*- coding: utf-8 -*-
"""
Created on Thu Aug 20 19:23:22 2026
@author: taric
Updated: 2026-08-22 - Animasyonlar eklendi, ikonlar kaldırıldı
"""

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
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
    page_title="SARCON Portal | GIS / Harita",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

apply_global_styles(is_login=False)
render_top_navbar()

st.markdown('<div class="page-content">', unsafe_allow_html=True)

st.markdown("""
<div style="border-left: 3px solid #3b82f6; padding-left: 0.8rem; margin-bottom: 1.5rem;">
    <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.3rem;">GIS / Harita</h3>
    <p style="color: #737373; margin: 0; font-size: 0.8rem;">Proje sahasi, tedarikciler ve potansiyel musterileri harita uzerinde goruntuleyin</p>
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
# 2. MEVCUT LOKASYONLARI CEK
# ==========================================
@st.cache_data(ttl=300)
def get_locations(project_id):
    try:
        response = supabase.table("project_locations").select("*").eq("project_id", project_id).execute()
        return response.data if response.data else []
    except:
        return []

with loading_spinner("Lokasyonlar yukleniyor..."):
    existing_locations = get_locations(project_id)
    time.sleep(0.3)

# ==========================================
# 3. TABLAR
# ==========================================
tab1, tab2 = st.tabs(["Harita", "Lokasyonlar"])

# ==========================================
# TAB 1: HARITA
# ==========================================
with tab1:
    st.markdown("### Proje Haritasi")
    
    # Harita merkezi - proje lokasyonu varsa oraya git
    if existing_locations:
        first_loc = existing_locations[0]
        map_center = [first_loc.get('latitude', 39.9334), first_loc.get('longitude', 32.8597)]
    else:
        map_center = [39.9334, 32.8597]  # Turkiye merkez
    
    # Haritayi olustur
    m = folium.Map(
        location=map_center, 
        zoom_start=10,
        tiles="OpenStreetMap",
        width="100%",
        height=500
    )
    
    # Lokasyonlari ekle
    if existing_locations:
        for loc in existing_locations:
            if loc.get('latitude') and loc.get('longitude'):
                # Renk haritasi
                color = {
                    'project': 'blue',
                    'supplier': 'green',
                    'client': 'orange',
                    'resource': 'red'
                }.get(loc.get('location_type'), 'gray')
                
                # Ikon
                icon = {
                    'project': 'home',
                    'supplier': 'truck',
                    'client': 'briefcase',
                    'resource': 'toolbox'
                }.get(loc.get('location_type'), 'info-sign')
                
                # Tip etiketi
                type_label = {
                    'project': 'Proje',
                    'supplier': 'Tedarikci',
                    'client': 'Musteri',
                    'resource': 'Kaynak'
                }.get(loc.get('location_type'), loc.get('location_type', ''))
                
                folium.Marker(
                    location=[loc['latitude'], loc['longitude']],
                    popup=folium.Popup(f"""
                        <b>{loc['name']}</b><br>
                        <b>Tur:</b> {type_label}<br>
                        <b>Adres:</b> {loc.get('address', '')}<br>
                        <b>Aclama:</b> {loc.get('description', '')}
                    """, max_width=300),
                    tooltip=loc['name'],
                    icon=folium.Icon(color=color, icon=icon, prefix='fa')
                ).add_to(m)
    
    # Haritayi render et
    st_data = st_folium(
        m, 
        width=700, 
        height=500,
        key="gis_map"
    )
    
    # Harita bilgisi
    if st_data and st_data.get('last_clicked'):
        toast_info("Bilgi", f"Son tiklanan: {st_data['last_clicked']}")

# ==========================================
# TAB 2: LOKASYONLAR
# ==========================================
with tab2:
    st.markdown("### Lokasyon Yonetimi")
    
    # Yeni lokasyon ekle
    with st.expander("Yeni Lokasyon Ekle", expanded=False):
        with st.form("new_location"):
            col1, col2 = st.columns(2)
            with col1:
                location_type = st.selectbox(
                    "Lokasyon Turu",
                    ["project", "supplier", "client", "resource"],
                    help="project=Proje Sahasi, supplier=Tedarikci, client=Musteri, resource=Kaynak"
                )
                name = st.text_input("Ad", placeholder="Lokasyon adi")
                address = st.text_input("Adres", placeholder="Adres bilgisi")
            with col2:
                latitude = st.number_input("Enlem (Latitude)", value=39.9334, format="%.6f", step=0.0001)
                longitude = st.number_input("Boylam (Longitude)", value=32.8597, format="%.6f", step=0.0001)
                description = st.text_area("Aciklama", placeholder="Lokasyon aciklamasi")
            
            if st.form_submit_button("Lokasyonu Kaydet", type="primary", use_container_width=True):
                if name:
                    data = {
                        "project_id": project_id,
                        "location_type": location_type,
                        "name": name,
                        "address": address,
                        "latitude": latitude,
                        "longitude": longitude,
                        "description": description
                    }
                    try:
                        with loading_spinner("Lokasyon kaydediliyor..."):
                            response = supabase.table("project_locations").insert(data).execute()
                            time.sleep(0.3)
                        toast_success("Basarili", "Lokasyon kaydedildi!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        toast_error("Hata", f"Kayit hatasi: {e}")
                else:
                    toast_warning("Uyari", "Lokasyon adi girin.")
    
    # Mevcut lokasyonlari listele
    if existing_locations:
        df = pd.DataFrame(existing_locations)
        
        # Turkce tip etiketleri
        type_labels = {
            'project': 'Proje',
            'supplier': 'Tedarikci',
            'client': 'Musteri',
            'resource': 'Kaynak'
        }
        df['type_label'] = df['location_type'].map(type_labels).fillna(df['location_type'])
        
        st.dataframe(
            df[["type_label", "name", "address", "latitude", "longitude"]],
            use_container_width=True,
            column_config={
                "type_label": "Tur",
                "name": "Ad",
                "address": "Adres",
                "latitude": "Enlem",
                "longitude": "Boylam"
            },
            hide_index=True
        )
        
        # Lokasyon sil
        st.markdown("### Lokasyon Sil")
        loc_to_delete = st.selectbox(
            "Silinecek lokasyonu secin",
            [""] + [l["name"] for l in existing_locations],
            key="delete_location"
        )
        
        if loc_to_delete and st.button("Lokasyonu Sil", use_container_width=True):
            try:
                with loading_spinner("Lokasyon siliniyor..."):
                    loc_id = next(l["id"] for l in existing_locations if l["name"] == loc_to_delete)
                    supabase.table("project_locations").delete().eq("id", loc_id).execute()
                    time.sleep(0.3)
                toast_success("Basarili", "Lokasyon silindi!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                toast_error("Hata", f"Silme hatasi: {e}")
    else:
        toast_info("Bilgi", "Henuz lokasyon eklenmemis.")

# ==========================================
# 4. BILGI ALANI
# ==========================================
with st.expander("Harita Kullanim Kilavuzu"):
    st.markdown("""
    **Harita Nasil Kullanilir?**
    
    1. **Lokasyon Ekle:** "Yeni Lokasyon Ekle" butonuna tiklayin.
    2. **Tur Secin:** Proje, Tedarikci, Musteri veya Kaynak secin.
    3. **Koordinat Girin:** Enlem ve boylam bilgilerini girin.
    4. **Haritada Gorun:** Kaydedilen lokasyonlar haritada isaretlenir.
    5. **Detay Gor:** Haritadaki isarete tiklayarak detaylari gorun.
    6. **Sil:** Istenmeyen lokasyonlari "Lokasyon Sil" bolumunden kaldirin.
    
    **Koordinat Bulma:**
    - Google Maps'te sag tik "Burada ne var?" koordinatlar gorunur
    - Koordinatlari kopyalayarak buraya yapistirin
    """)

st.markdown('</div>', unsafe_allow_html=True)