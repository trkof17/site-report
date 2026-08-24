# -*- coding: utf-8 -*-
"""
Created on Mon Aug 24 21:23:51 2026

@author: taric
"""

import streamlit as st
import base64
from utils.auth import sign_up, sign_in, get_current_user
from utils.styles import apply_global_styles
from utils.animations import apply_animations  # <-- EKLENDİ

st.set_page_config(
    page_title="sarcon | Giriş",
    page_icon="🏗️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Login teması ve sidebar gizleme uygula
apply_global_styles(is_login=True)
apply_animations()  # <-- EKLENDİ - Animasyonları aktif et

# Session initialization
if "user" not in st.session_state:
    st.session_state.user = None
    st.session_state.logged_in = False

if st.session_state.user is None:
    user = get_current_user()
    if user:
        st.session_state.user = user
        st.session_state.logged_in = True
        st.switch_page("pages/dashboard.py")

# Logo helper
def get_logo_base64():
    try:
        with open("logo.png", "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return None

logo_b64 = get_logo_base64()

if logo_b64:
    st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: flex-start; margin-bottom: 2rem;">
        <img src="data:image/png;base64,{logo_b64}" style="height: 48px; width: auto; object-fit: contain;">
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <h2 style="color: #ffffff; font-weight: 700; margin-bottom: 2rem; letter-spacing: -0.5px;">🏗️ SARCON PORTAL</h2>
    """, unsafe_allow_html=True)

# Login & Register Tabs
tab1, tab2 = st.tabs(["Giriş Yap", "Kayıt Ol"])

with tab1:
    # FORM kullanımı - autofill sorununu çözer
    with st.form("login_form"):
        email = st.text_input(
            "E-posta", 
            key="login_email", 
            placeholder="ornek@firma.com",
            autocomplete="email"
        )
        password = st.text_input(
            "Şifre", 
            type="password", 
            key="login_password", 
            placeholder="••••••••",
            autocomplete="current-password"
        )
        
        submitted = st.form_submit_button("Giriş Yap", use_container_width=True)
        
        if submitted:
            if not email or not password:
                st.warning("Lütfen e-posta ve şifre alanlarını doldurun.")
            else:
                with st.spinner("🔐 Oturum açılıyor..."):
                    user, err = sign_in(email.strip(), password)
                    if user:
                        st.session_state.user = user
                        st.session_state.logged_in = True
                        st.switch_page("pages/dashboard.py")
                    else:
                        st.error(f"❌ {err}")

with tab2:
    with st.form("signup_form"):
        email = st.text_input(
            "E-posta", 
            key="signup_email", 
            placeholder="ornek@firma.com",
            autocomplete="email"
        )
        password = st.text_input(
            "Şifre", 
            type="password", 
            key="signup_password", 
            placeholder="•••••••• (en az 6 karakter)",
            autocomplete="new-password"
        )
        
        submitted = st.form_submit_button("Kayıt Ol", use_container_width=True)
        
        if submitted:
            if not email or not password:
                st.warning("Lütfen e-posta ve şifre alanlarını doldurun.")
            else:
                with st.spinner("📝 Hesap oluşturuluyor..."):
                    user, err = sign_up(email.strip(), password)
                    if user:
                        st.success("✅ Kayıt başarılı! Şimdi giriş yapabilirsiniz.")
                    else:
                        st.error(f"❌ {err}")

# Footer
st.markdown("""
<div style="margin-top: 4rem; text-align: center; color: #525252; font-size: 0.75rem;">
    © 2026 SARCON
</div>
""", unsafe_allow_html=True)