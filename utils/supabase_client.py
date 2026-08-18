# -*- coding: utf-8 -*-
"""
Created on Wed Aug 12 04:38:36 2026
@author: taric
"""

from supabase import create_client, Client
import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

def get_supabase() -> Client:
    """Supabase client'ı döndür (önce Secrets, sonra .env)"""
    
    # 1. YÖNTEM: Streamlit Cloud Secrets
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

def test_connection():
    try:
        supabase = get_supabase()
        response = supabase.table("projects").select("*").limit(1).execute()
        print("✅ Supabase bağlantısı başarılı!")
        print("📊 Tablo durumu:", response.data)
        return True
    except Exception as e:
        print("❌ Bağlantı hatası:", str(e))
        return False
