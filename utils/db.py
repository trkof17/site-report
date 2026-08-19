import os
import datetime
import pandas as pd
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

# Windows kaçış karakteri (\t, \s vb.) çökmesini önlemek için düz bölü (/) kullanıyoruz:
ENV_PATH = "C:/Users/taric/Desktop/saascon/site-report/.env"

# .env dosyasını zorla ve ezerek yükle
load_dotenv(dotenv_path=ENV_PATH, override=True)


@st.cache_resource
def init_supabase() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    # .env içinde bulunamazsa Streamlit Secrets alanını kontrol et
    if not url or not key:
        try:
            url = url or st.secrets.get("SUPABASE_URL")
            key = key or st.secrets.get("SUPABASE_ANON_KEY")
        except Exception:
            pass

    if not url or not key:
        st.error(
            f"Supabase bağlantı bilgileri bulunamadı!\n\n"
            f"Aranan .env Konumu: {ENV_PATH}\n\n"
            f"Lütfen bu konumda .env dosyasının bulunduğundan ve içerisinde "
            f"SUPABASE_URL ile SUPABASE_ANON_KEY değerlerinin yer aldığından emin olun."
        )
        st.stop()

    return create_client(url, key)


supabase = init_supabase()


# ==========================================
# 1. OKUMA FONKSİYONLARI (CACHED)
# ==========================================

@st.cache_data(ttl=600, show_spinner="Projeler yükleniyor...")
def get_user_projects():
    """Kullanıcıya ait projeleri getirir (10 dakika önbellek)."""
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
    """Seçilen projenin raporlarını getirir (5 dakika önbellek)."""
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
    """Belirli bir tarihteki iş ilerleme kayıtlarını getirir."""
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
    """Bir önceki güne ait kaynak miktarını sorgular."""
    try:
        prev_date = current_date - datetime.timedelta(days=1)
        prev_date_str = prev_date.strftime("%Y-%m-%d")

        response = (
            supabase.table("daily_resources")
            .select("value")
            .eq("project_id", project_id)
            .eq("report_date", prev_date_str)
            .eq("category", resource_type)  # DÜZELTİLDİ: resource_type → category
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
    """Aynı mahal/iş türü için bir önceki gündeki ilerlemeyi sorgular."""
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
# 2. YAZMA/GÜNCELLEME FONKSİYONLARI (CACHE CLEARING)
# ==========================================

def create_project(project_name: str, start_date: str, end_date: str):
    """Yeni proje ekler ve projeler önbelleğini temizler."""
    try:
        payload = {
            "project_name": project_name,
            "start_date": start_date,
            "end_date": end_date,
        }
        res = supabase.table("projects").insert(payload).execute()

        # Proje önbelleğini temizle (Yeni proje hemen görünsün)
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
    """Günlük kaynak verilerini (Endirekt, Direkt, Makine vb.) kaydeder veya günceller."""
    try:
        date_str = report_date.strftime("%Y-%m-%d")

        # Mevcut kayıtları temizle
        (
            supabase.table("daily_resources")
            .delete()
            .eq("project_id", project_id)
            .eq("report_date", date_str)
            .eq("category", resource_type)  # DÜZELTİLDİ: resource_type → category
            .execute()
        )

        insert_payload = []
        for item, qty in resource_data.items():
            insert_payload.append(
                {
                    "project_id": project_id,
                    "report_date": date_str,
                    "category": resource_type,  # DÜZELTİLDİ: resource_type → category
                    "item_name": item,
                    "value": qty,
                }
            )

        if insert_payload:
            supabase.table("daily_resources").insert(insert_payload).execute()

        # Rapor önbelleğini temizle
        get_project_reports.clear()

        return True, None
    except Exception as e:
        return False, str(e)


def save_work_progress(project_id: int, report_date: datetime.date, rows: list):
    """Günlük iş ilerleme verilerini kaydeder."""
    try:
        date_str = report_date.strftime("%Y-%m-%d")

        # O günkü eski verileri temizle
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
                # Beklenmeyen geçici sütunları temizle
                r.pop("id", None)

            supabase.table("daily_work_progress").insert(rows).execute()

        # İlgili sorgu önbelleklerini temizle
        get_work_progress_by_date.clear()
        get_project_reports.clear()

        return True, None
    except Exception as e:
        return False, str(e)


def add_lead(email, company, phone, project_id, error_count, total_manhours):
    """Yeni lead (müşteri adayı) ekler."""
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
