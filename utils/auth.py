import streamlit as st
from utils.supabase_client import get_supabase
import re

def sign_up(email, password):
    try:
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return None, "Geçersiz e-posta formatı"
        if len(password) < 6:
            return None, "Şifre en az 6 karakter olmalı"
        supabase = get_supabase()
        response = supabase.auth.sign_up({"email": email, "password": password})
        if response.user:
            return response.user, None
        return None, "Kayıt başarısız"
    except Exception as e:
        return None, str(e)

def sign_in(email, password):
    try:
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return None, "Geçersiz e-posta formatı"
        supabase = get_supabase()
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if response.user:
            return response.user, None
        return None, "Giriş başarısız"
    except Exception as e:
        return None, str(e)

def sign_out():
    """Çıkış yap ve session'ı temizle - KESİN ÇÖZÜM"""
    try:
        supabase = get_supabase()
        supabase.auth.sign_out()
    except:
        pass
    
    # Session'ı temizle
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    st.rerun()

def get_current_user():
    try:
        supabase = get_supabase()
        user = supabase.auth.get_user()
        if user and user.user:
            return user.user
        return None
    except:
        return None
