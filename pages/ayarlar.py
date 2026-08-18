# -*- coding: utf-8 -*-
"""
Created on Mon Aug 17 03:50:16 2026

@author: taric
"""

import streamlit as st
from utils.styles import apply_global_styles, render_top_navbar
from utils.auth import get_current_user

st.set_page_config(
    page_title="SARCON Portal | Ayarlar",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

apply_global_styles(is_login=False)
render_top_navbar()

st.markdown("""
<div style="border-left: 3px solid #3b82f6; padding-left: 0.8rem; margin-bottom: 1.5rem;">
    <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.3rem;">👤 Kullanıcı Ayarları</h3>
    <p style="color: #737373; margin: 0; font-size: 0.8rem;">Profil bilgilerinizi ve hesap ayarlarınızı yönetin</p>
</div>
""", unsafe_allow_html=True)

user = get_current_user()

if user:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown(f"""
        <div style="
            background-color: #141414;
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid #262626;
            text-align: center;
        ">
            <div style="font-size: 4rem; opacity: 0.6;">👤</div>
            <h4 style="color: #ffffff; margin: 0.5rem 0 0.2rem 0;">{user.email}</h4>
            <p style="color: #737373; font-size: 0.8rem;">Kullanıcı</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="
            background-color: #141414;
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid #262626;
        ">
            <h4 style="color: #ffffff; margin: 0 0 1rem 0;">Hesap Bilgileri</h4>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("profile_form"):
            st.text_input("E-posta", value=user.email, disabled=True)
            st.text_input("Ad Soyad", placeholder="Henüz eklenmedi")
            st.text_input("Şirket", placeholder="Henüz eklenmedi")
            st.text_input("Telefon", placeholder="Henüz eklenmedi")
            
            if st.form_submit_button("Bilgileri Güncelle", use_container_width=True):
                st.success("✅ Bilgiler güncellendi! (Bu özellik yakında tam aktif olacak)")
else:
    st.warning("Oturum bilgileriniz alınamadı.")