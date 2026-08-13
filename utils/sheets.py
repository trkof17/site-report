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
        # Secrets kontrolü
        if 'google' not in st.secrets:
            st.error("❌ Secrets'ta 'google' bölümü bulunamadı!")
            st.info(f"📋 Mevcut secrets anahtarları: {list(st.secrets.keys())}")
            return None
        
        # Credentials kontrolü
        if 'credentials' not in st.secrets['google']:
            st.error("❌ 'google' bölümünde 'credentials' anahtarı bulunamadı!")
            st.info(f"📋 google içindeki anahtarlar: {list(st.secrets['google'].keys())}")
            return None
        
        # JSON'ı yükle
        creds_json = st.secrets['google']['credentials']
        st.info(f"📄 Credentials uzunluğu: {len(creds_json)} karakter")
        
        try:
            creds_dict = json.loads(creds_json)
            st.success("✅ JSON başarıyla parse edildi!")
        except json.JSONDecodeError as e:
            st.error(f"❌ JSON parse hatası: {str(e)}")
            st.code(creds_json[:500] + "...", language="json")
            return None
        
        # Bağlan
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        return client
        
    except Exception as e:
        st.error(f"Google Sheets bağlantı hatası: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
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
