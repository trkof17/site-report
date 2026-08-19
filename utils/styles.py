import streamlit as st

def apply_global_styles(is_login=False):
    """Sistem genelindeki stil ve sidebar gizleme CSS kurallarını uygular."""
    hide_sidebar_css = """
    <style>
        [data-testid="stSidebar"], section[data-testid="stSidebar"] {
            display: none !important;
            width: 0px !important;
        }
        [data-testid="collapsedControl"], button[kind="header"] {
            display: none !important;
        }
        .main .block-container {
            max-width: 1200px;
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }
        .stApp {
            background-color: #0a0a0a !important;
        }
        .stTextInput > div > div > input {
            background-color: #1a1a1a !important;
            color: #ffffff !important;
            border: 1px solid #333333 !important;
            border-radius: 8px !important;
        }
        .stSelectbox > div > div > select {
            background-color: #1a1a1a !important;
            color: #ffffff !important;
            border: 1px solid #333333 !important;
            border-radius: 8px !important;
        }
        .stDateInput > div > div > input {
            background-color: #1a1a1a !important;
            color: #ffffff !important;
            border: 1px solid #333333 !important;
            border-radius: 8px !important;
        }
        .stNumberInput > div > div > input {
            background-color: #1a1a1a !important;
            color: #ffffff !important;
            border: 1px solid #333333 !important;
            border-radius: 8px !important;
        }
        .stDataFrame {
            background-color: #0a0a0a !important;
        }
        .stDataFrame thead tr th {
            background-color: #1a1a1a !important;
            color: #ffffff !important;
        }
        .stDataFrame tbody tr td {
            background-color: #0a0a0a !important;
            color: #ffffff !important;
            border-bottom: 1px solid #1a1a1a !important;
        }
        div.stButton > button {
            background-color: #000000 !important;
            color: #ffffff !important;
            border: 1px solid #333333 !important;
            border-radius: 6px !important;
            font-weight: 500 !important;
            font-size: 0.8rem !important;
            transition: all 0.3s ease !important;
            cursor: pointer !important;
        }
        div.stButton > button:hover {
            background-color: #1a1a1a !important;
            border-color: #555555 !important;
        }
    </style>
    """
    st.markdown(hide_sidebar_css, unsafe_allow_html=True)


def render_top_navbar():
    """Üst navigasyon header - ÇIKIŞ SAĞ ÜSTE"""
    from utils.auth import sign_out
    
    col_left, col_spacer, col_right = st.columns([3, 1, 0.8])
    
    with col_left:
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
        with col_btn1:
            if st.button("Özet", key="nav_dash", use_container_width=True):
                st.switch_page("pages/dashboard.py")
        with col_btn2:
            if st.button("Veri Girişi", key="nav_data", use_container_width=True):
                st.switch_page("pages/veri_girisi.py")
        with col_btn3:
            if st.button("Rapor Al", key="nav_report", use_container_width=True):
                st.switch_page("pages/rapor_al.py")
    
    with col_right:
        if st.button("Çıkış", key="nav_logout", use_container_width=True):
            sign_out()
            st.rerun()
    
    st.markdown("<hr style='border-color: #262626; margin-top: 0.5rem; margin-bottom: 1.5rem;'>", unsafe_allow_html=True)
