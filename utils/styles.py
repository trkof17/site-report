import streamlit as st
from utils.animations import apply_animations  
def apply_global_styles(is_login=False):
    """Sistem genelindeki stil CSS kurallarını uygular."""
    hide_sidebar_css = """
    <style>
        /* Ana içerik düzeni */
        .stApp {
            background-color: #0a0a0a !important;
        }
        
        /* Streamlit varsayılan menüsünü gizle */
        #MainMenu { visibility: hidden !important; }
        header { visibility: hidden !important; }
        footer { visibility: hidden !important; }
        .stDeployButton { display: none !important; }
        .stApp > header { display: none !important; }
        
        /* ========================================== */
        /* INPUT ALANLARI */
        /* ========================================== */
        .stTextInput > div > div > input {
            background-color: #1a1a1a !important;
            color: #ffffff !important;
            border: 1px solid #333333 !important;
            border-radius: 8px !important;
        }
        .stTextInput > div > div > input:focus {
            border-color: #555555 !important;
            box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.05) !important;
        }
        .stTextInput > label {
            color: #ffffff !important;
            font-weight: 500 !important;
        }
        
        /* ========================================== */
        /* BUTONLAR */
        /* ========================================== */
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
        
        /* ========================================== */
        /* TABS - Giriş Yap / Kayıt Ol */
        /* ========================================== */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
            background-color: #1a1a1a;
            border-radius: 8px;
            padding: 4px;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 6px;
            padding: 8px 16px;
            color: #a3a3a3 !important;
            font-weight: 500;
            transition: all 0.2s ease;
            background-color: transparent !important;
        }
        .stTabs [data-baseweb="tab"]:hover {
            color: #ffffff !important;
            background-color: #2a2a2a !important;
        }
        .stTabs [aria-selected="true"] {
            background-color: #000000 !important;
            color: #ffffff !important;
        }
        .stTabs [data-baseweb="tab-panel"] {
            background-color: #0a0a0a !important;
            padding: 1rem 0 !important;
        }
        .stTabs [role="tabpanel"] {
            background-color: #0a0a0a !important;
        }
        .stTabs div {
            background-color: #0a0a0a !important;
        }
        
        /* ========================================== */
        /* ALERT MESAJLARI */
        /* ========================================== */
        .stAlert {
            border-radius: 6px !important;
            background-color: #1a1a1a !important;
            border-left: 4px solid #555555 !important;
        }
        .stAlert > div {
            color: #ffffff !important;
        }
        
        /* ========================================== */
        /* TABLO */
        /* ========================================== */
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
        
        /* ========================================== */
        /* SCROLLBAR */
        /* ========================================== */
        ::-webkit-scrollbar {
            width: 4px;
            height: 4px;
        }
        ::-webkit-scrollbar-track {
            background: #0a0a0a;
        }
        ::-webkit-scrollbar-thumb {
            background: #555555;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #777777;
        }
    """
    
    # Login sayfasında sidebar'ı gizle
    if is_login:
        hide_sidebar_css += """
        [data-testid="stSidebar"] {
            display: none !important;
            width: 0px !important;
        }
        """
    
    hide_sidebar_css += """
    </style>
    """
    st.markdown(hide_sidebar_css, unsafe_allow_html=True)
    
    apply_animations()