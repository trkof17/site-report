import streamlit as st

def render_custom_sidebar():
    """
    Streamlit'in sidebar'ını kullanarak özel menü oluşturur.
    Streamlit otomatik menüsü gizlenir, sadece özel menü gösterilir.
    """
    from utils.auth import sign_out

    # Streamlit sidebar'ını kullan
    with st.sidebar:
        # Streamlit otomatik navigasyon menüsünü gizle
        st.markdown("""
        <style>
            /* Streamlit otomatik navigasyon menüsünü gizle */
            section[data-testid="stSidebar"] nav {
                display: none !important;
            }
            section[data-testid="stSidebar"] ul {
                display: none !important;
            }
            section[data-testid="stSidebar"] .st-emotion-cache-1v0mbdj {
                display: none !important;
            }
            section[data-testid="stSidebar"] .st-emotion-cache-6qob1r {
                display: none !important;
            }
            section[data-testid="stSidebar"] .st-emotion-cache-1h9usl1 {
                display: none !important;
            }
            /* Sidebar genişliği ve arkaplan */
            [data-testid="stSidebar"] {
                width: 250px !important;
                min-width: 250px !important;
                max-width: 250px !important;
                background-color: #0a0a0a !important;
                border-right: 1px solid #1a1a1a !important;
            }
            [data-testid="stSidebar"] .css-1d391kg {
                padding: 1rem 0.75rem !important;
            }
            /* Sidebar'daki özel butonlar */
            [data-testid="stSidebar"] div.stButton > button {
                background-color: transparent !important;
                color: #d4d4d4 !important;
                border: none !important;
                border-radius: 6px !important;
                text-align: left !important;
                padding: 0.6rem 0.75rem !important;
                font-weight: 400 !important;
                font-size: 0.85rem !important;
                transition: all 0.15s ease !important;
                width: 100% !important;
                justify-content: flex-start !important;
            }
            [data-testid="stSidebar"] div.stButton > button:hover {
                background-color: #1a1a1a !important;
                color: #ffffff !important;
            }
            /* Sidebar başlıkları */
            [data-testid="stSidebar"] .stMarkdown h3 {
                color: #a3a3a3 !important;
                font-size: 0.7rem !important;
                text-transform: uppercase !important;
                letter-spacing: 0.5px !important;
                padding: 0.5rem 0.75rem !important;
                margin: 0 !important;
            }
            /* Sidebar ayraç */
            [data-testid="stSidebar"] hr {
                border-color: #1a1a1a !important;
                margin: 0.75rem 0 !important;
            }
            /* Kullanıcı bilgisi */
            .user-info {
                color: #737373;
                font-size: 0.8rem;
                padding: 0.5rem 0.75rem;
            }
        </style>
        """, unsafe_allow_html=True)

        # Başlık
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0; border-bottom: 1px solid #262626; margin-bottom: 1rem;">
            <h3 style="color: #ffffff; margin: 0;">🏗️ SARCON</h3>
            <p style="color: #737373; font-size: 0.8rem; margin: 0;">Portal</p>
        </div>
        """, unsafe_allow_html=True)

        # Menü kategorileri
        menu_sections = [
            {"category": "Ana", "items": [{"label": "📊 Özet", "page": "pages/dashboard.py"}, {"label": "📝 Veri Girişi", "page": "pages/veri_girisi.py"}]},
            {"category": "Proje", "items": [{"label": "📐 Keşif", "page": "pages/kesif_girisi.py"}, {"label": "💰 Maliyet", "page": "pages/maliyet_girisi.py"}, {"label": "📊 Bütçe", "page": "pages/butce_analizi.py"}, {"label": "📄 Hakediş", "page": "pages/hakedis.py"}]},
            {"category": "Analiz", "items": [{"label": "📊 Gelişmiş", "page": "pages/gelismis_dashboard.py"}, {"label": "📅 İş Programı", "page": "pages/is_programi.py"}, {"label": "💰 Nakit Akışı", "page": "pages/nakit_akisi.py"}]},
            {"category": "Doküman", "items": [{"label": "📄 Rapor Al", "page": "pages/rapor_al.py"}, {"label": "📋 Sözleşme", "page": "pages/sozlesme_yonetimi.py"}, {"label": "📐 DWG", "page": "pages/dwg_goruntuleyici.py"}, {"label": "📊 Teklif", "page": "pages/teklif_analizi.py"}]},
            {"category": "Takip", "items": [{"label": "⚠️ NCR", "page": "pages/ncr_takibi.py"}, {"label": "🗺️ Harita", "page": "pages/gis_harita.py"}]},
            {"category": "Hesap", "items": [{"label": "⚙️ Ayarlar", "page": "pages/ayarlar.py"}]}
        ]

        for section in menu_sections:
            st.markdown(f"### {section['category']}")
            for item in section["items"]:
                if st.button(item["label"], key=f"nav_{item['page']}", use_container_width=True):
                    try:
                        st.switch_page(item["page"])
                    except:
                        st.error(f"Sayfa bulunamadı: {item['page']}")

        st.markdown("---")
        user_email = st.session_state.user.email if 'user' in st.session_state and st.session_state.user else 'Misafir'
        st.markdown(f'<div class="user-info">👤 {user_email}</div>', unsafe_allow_html=True)

        if st.button("🚪 Çıkış", key="logout_btn", use_container_width=True):
            sign_out()
            st.rerun()