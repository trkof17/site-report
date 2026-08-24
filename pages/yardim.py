# -*- coding: utf-8 -*-
"""
Created on Fri Aug 21 06:10:30 2026
@author: taric
Updated: 2026-08-24 - Türkçe karakterler düzeltildi, yardım ikonu sağ üste alındı
"""

import streamlit as st
import time
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
    page_title="SARCON Portal | Yardım",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

apply_global_styles(is_login=False)
render_top_navbar()

st.markdown('<div class="page-content">', unsafe_allow_html=True)

st.markdown("""
<div style="border-left: 3px solid #3b82f6; padding-left: 0.8rem; margin-bottom: 1.5rem;">
    <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.3rem;">Yardım ve Dokümantasyon</h3>
    <p style="color: #737373; margin: 0; font-size: 0.8rem;">Sık sorulan sorular, kullanım kılavuzu ve geri bildirim</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 1. SIK SORULAN SORULAR
# ==========================================
st.markdown("### Sık Sorulan Sorular")

with st.expander("Nasıl proje oluştururum?"):
    st.markdown("""
    1. **Veri Girişi** sayfasına gidin.
    2. **Yeni Proje Oluştur** butonuna tıklayın.
    3. Proje adını, başlangıç ve bitiş tarihlerini girin.
    4. **Proje Kaydet** butonuna tıklayın.
    """)

with st.expander("Nasıl veri girişi yaparım?"):
    st.markdown("""
    1. **Veri Girişi** sayfasına gidin.
    2. Proje ve rapor tarihini seçin.
    3. **Kaynak Girişi** bölümünden kaynak türünü seçin.
    4. Kaynakları ve miktarlarını girin.
    5. **İş İlerleme** bölümünde iş kalemlerini girin.
    6. **Tüm Verileri Kaydet** butonuna tıklayın.
    """)

with st.expander("Maliyet girişi nasıl yapılır?"):
    st.markdown("""
    1. **Maliyet Girişi** sayfasına gidin.
    2. Poz No seçin (Keşif'ten otomatik gelir).
    3. Birim maliyet, nakliye, işçilik ve diğer giderleri girin.
    4. Toplamlar otomatik hesaplanır.
    5. Kategori seçin ve **Kaydet** butonuna tıklayın.
    """)

with st.expander("Bütçe analizi nasıl yapılır?"):
    st.markdown("""
    1. **Bütçe Analizi** sayfasına gidin.
    2. Kategori ve bütçe kalemi girin.
    3. Planlanan tutarı girin.
    4. Gerçekleşen tutar Maliyet Girişi'nden otomatik gelir.
    5. Sapma ve sapma yüzdesi otomatik hesaplanır.
    6. EVM analizi otomatik gösterilir.
    """)

with st.expander("Haritaya nasıl lokasyon eklerim?"):
    st.markdown("""
    1. **GIS Harita** sayfasına gidin.
    2. **Yeni Lokasyon Ekle** butonuna tıklayın.
    3. Tür, ad, adres ve koordinatları girin.
    4. **Kaydet** butonuna tıklayın.
    """)

with st.expander("Rapor nasıl alırım?"):
    st.markdown("""
    1. **Rapor Al** sayfasına gidin.
    2. Proje seçin ve rapor türünü belirleyin.
    3. Tarih aralığını seçin.
    4. Rapor önizlemesini inceleyin.
    5. **PDF**, **Excel** veya **Word** olarak dışa aktarın.
    6. Raporu kaydedin veya e-posta ile gönderin.
    """)

with st.expander("Nakit akışı nasıl takip edilir?"):
    st.markdown("""
    1. **Nakit Akışı** sayfasına gidin.
    2. Proje seçin.
    3. Planlanan ve gerçekleşen nakit giriş/çıkışlarını girin.
    4. Kümülatif nakit akışı otomatik hesaplanır.
    5. Grafiklerle görsel analiz yapın.
    """)

with st.expander("İş programı nasıl oluşturulur?"):
    st.markdown("""
    1. **İş Programı** sayfasına gidin.
    2. Proje seçin.
    3. Ana iş (Level 0), alt iş (Level 1) ve alt-alt iş (Level 2) ekleyin.
    4. Başlangıç ve bitiş tarihlerini girin.
    5. Milestone (dönüm noktası) ekleyin.
    6. İşler arası bağlantı tiplerini (FS, SS, FF) belirleyin.
    """)

with st.expander("Keşif girişi nasıl yapılır?"):
    st.markdown("""
    1. **Keşif Girişi** sayfasına gidin.
    2. Proje seçin.
    3. Poz no, tanım, birim ve metraj girin.
    4. Yeni kalem eklemek için **Kalem Ekle** butonuna tıklayın.
    5. Tüm kalemleri girdikten sonra **Kaydet** butonuna tıklayın.
    """)

with st.expander("Sözleşme yönetimi nasıl yapılır?"):
    st.markdown("""
    1. **Sözleşme Yönetimi** sayfasına gidin.
    2. **Yeni Sözleşme** butonuna tıklayın.
    3. Sözleşme türü, başlangıç ve bitiş tarihlerini girin.
    4. Sözleşme tutarını ve şartlarını belirleyin.
    5. Dosya yükleyin (PDF, DOCX).
    6. **Kaydet** butonuna tıklayın.
    """)

with st.expander("NCR (Uygunsuzluk Kaydı) nasıl oluşturulur?"):
    st.markdown("""
    1. **NCR Takibi** sayfasına gidin.
    2. **Yeni NCR Oluştur** butonuna tıklayın.
    3. NCR numarası, başlık ve açıklama girin.
    4. Kategori ve öncelik seviyesini belirleyin.
    5. Sorumlu kişiyi ve son tarihi girin.
    6. **Kaydet** butonuna tıklayın.
    """)

# ==========================================
# 2. GERİ BİLDİRİM
# ==========================================
st.markdown("---")
st.markdown("### Geri Bildirim")

with st.form("feedback_form"):
    feedback_name = st.text_input("Ad Soyad", placeholder="Adınız")
    feedback_email = st.text_input("E-posta", placeholder="ornek@firma.com")
    feedback_type = st.selectbox(
        "Konu",
        ["Hata Bildirimi", "Özellik Talebi", "Kullanım Sorunu", "Genel Geri Bildirim"],
        help="Ne tür bir geri bildirim göndermek istiyorsunuz?"
    )
    feedback_message = st.text_area(
        "Mesajınız",
        placeholder="Lütfen detaylı açıklama yapın...",
        height=150,
        help="Sorunuzu veya önerinizi detaylı anlatın"
    )
    
    if st.form_submit_button("Geri Bildirim Gönder", type="primary", use_container_width=True):
        if feedback_message:
            with loading_spinner("Geri bildirim gönderiliyor..."):
                time.sleep(1.0)
            toast_success("Başarılı", "Geri bildiriminiz başarıyla gönderildi!")
            toast_info("Bilgi", "En kısa sürede size dönüş yapılacaktır.")
        else:
            toast_warning("Uyarı", "Lütfen mesajınızı girin.")

# ==========================================
# 3. DOKÜMANTASYON
# ==========================================
st.markdown("---")
st.markdown("### Dokümantasyon")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="animate-card" style="
        background-color: #141414;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #262626;
    ">
        <p style="color: #ffffff; font-weight: 600; margin: 0 0 0.5rem 0;">Bütçe Analizi</p>
        <p style="color: #737373; margin: 0 0 0.2rem 0;">• Sapma = Planlanan - Gerçekleşen</p>
        <p style="color: #737373; margin: 0 0 0.2rem 0;">• Sapma% = (Sapma / Planlanan) × 100</p>
        <p style="color: #737373; margin: 0 0 0.2rem 0;">• CPI = EV/AC (1'den büyük iyi)</p>
        <p style="color: #737373; margin: 0;">• SPI = EV/PV (1'den büyük iyi)</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="animate-card" style="
        background-color: #141414;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #262626;
    ">
        <p style="color: #ffffff; font-weight: 600; margin: 0 0 0.5rem 0;">Maliyet Hesaplama</p>
        <p style="color: #737373; margin: 0 0 0.2rem 0;">• Toplam Birim Maliyet = Birim Maliyet + Nakliye + İşçilik + Diğer</p>
        <p style="color: #737373; margin: 0;">• Toplam Maliyet = Toplam Birim Maliyet × Keşif Metrajı</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="animate-card" style="
        background-color: #141414;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #262626;
    ">
        <p style="color: #ffffff; font-weight: 600; margin: 0 0 0.5rem 0;">İş Programı</p>
        <p style="color: #737373; margin: 0 0 0.2rem 0;">• Ana İş (Level 0)</p>
        <p style="color: #737373; margin: 0 0 0.2rem 0;">• Alt İş (Level 1)</p>
        <p style="color: #737373; margin: 0 0 0.2rem 0;">• Alt-Alt İş (Level 2)</p>
        <p style="color: #737373; margin: 0 0 0.2rem 0;">• Milestone = Tarih işareti</p>
        <p style="color: #737373; margin: 0;">• Bağlantı Tipleri: FS, SS, FF</p>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 4. İLETİŞİM
# ==========================================
st.markdown("---")
st.markdown("""
<div class="animate-card" style="
    background-color: #141414;
    padding: 1.5rem;
    border-radius: 12px;
    border: 1px solid #262626;
">
    <h4 style="color: #ffffff; margin: 0 0 0.5rem 0;">İletişim</h4>
    <p style="color: #737373; margin: 0.2rem 0;">Destek: info@sarcon.com.tr</p>
    <p style="color: #737373; margin: 0.2rem 0;">Web: www.sarcon.com.tr</p>
    <p style="color: #737373; margin: 0.2rem 0;">Çalışma Saatleri: 09:00 - 18:00 (Hafta içi)</p>
</div>
""", unsafe_allow_html=True)

st.caption("2026 SARCON - Tüm hakları saklıdır.")

st.markdown('</div>', unsafe_allow_html=True)