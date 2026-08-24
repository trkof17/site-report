# -*- coding: utf-8 -*-
"""
Profil Sayfası - SARCON Portal
Kullanıcı bilgileri, hesap ayarları ve yetki yönetimi
Created: 22 Ağustos 2026
Updated: 2026-08-22 - Animasyonlar eklendi, ikonlar kaldırıldı
"""

import streamlit as st
import time
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
    page_title="SARCON Portal | Profil",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

apply_global_styles(is_login=False)
render_top_navbar()

st.markdown('<div class="page-content">', unsafe_allow_html=True)

st.markdown("""
<div style="border-left: 3px solid #3b82f6; padding-left: 0.8rem; margin-bottom: 1.5rem;">
    <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.3rem;">Profilim</h3>
    <p style="color: #737373; margin: 0; font-size: 0.8rem;">Kisisel bilgilerinizi ve hesap ayarlarinizi yönetin</p>
</div>
""", unsafe_allow_html=True)

user = get_current_user()

if not user:
    toast_warning("Oturum Hatasi", "Oturum bilgileriniz alinamadi. Lutfen tekrar giris yapin.")
    if st.button("Giris Sayfasina Don", use_container_width=True):
        st.switch_page("app.py")
    st.stop()

# Kullanici bilgilerini session'dan al veya varsayilan degerler kullan
user_data = st.session_state.get('user_data', {})
user_email = user.email if hasattr(user, 'email') else user_data.get('email', 'Bilgi yok')

# TAB'lar: Profil | Hesap Ayarlari | Yetki Yönetimi
tab1, tab2, tab3 = st.tabs(["Profil Bilgileri", "Hesap Ayarlari", "Yetki Yönetimi"])

# ===================== TAB 1: PROFIL BILGILERI =====================
with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown(f"""
        <div class="animate-card" style="
            background-color: #141414;
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid #262626;
            text-align: center;
        ">
            <div style="font-size: 4rem; opacity: 0.6;">👤</div>
            <h4 style="color: #ffffff; margin: 0.5rem 0 0.2rem 0;">{user_data.get('ad_soyad', 'Isimsiz Kullanici')}</h4>
            <p style="color: #737373; font-size: 0.8rem;">{user_data.get('pozisyon', 'Pozisyon belirtilmemis')}</p>
            <p style="color: #555555; font-size: 0.7rem; margin-top: 0.5rem;">{user_email}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="animate-card" style="
            background-color: #141414;
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid #262626;
        ">
            <h4 style="color: #ffffff; margin: 0 0 1rem 0;">Kisisel Bilgiler</h4>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("profile_form", clear_on_submit=False):
            ad_soyad = st.text_input(
                "Ad Soyad",
                value=user_data.get('ad_soyad', ''),
                placeholder="Adiniz ve soyadiniz"
            )
            email = st.text_input("E-posta", value=user_email, disabled=True)
            
            yetki = st.selectbox(
                "Yetki Seviyesi",
                options=["Admin", "Proje Müdürü", "Teknik Ofis Müh.", "Isveren", "Mühendis", "Izleyici"],
                index=0 if user_data.get('yetki', '') == "Admin" else 1
            )
            
            pozisyon = st.selectbox(
                "Firmadaki Pozisyonu",
                options=["Proje Müdürü", "Teknik Ofis Mühendisi", "Isveren", "Santiye Sefi", "Kontrol Mühendisi", "Diger"],
                index=0 if user_data.get('pozisyon', '') == "Proje Müdürü" else 1
            )
            
            adres = st.text_area(
                "Adres",
                value=user_data.get('adres', ''),
                placeholder="Ev adresiniz",
                height=80
            )
            
            firma_adresi = st.text_area(
                "Firma Adresi",
                value=user_data.get('firma_adresi', ''),
                placeholder="Firma adresiniz",
                height=80
            )
            
            st.divider()
            
            col_save1, col_save2 = st.columns([1, 3])
            with col_save1:
                if st.form_submit_button("Bilgileri Guncelle", use_container_width=True):
                    with loading_spinner("Bilgiler guncelleniyor..."):
                        st.session_state.user_data = {
                            'ad_soyad': ad_soyad,
                            'email': email,
                            'yetki': yetki,
                            'pozisyon': pozisyon,
                            'adres': adres,
                            'firma_adresi': firma_adresi
                        }
                        time.sleep(0.3)
                    toast_success("Basarili", "Profil bilgileriniz guncellendi!")

# ===================== TAB 2: HESAP AYARLARI =====================
with tab2:
    st.markdown("""
    <div class="animate-card" style="
        background-color: #141414;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #262626;
        margin-bottom: 1rem;
    ">
        <h4 style="color: #ffffff; margin: 0 0 0.5rem 0;">Hesap Guvenligi</h4>
        <p style="color: #737373; margin: 0; font-size: 0.8rem;">Sifrenizi guncelleyin ve hesap bilgilerinizi yönetin</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sifre Degistir
    with st.expander("Sifre Degistir", expanded=False):
        with st.form("password_form"):
            st.text_input("Mevcut Sifre", type="password")
            st.text_input("Yeni Sifre", type="password")
            st.text_input("Yeni Sifre (Tekrar)", type="password")
            
            if st.form_submit_button("Sifreyi Guncelle", use_container_width=True):
                with loading_spinner("Sifre guncelleniyor..."):
                    time.sleep(0.5)
                toast_success("Basarili", "Sifreniz basariyla guncellendi! (Demo modu)")

    st.divider()
    
    # Ikinci Mail Adresi
    st.markdown("""
    <h5 style="color: #ffffff; margin: 0 0 0.5rem 0;">Yedek E-posta Adresi</h5>
    <p style="color: #737373; margin: 0 0 1rem 0; font-size: 0.8rem;">Bildirimler ve yedek iletisim icin ikinci bir e-posta adresi tanimlayin</p>
    """, unsafe_allow_html=True)
    
    with st.form("email_form"):
        yedek_email = st.text_input(
            "Yedek E-posta",
            value=user_data.get('yedek_email', ''),
            placeholder="yedek@email.com"
        )
        
        if st.form_submit_button("Yedek E-postayi Guncelle", use_container_width=True):
            with loading_spinner("E-posta guncelleniyor..."):
                st.session_state.user_data['yedek_email'] = yedek_email
                time.sleep(0.3)
            toast_success("Basarili", f"Yedek e-posta adresi guncellendi: {yedek_email}")
    
    st.divider()
    
    # Ayarlar Sayfasina Yönlendirme
    st.markdown("""
    <div class="animate-card" style="
        background-color: #141414;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #262626;
        margin-top: 1rem;
    ">
        <h5 style="color: #ffffff; margin: 0 0 0.5rem 0;">Gelismis Ayarlar</h5>
        <p style="color: #737373; margin: 0 0 1rem 0; font-size: 0.8rem;">Uygulama ayarlari, bildirimler ve diger tercihler icin</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Ayarlar Sayfasina Git", use_container_width=True):
        try:
            st.switch_page("pages/ayarlar.py")
        except:
            toast_error("Hata", "Ayarlar sayfasina gidilemedi")

# ===================== TAB 3: YETKI YÖNETIMI =====================
with tab3:
    st.markdown("""
    <div class="animate-card" style="
        background-color: #141414;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #262626;
        margin-bottom: 1rem;
    ">
        <h4 style="color: #ffffff; margin: 0 0 0.5rem 0;">Proje Yetkilendirme</h4>
        <p style="color: #737373; margin: 0; font-size: 0.8rem;">Diger kullanicilara projeleriniz uzerinde yetki verin</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Mevcut yetkilendirilmis kullanicilar
    st.markdown("### Yetkilendirilmis Kullanicilar")
    
    authorized_users = user_data.get('authorized_users', [
        {"email": "ahmet@firma.com", "yetki": "Goruntuleme"},
        {"email": "mehmet@firma.com", "yetki": "Düzenleme"}
    ])
    
    if authorized_users:
        for idx, auth_user in enumerate(authorized_users):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.text(auth_user['email'])
            with col2:
                st.text(auth_user['yetki'])
            with col3:
                if st.button("Sil", key=f"remove_{idx}"):
                    authorized_users.pop(idx)
                    st.session_state.user_data['authorized_users'] = authorized_users
                    toast_success("Basarili", "Kullanici kaldirildi")
                    st.rerun()
        
        st.divider()
    else:
        toast_info("Bilgi", "Henuz yetkilendirilmis kullanici yok.")
    
    # Yeni kullanici ekle
    st.markdown("### Yeni Kullanici Ekle")
    
    with st.form("add_user_form"):
        col1, col2 = st.columns([2, 1])
        with col1:
            new_email = st.text_input("E-posta Adresi", placeholder="kullanici@firma.com")
        with col2:
            new_permission = st.selectbox("Yetki", ["Goruntuleme", "Düzenleme"])
        
        if st.form_submit_button("Kullanici Ekle", use_container_width=True):
            if new_email and new_email not in [u['email'] for u in authorized_users]:
                authorized_users.append({"email": new_email, "yetki": new_permission})
                st.session_state.user_data['authorized_users'] = authorized_users
                toast_success("Basarili", f"{new_email} yetkilendirildi ({new_permission})")
                st.rerun()
            elif new_email in [u['email'] for u in authorized_users]:
                toast_warning("Uyari", "Bu kullanici zaten yetkilendirilmis.")

    st.divider()
    
    # Yetki aciklamasi
    with st.expander("Yetki Seviyeleri Hakkinda"):
        st.markdown("""
        - **Goruntuleme**: Projeyi goruntuleyebilir, raporlari inceleyebilir
        - **Düzenleme**: Projeye veri girebilir, guncelleme yapabilir
        - **Ayni Anda Düzenleme**: Birden fazla kullanici ayni proje uzerinde calisabilir.
          Son kaydedenin degisiklikleri gecerli olur.
        """)

st.divider()
st.caption("SARCON Portal v0.1 - Profil Yönetimi")

st.markdown('</div>', unsafe_allow_html=True)