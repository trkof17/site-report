from supabase import create_client, Client
import os
from dotenv import load_dotenv
import streamlit as st

# .env'yi yükle (local için)
load_dotenv()

def get_supabase() -> Client:
    """Supabase istemcisini döndürür (önce secrets, sonra .env)"""
    
    # 1. YÖNTEM: Streamlit Cloud Secrets (öncelikli)
    try:
        if 'supabase' in st.secrets:
            url = st.secrets['supabase']['url']
            key = st.secrets['supabase']['anon_key']
            if url and key:
                return create_client(url, key)
    except:
        pass  # Secrets yoksa devam et
    
    # 2. YÖNTEM: .env dosyası (local)
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        raise ValueError("SUPABASE_URL ve SUPABASE_ANON_KEY bulunamadı! (Secrets veya .env'de tanımlı değil)")
    
    return create_client(url, key)
