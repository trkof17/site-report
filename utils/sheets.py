import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st
from datetime import datetime
import json

def get_sheets_client():
    """Google Sheets istemcisini Secrets'tan oluştur"""
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    try:
        # Secrets'tan credentials'ı al
        if 'google' not in st.secrets:
            st.error("❌ Secrets'ta 'google' bölümü bulunamadı!")
            return None
        
        # JSON'ı yükle
        creds_json = st.secrets['google']['credentials']
        creds_dict = json.loads(creds_json)
        
        # DOĞRUDAN ServiceAccountCredentials ile dene
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        return client
        
    except Exception as e:
        st.error(f"Google Sheets bağlantı hatası: {str(e)}")
        return None

def append_lead(sheet_name, email, company, project_name, error_count, total_manhours):
    """Lead bilgilerini Google Sheets'e ekle"""
    try:
        client = get_sheets_client()
        if not client:
            return False
        
        # Sheets adını Secrets'tan al
        if 'google' in st.secrets and 'sheet_name' in st.secrets['google']:
            sheet_name = st.secrets['google']['sheet_name']
        
        # Sayfayı aç
        sheet = client.open(sheet_name).sheet1
        
        # Satır oluştur
        row = [
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            email,
            company,
            project_name,
            error_count,
            total_manhours,
            'Yeni'
        ]
        
        # Ekle
        sheet.append_row(row)
        st.success("✅ Lead başarıyla Google Sheets'e kaydedildi!")
        return True
    except Exception as e:
        st.error(f"Lead kaydedilemedi: {str(e)}")
        return False
