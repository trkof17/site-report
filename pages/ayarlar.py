# -*- coding: utf-8 -*-
"""
Ayarlar Sayfası - SARCON Portal
Uygulama ayarları, bildirimler ve tercihler
"""

import streamlit as st
from utils.styles import apply_global_styles
from utils.auth import get_current_user
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
    page_title="SARCON Portal | Ayarlar",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

apply_global_styles(is_login=False)
render_top_navbar()

st.markdown('<div class="page-content">', unsafe_allow_html=True)

st.markdown("""
<div style="border-left: 3px solid #3b82f6; padding-left: 0.8rem; margin-bottom: 1.5rem;">
    <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.3rem;">⚙️ Uygulama Ayarları</h3>
    <p style="color: #737373; margin: 0; font-size: 0.8rem;">Uygulama tercihlerinizi ve bildirim ayarlarınızı yönetin</p>
</div>
""", unsafe_allow_html=True)

user = get_current_user()

if not user:
    toast_error("Oturum Hatası", "Oturum bilgileriniz alınamadı. Lütfen tekrar giriş yapın.")
    if st.button("Giriş Sayfasına Dön", use_container_width=True):
        st.switch_page("app.py")
    st.stop()

# Ana ayarlar
tab1, tab2, tab3 = st.tabs(["🎨 Görünüm", "🔔 Bildirimler", "📊 Veri"])

# ===================== TAB 1: GÖRÜNÜM =====================
with tab1:
    st.markdown("""
    <div class="animate-card" style="
        background-color: #141414;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #262626;
    ">
        <h4 style="color: #ffffff; margin: 0 0 1rem 0;">🎨 Tema ve Görünüm</h4>
    </div>
    """, unsafe_allow_html=True)
    
    toast_info("Bilgi", "Tema tercihi ve görünüm ayarları yakında eklenecektir.")
    
    with st.container():
        st.selectbox("Tema", options=["Koyu (Varsayılan)", "Açık", "Sistem"], disabled=True)
        st.selectbox("Dil", options=["Türkçe", "İngilizce", "Arapça"], disabled=True)
        st.slider("Yazı Boyutu", min_value=80, max_value=120, value=100, step=5, disabled=True)
    
    toast_info("⏳", "Bu özellikler ileriki sürümlerde aktif olacaktır.")

# ===================== TAB 2: BİLDİRİMLER =====================
with tab2:
    st.markdown("""
    <div class="animate-card" style="
        background-color: #141414;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #262626;
    ">
        <h4 style="color: #ffffff; margin: 0 0 1rem 0;">🔔 Bildirim Ayarları</h4>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("E-posta Bildirimleri")
    
    col1, col2 = st.columns(2)
    with col1:
        st.toggle("📧 Proje Güncellemeleri", value=True)
        st.toggle("📧 Hakediş Onayları", value=True)
        st.toggle("📧 NCR Bildirimleri", value=True)
    with col2:
        st.toggle("📧 Haftalık Raporlar", value=False)
        st.toggle("📧 Sistem Uyarıları", value=True)
        st.toggle("📧 Kullanıcı Davetleri", value=True)
    
    st.divider()
    
    # İkinci mail adresi (profil'den alınan)
    user_data = st.session_state.get('user_data', {})
    yedek_email = user_data.get('yedek_email', 'Tanımlanmamış')
    
    st.markdown(f"""
    <div class="animate-card" style="
        background-color: #141414;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #262626;
        margin: 0.5rem 0;
    ">
        <p style="color: #737373; margin: 0;">📧 Yedek E-posta: <strong style="color: #ffffff;">{yedek_email}</strong></p>
        <p style="color: #737373; font-size: 0.8rem; margin: 0;">(Profil sayfasından değiştirebilirsiniz)</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("👤 Profil Sayfasına Git", use_container_width=True, key="profile_btn"):
        try:
            st.switch_page("pages/profil.py")
        except:
            toast_error("Hata", "Profil sayfasına gidilemedi")

# ===================== TAB 3: VERİ =====================
with tab3:
    st.markdown("""
    <div class="animate-card" style="
        background-color: #141414;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #262626;
    ">
        <h4 style="color: #ffffff; margin: 0 0 1rem 0;">📊 Veri Yönetimi</h4>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("Veri İşlemleri")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Örnek Veri Yükle", use_container_width=True, key="load_data"):
            with loading_spinner("Örnek veriler yükleniyor..."):
                import time
                time.sleep(1.5)
                toast_success("Başarılı", "Örnek veriler başarıyla yüklendi!")
    
    with col2:
        if st.button("🗑️ Test Verilerini Temizle", use_container_width=True, key="clear_data"):
            toast_warning("Uyarı", "Bu işlem tüm test verilerini silecektir.")
            if st.button("Evet, Temizle", key="confirm_clear"):
                with loading_spinner("Veriler temizleniyor..."):
                    import time
                    time.sleep(1.5)
                    toast_success("Başarılı", "Test verileri temizlendi!")
    
    st.divider()
    
    st.subheader("Veritabanı Bilgileri")
    
    st.markdown("""
    <div class="animate-card" style="
        background-color: #141414;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #262626;
    ">
        <p style="color: #737373; margin: 0.2rem 0;">📊 <strong style="color: #ffffff;">Veritabanı Durumu</strong></p>
        <p style="color: #737373; margin: 0.2rem 0;">• Bağlantı: <span style="color: #22c55e;">✅ Aktif</span></p>
        <p style="color: #737373; margin: 0.2rem 0;">• Tablo Sayısı: <span style="color: #ffffff;">19</span></p>
        <p style="color: #737373; margin: 0.2rem 0;">• Kayıt Sayısı: <span style="color: #ffffff;">Demo modu</span></p>
        <p style="color: #737373; margin: 0.2rem 0;">• Son Yedekleme: <span style="color: #ffffff;">22.08.2026</span></p>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.divider()
st.caption("SARCON Portal v0.1 - Ayarlar")
st.markdown('</div>', unsafe_allow_html=True)