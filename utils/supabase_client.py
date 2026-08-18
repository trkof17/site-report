# -*- coding: utf-8 -*-
"""
Created on Wed Aug 12 04:38:36 2026

@author: taric
"""

from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_ANON_KEY

def get_supabase() -> Client:
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise ValueError("SUPABASE_URL ve SUPABASE_ANON_KEY .env'de tanımlı değil!")
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

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