import streamlit as st
import base64
from utils.auth import sign_up, sign_in, get_current_user
from utils.styles import apply_global_styles

st.set_page_config(
    page_title="SARCON Portal | Giriş",
    page_icon="🏗️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Login teması ve sidebar gizleme uygula
apply_global_styles(is_login=True)

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
    <h2 style="color: #ffffff; font-weight: 700; margin-bottom: 2rem; letter-spacing: -0.5px;">SARCON PORTAL</h2>
    """, unsafe_allow_html=True)

# Login & Register Tabs
tab1, tab2 = st.tabs(["Giriş Yap", "Kayıt Ol"])

with tab1:
    email = st.text_input("E-posta", key="login_email", placeholder="ornek@firma.com")
    password = st.text_input("Şifre", type="password", key="login_password", placeholder="••••••••")
    
    if st.button("Giriş Yap", key="login_btn", use_container_width=True):
        if not email or not password:
            st.warning("Lütfen e-posta ve şifre alanlarını doldurun.")
        else:
            with st.spinner("Giriş yapılıyor..."):
                user, err = sign_in(email.strip(), password)
                if user:
                    st.session_state.user = user
                    st.session_state.logged_in = True
                    st.switch_page("pages/dashboard.py")
                else:
                    st.error(f"❌ {err}")

with tab2:
    email = st.text_input("E-posta", key="signup_email", placeholder="ornek@firma.com")
    password = st.text_input("Şifre", type="password", key="signup_password", placeholder="•••••••• (en az 6 karakter)")
    
    if st.button("Kayıt Ol", key="signup_btn", use_container_width=True):
        if not email or not password:
            st.warning("Lütfen e-posta ve şifre alanlarını doldurun.")
        else:
            with st.spinner("Kayıt yapılıyor..."):
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
