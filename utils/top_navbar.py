import streamlit as st
import base64

def get_logo_base64():
    try:
        with open("logo.png", "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return None

def render_top_navbar():
    # Streamlit'in tüm üst header ve container boşluklarını tam olarak sıfırlayan CSS
    st.markdown("""
    <style>
        /* 1. Native Header, AppHeader ve Sidebar Alanlarını Gizle ve Sıfırla */
        [data-testid="stHeader"], 
        [data-testid="stAppHeader"],
        [data-testid="stSidebar"], 
        [data-testid="stSidebarCollapsedControl"],
        header[data-testid="stHeader"] { 
            display: none !important; 
            height: 0px !important;
            min-height: 0px !important;
            padding: 0px !important;
            margin: 0px !important;
        }
        
        /* 2. Ana Uygulama Kapsayıcısını En Tepeye Çek */
        .stApp {
            margin-top: 0px !important;
            padding-top: 0px !important;
        }

        /* 3. Sayfa İçerik Konteynerinin Üst Padding'ini Sıfırla */
        .main .block-container,
        div[data-testid="stMainBlockContainer"] { 
            padding-top: 0.25rem !important;
            padding-bottom: 2rem !important;
            margin-top: 0px !important;
        }

        /* 4. Top Navbar Popover & Button Stillerini Koru */
        div[data-testid="stPopover"] > button, 
        div.stButton > button {
            background-color: transparent !important;
            color: #9aa8b9 !important;
            border: 1px solid #2a2d3d !important;
            font-weight: 500 !important;
            font-size: 0.9rem !important;
            padding: 0.4rem 0.6rem !important;
            box-shadow: none !important;
            transition: all 0.2s ease;
        }

        div[data-testid="stPopover"] > button:hover, 
        div.stButton > button:hover {
            color: #ffffff !important;
            background-color: rgba(255, 255, 255, 0.08) !important;
            border-color: #4a4d5d !important;
            border-radius: 6px !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Menü Grupları
    menu_groups = {
        "Proje & Giriş": [
            ("Keşif Girişi", "pages/kesif_girisi.py"),
            ("Maliyet Girişi", "pages/maliyet_girisi.py"),
            ("Veri Girişi", "pages/veri_girisi.py"),
            ("Sözleşme Yönetimi", "pages/sozlesme_yonetimi.py"),
        ],
        "Saha & Takip": [
            ("İlerleme Durumu", "pages/ilerleme_durumu.py"),
            ("İş Programı", "pages/is_programi.py"),
            ("NCR Takibi", "pages/ncr_takibi.py"),
            ("Hakediş", "pages/hakedis.py"),
        ],
        "Finans & Analiz": [
            ("Gelişmiş Dashboard", "pages/gelismis_dashboard.py"),
            ("Bütçe Analizi", "pages/butce_analizi.py"),
            ("Nakit Akışı", "pages/nakit_akisi.py"),
            ("Teklif Analizi", "pages/teklif_analizi.py"),
        ],
        "Görsel & Rapor": [
            ("GIS Harita", "pages/gis_harita.py"),
            ("DWG Görüntüleyici", "pages/dwg_goruntuleyici.py"),
            ("Rapor Al", "pages/rapor_al.py"),
        ],
        "Sistem": [
            ("Profil", "pages/profil.py"),
            ("Ayarlar", "pages/ayarlar.py"),
            ("Yardım", "pages/yardim.py"),
        ]
    }

    # Navbar Layout Yapısı
    cols = st.columns([2, 9, 1], vertical_alignment="center")
    
    # Sol: Logo (80px)
    with cols[0]:
        logo_b64 = get_logo_base64()
        if logo_b64:
            st.markdown(f'<img src="data:image/png;base64,{logo_b64}" style="height: 80px; width: auto; display: block;">', unsafe_allow_html=True)
        else:
            st.markdown('<span style="font-size: 2rem; font-weight: 800; color: #fff;">SARCON</span>', unsafe_allow_html=True)

    # Orta: Menü Elemanları
    with cols[1]:
        nav_cols = st.columns(6)
        
        # Ana Sayfa Butonu
        with nav_cols[0]:
            if st.button("Ana Sayfa", key="btn_home", use_container_width=True):
                st.switch_page("pages/dashboard.py")
        
        # Dropdown Menüler
        for idx, (group_title, items) in enumerate(menu_groups.items(), start=1):
            with nav_cols[idx]:
                with st.popover(f"{group_title} ▾", use_container_width=True):
                    for label, page_path in items:
                        if st.button(label, key=f"btn_{page_path}", use_container_width=True):
                            st.switch_page(page_path)

    # Sağ: Versiyon
    with cols[2]:
        st.markdown('<div style="text-align: right; color: #555; font-size: 0.75rem;">v1.0.0</div>', unsafe_allow_html=True)

    st.divider()