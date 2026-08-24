# -*- coding: utf-8 -*-

import os
import datetime
import pandas as pd
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

# .env dosyasını yükle (local için)
load_dotenv()

@st.cache_resource
def init_supabase() -> Client:
    """Supabase client'ı başlat (önce Secrets, sonra .env)"""
    
    # 1. YÖNTEM: Streamlit Cloud Secrets (öncelikli)
    try:
        if 'supabase' in st.secrets:
            url = st.secrets['supabase']['url']
            key = st.secrets['supabase']['anon_key']
            if url and key:
                print("✅ Supabase bağlantısı Secrets'tan başarıyla kuruldu!")
                return create_client(url, key)
    except Exception as e:
        pass  # Secrets yoksa devam et
    
    # 2. YÖNTEM: .env dosyası (local)
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    
    if url and key:
        print("✅ Supabase bağlantısı .env'den başarıyla kuruldu!")
        return create_client(url, key)
    
    # Hiçbir yerde bulunamazsa hata göster
    st.error(
        "⚠️ Supabase bağlantı bilgileri bulunamadı!\n\n"
        "Cloud'da: Streamlit Secrets'a `supabase` bilgilerini ekleyin.\n"
        "Local'de: `.env` dosyasını kontrol edin."
    )
    st.stop()

supabase = init_supabase()

# ==========================================
# 1. OKUMA FONKSİYONLARI (CACHED)
# ==========================================

@st.cache_data(ttl=600, show_spinner="Projeler yükleniyor...")
# utils/db.py - Yeni fonksiyon ekle

def get_daily_report_items(project_id, start_date=None, end_date=None):
    """Belirli tarih aralığındaki günlük raporları getir"""
    try:
        query = supabase.table("daily_reports").select("*").eq("project_id", project_id)
        
        if start_date:
            query = query.gte("report_date", start_date)
        if end_date:
            query = query.lte("report_date", end_date)
            
        response = query.execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Günlük raporlar getirilirken hata: {str(e)}")
        return []

def get_total_completed_quantities(project_id):
    """Tüm günlük raporlardan toplam yapilan is miktarlarini hesapla"""
    try:
        reports = get_daily_report_items(project_id)
        completed_qty = {}
        
        for report in reports:
            if "items" in report and isinstance(report["items"], list):
                for item in report["items"]:
                    item_name = item.get("item_name", "")
                    qty = float(item.get("quantity", 0))
                    if item_name:
                        completed_qty[item_name] = completed_qty.get(item_name, 0) + qty
        
        return completed_qty
    except Exception as e:
        st.error(f"Yapilan is miktarlari hesaplanirken hata: {str(e)}")
        return {}

def save_daily_report(project_id, items, report_date=None):
    """Günlük rapor kaydet"""
    try:
        if not report_date:
            report_date = datetime.now().date().isoformat()
            
        data = {
            "project_id": project_id,
            "report_date": report_date,
            "items": items
        }
        
        # Aynı tarihte rapor varsa güncelle
        existing = supabase.table("daily_reports").select("*")\
            .eq("project_id", project_id)\
            .eq("report_date", report_date)\
            .execute()
        
        if existing.data:
            response = supabase.table("daily_reports")\
                .update(data)\
                .eq("id", existing.data[0]["id"])\
                .execute()
        else:
            response = supabase.table("daily_reports").insert(data).execute()
            
        return bool(response.data)
    except Exception as e:
        st.error(f"Günlük rapor kaydedilirken hata: {str(e)}")
        return False
def get_user_projects():
    try:
        response = (
            supabase.table("projects")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return response.data, None
    except Exception as e:
        return None, str(e)

@st.cache_data(ttl=300, show_spinner="Raporlar analiz ediliyor...")
def get_project_reports(project_id: int):
    try:
        response = (
            supabase.table("daily_reports")
            .select("*")
            .eq("project_id", project_id)
            .execute()
        )
        return response.data, None
    except Exception as e:
        return None, str(e)

@st.cache_data(ttl=300)
def get_work_progress_by_date(project_id: int, report_date: datetime.date):
    try:
        date_str = (
            report_date.strftime("%Y-%m-%d")
            if isinstance(report_date, (datetime.date, datetime.datetime))
            else str(report_date)
        )
        response = (
            supabase.table("daily_work_progress")
            .select("*")
            .eq("project_id", project_id)
            .eq("report_date", date_str)
            .execute()
        )
        return response.data, None
    except Exception as e:
        return None, str(e)

def get_previous_day_value(
    project_id: int, current_date: datetime.date, resource_type: str, item_name: str
) -> float:
    try:
        prev_date = current_date - datetime.timedelta(days=1)
        prev_date_str = prev_date.strftime("%Y-%m-%d")

        response = (
            supabase.table("daily_resources")
            .select("value")
            .eq("project_id", project_id)
            .eq("report_date", prev_date_str)
            .eq("category", resource_type)
            .eq("item_name", item_name)
            .execute()
        )

        if response.data and len(response.data) > 0:
            return response.data[0].get("value", 0)
        return 0
    except Exception:
        return 0

def get_previous_day_progress(
    project_id: int, current_date: datetime.date, row_data: dict
) -> dict:
    try:
        prev_date = current_date - datetime.timedelta(days=1)
        prev_date_str = prev_date.strftime("%Y-%m-%d")

        query = (
            supabase.table("daily_work_progress")
            .select("ilerleme_yuzdesi")
            .eq("project_id", project_id)
            .eq("report_date", prev_date_str)
            .eq("yapilan_is", row_data.get("yapilan_is", ""))
        )

        if row_data.get("bolge"):
            query = query.eq("bolge", row_data["bolge"])
        if row_data.get("blok"):
            query = query.eq("blok", row_data["blok"])

        response = query.execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return {"ilerleme_yuzdesi": 0}
    except Exception:
        return {"ilerleme_yuzdesi": 0}

# ==========================================
# 2. YAZMA/GÜNCELLEME FONKSİYONLARI
# ==========================================

def create_project(project_name: str, start_date: str, end_date: str):
    try:
        payload = {
            "project_name": project_name,
            "start_date": start_date,
            "end_date": end_date,
        }
        res = supabase.table("projects").insert(payload).execute()
        get_user_projects.clear()
        return res.data, None
    except Exception as e:
        return None, str(e)

def save_daily_resources(
    project_id: int,
    report_date: datetime.date,
    resource_type: str,
    resource_data: dict,
):
    try:
        date_str = report_date.strftime("%Y-%m-%d")

        # Önce eski kayıtları sil (detaylı versiyon için)
        (
            supabase.table("daily_resources")
            .delete()
            .eq("project_id", project_id)
            .eq("report_date", date_str)
            .eq("category", resource_type)
            .execute()
        )

        insert_payload = []
        for item, data in resource_data.items():
            # Eğer data dict ise (yeni format)
            if isinstance(data, dict):
                insert_payload.append(
                    {
                        "project_id": project_id,
                        "report_date": date_str,
                        "category": resource_type,
                        "item_name": item,
                        "value": data.get("miktar", 0),
                        "birim": data.get("birim", ""),
                        "is_turu": data.get("is_turu", ""),
                        "wbs_kodu": data.get("wbs_kodu", ""),
                        "birim_fiyat": data.get("birim_fiyat", 0),
                        "toplam_maliyet": data.get("toplam_maliyet", 0),
                        "notlar": data.get("notlar", "")
                    }
                )
            else:
                # Eski format (sadece miktar)
                insert_payload.append(
                    {
                        "project_id": project_id,
                        "report_date": date_str,
                        "category": resource_type,
                        "item_name": item,
                        "value": data,
                        "birim": "",
                        "is_turu": "",
                        "wbs_kodu": "",
                        "birim_fiyat": 0,
                        "toplam_maliyet": 0,
                        "notlar": ""
                    }
                )

        if insert_payload:
            supabase.table("daily_resources").insert(insert_payload).execute()

        get_project_reports.clear()
        return True, None
    except Exception as e:
        return False, str(e)

def save_work_progress(project_id: int, report_date: datetime.date, rows: list):
    try:
        date_str = report_date.strftime("%Y-%m-%d")

        (
            supabase.table("daily_work_progress")
            .delete()
            .eq("project_id", project_id)
            .eq("report_date", date_str)
            .execute()
        )

        if rows:
            for r in rows:
                r["project_id"] = project_id
                r["report_date"] = date_str
                r.pop("id", None)

            supabase.table("daily_work_progress").insert(rows).execute()

        get_work_progress_by_date.clear()
        get_project_reports.clear()
        return True, None
    except Exception as e:
        return False, str(e)

def add_lead(email, company, phone, project_id, error_count, total_manhours):
    try:
        payload = {
            "email": email,
            "company": company,
            "phone": phone,
            "project_id": project_id,
            "error_count": error_count,
            "total_manhours": total_manhours,
            "status": "new"
        }
        res = supabase.table("leads").insert(payload).execute()
        return res.data, None
    except Exception as e:
        return None, str(e)

# ==========================================
# 3. AKSİYON LİSTESİ FONKSİYONLARI (GÜNCELLENDİ)
# ==========================================

@st.cache_data(ttl=300, show_spinner="Aksiyonlar yükleniyor...")
def get_actions(project_id=None):
    """Aksiyon listesini getir"""
    try:
        query = supabase.table("actions").select("*")
        if project_id:
            query = query.eq("project_id", str(project_id))
        response = query.order("created_at", desc=True).execute()
        return response.data, None
    except Exception as e:
        return None, str(e)

def create_action(action_data: dict):
    """Yeni aksiyon oluştur"""
    try:
        response = supabase.table("actions").insert(action_data).execute()
        get_actions.clear()  # Cache temizle
        return response.data, None
    except Exception as e:
        return None, str(e)

def update_action(action_id: int, update_data: dict):
    """Aksiyon güncelle"""
    try:
        response = supabase.table("actions").update(update_data).eq("id", action_id).execute()
        get_actions.clear()
        return response.data, None
    except Exception as e:
        return None, str(e)

def delete_action(action_id: int):
    """Aksiyon sil"""
    try:
        response = supabase.table("actions").delete().eq("id", action_id).execute()
        get_actions.clear()
        return response.data, None
    except Exception as e:
        return None, str(e)

def get_action_stats(project_id=None):
    """Aksiyon istatistikleri"""
    try:
        data, err = get_actions(project_id)
        if err:
            return None, err
        
        if not data:
            return {
                "total": 0,
                "open": 0,
                "completed": 0,
                "rejected": 0,
                "high_priority": 0
            }, None
        
        df = pd.DataFrame(data)
        stats = {
            "total": len(df),
            "open": len(df[df['status'].isin(['Açık', 'Devam Ediyor'])]),
            "completed": len(df[df['status'] == 'Tamamlandı']),
            "rejected": len(df[df['status'] == 'Reddedildi']),
            "high_priority": len(df[df['priority'] == 'Yüksek'])
        }
        return stats, None
    except Exception as e:
        return None, str(e)

def export_actions_to_excel(actions_data, filename="aksiyon_listesi.xlsx"):
    """Aksiyonları Excel'e aktar"""
    try:
        df = pd.DataFrame(actions_data)
        
        # Sadece istenen kolonları seç
        columns = [
            'id', 'created_by', 'assigned_to', 'title', 'work_type', 
            'description', 'project', 'created_date', 'updated_date', 
            'status', 'priority'
        ]
        
        # Mevcut kolonları filtrele
        available_cols = [col for col in columns if col in df.columns]
        df_export = df[available_cols].copy()
        
        # Kolon adlarını Türkçeleştir
        column_names = {
            'id': 'ID',
            'created_by': 'Oluşturan',
            'assigned_to': 'Atanan',
            'title': 'Konu',
            'work_type': 'İş Türü',
            'description': 'Açıklama',
            'project': 'Proje',
            'created_date': 'Oluşturma Tarihi',
            'updated_date': 'Güncelleme Tarihi',
            'status': 'Durum',
            'priority': 'Öncelik'
        }
        
        df_export = df_export.rename(columns=column_names)
        
        # Excel'e yaz
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df_export.to_excel(writer, sheet_name='Aksiyonlar', index=False)
            
            # Sütun genişliklerini otomatik ayarla
            worksheet = writer.sheets['Aksiyonlar']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        return True, filename
    except Exception as e:
        return False, str(e)

def import_actions_from_excel(file, project_id, project_name):
    """Excel'den aksiyon içe aktar"""
    try:
        df = pd.read_excel(file, engine='openpyxl')
        
        # Kolon eşleştirme
        column_map = {
            'Oluşturan': 'created_by',
            'Atanan': 'assigned_to',
            'Konu': 'title',
            'İş Türü': 'work_type',
            'Açıklama': 'description',
            'Proje': 'project',
            'Oluşturma Tarihi': 'created_date',
            'Güncelleme Tarihi': 'updated_date',
            'Durum': 'status',
            'Öncelik': 'priority'
        }
        
        # Excel'deki kolonları kontrol et
        missing_cols = []
        for excel_col in column_map.keys():
            if excel_col not in df.columns:
                missing_cols.append(excel_col)
        
        if missing_cols:
            return False, f"Eksik kolonlar: {', '.join(missing_cols)}"
        
        # DataFrame'i dönüştür
        success_count = 0
        error_count = 0
        
        for _, row in df.iterrows():
            try:
                action_data = {
                    "project_id": str(project_id),
                    "project": project_name,
                    "created_by": str(row.get('Oluşturan', 'Sistem')),
                    "assigned_to": str(row.get('Atanan', '')),
                    "title": str(row.get('Konu', '')),
                    "work_type": str(row.get('İş Türü', 'Genel')),
                    "description": str(row.get('Açıklama', '')),
                    "status": str(row.get('Durum', 'Açık')),
                    "priority": str(row.get('Öncelik', 'Orta')),
                    "created_date": str(row.get('Oluşturma Tarihi', datetime.date.today())),
                    "updated_date": str(row.get('Güncelleme Tarihi', datetime.date.today()))
                }
                
                # Status ve Priority validasyonu
                valid_status = ['Açık', 'Devam Ediyor', 'Tamamlandı', 'Reddedildi']
                valid_priority = ['Yüksek', 'Orta', 'Düşük']
                
                if action_data['status'] not in valid_status:
                    action_data['status'] = 'Açık'
                if action_data['priority'] not in valid_priority:
                    action_data['priority'] = 'Orta'
                
                result, err = create_action(action_data)
                if result:
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                error_count += 1
        
        return True, f"{success_count} başarılı, {error_count} hata"
    except Exception as e:
        return False, str(e)

# ==========================================
# 4. DİĞER HARCAMALAR FONKSİYONLARI (YENİ)
# ==========================================

def save_other_expense(expense_data: dict):
    """Diğer harcamaları kaydet"""
    try:
        response = supabase.table("other_expenses").insert(expense_data).execute()
        return True, None
    except Exception as e:
        return False, str(e)

def get_other_expenses(project_id: int, date: datetime.date):
    """Belirli tarihteki diğer harcamaları getir"""
    try:
        date_str = date.strftime("%Y-%m-%d")
        response = (
            supabase.table("other_expenses")
            .select("*")
            .eq("project_id", project_id)
            .eq("tarih", date_str)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data, None
    except Exception as e:
        return [], str(e)

def get_resource_summary(project_id: int, start_date: datetime.date, end_date: datetime.date):
    """Belirli dönemdeki kaynak özetini getir"""
    try:
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        response = (
            supabase.table("daily_resources")
            .select("*")
            .eq("project_id", project_id)
            .gte("report_date", start_str)
            .lte("report_date", end_str)
            .execute()
        )
        
        if not response.data:
            return [], None
            
        # Veriyi özetle
        df = pd.DataFrame(response.data)
        
        # İş türü bazlı adam-saat hesapla (personel için)
        personel_data = df[df['category'].isin(['Endirekt Personel', 'Direkt Personel'])]
        summary = []
        
        if not personel_data.empty:
            # İş türü bazlı gruplama
            if 'is_turu' in personel_data.columns:
                grouped = personel_data.groupby(['is_turu', 'item_name']).agg({
                    'value': 'sum',
                    'toplam_maliyet': 'sum'
                }).reset_index()
                
                for _, row in grouped.iterrows():
                    summary.append({
                        'is_turu': row['is_turu'] if row['is_turu'] else 'Genel',
                        'personel': row['item_name'],
                        'toplam_gun': row['value'],
                        'toplam_maliyet': row['toplam_maliyet']
                    })
        
        return summary, None
    except Exception as e:
        return [], str(e)