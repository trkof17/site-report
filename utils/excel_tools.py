import pandas as pd
import io
import datetime
from utils.db import supabase
from utils.lists import (
    ENDIRECT_PERSONEL, DIRECT_PERSONEL, YAPI_MALZEME, DEMIRBASLAR,
    SARF_MALZEMELER, MAKINA
)

def get_excel_template():
    """Boş Excel şablonu oluştur (Kaynak türleriyle birlikte)"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        
        # 1. Günlük Raporlar şablonu
        df_reports = pd.DataFrame(columns=[
            'report_date', 'activity', 'trade', 'planned_manpower', 'actual_manpower',
            'planned_machine_hours', 'actual_machine_hours', 'planned_quantity', 
            'actual_quantity', 'cost', 'notes'
        ])
        df_reports.to_excel(writer, sheet_name='Günlük_Raporlar', index=False)
        
        # 2. Kaynaklar şablonu (TÜM KAYNAK TÜRLERİ İLE)
        df_resources = pd.DataFrame(columns=[
            'report_date', 'category', 'item_name', 'value', 'unit', 'notes'
        ])
        # Örnek veri ekle (kullanıcıya rehberlik etmek için)
        sample_data = [
            ['2026-08-20', 'Endirekt Personel', 'Proje Müdürü', 1, 'kişi', ''],
            ['2026-08-20', 'Endirekt Personel', 'İnşaat Mühendisi', 1, 'kişi', ''],
            ['2026-08-20', 'Direkt Personel', 'Usta', 3, 'kişi', ''],
            ['2026-08-20', 'Yapı Malzemesi', 'C30 B.A. Betonu', 50, 'm³', ''],
            ['2026-08-20', 'Makina', 'Ekskavatör', 1, 'adet', ''],
            ['2026-08-20', 'Makina', 'Kule Vinç', 1, 'adet', ''],
            ['2026-08-20', 'Demirbaşlar', 'Plywood', 20, 'm²', ''],
        ]
        for row in sample_data:
            df_resources.loc[len(df_resources)] = row
        df_resources.to_excel(writer, sheet_name='Kaynaklar', index=False)
        
        # Kaynak Türleri bilgi sayfası
        info_data = []
        for category, items in [
            ('Endirekt Personel', ENDIRECT_PERSONEL),
            ('Direkt Personel', DIRECT_PERSONEL),
            ('Yapı Malzemesi', YAPI_MALZEME),
            ('Demirbaşlar', DEMIRBASLAR),
            ('Sarf Malzemeler', SARF_MALZEMELER),
            ('Makina', MAKINA),
        ]:
            for item in items:
                info_data.append({'Kategori': category, 'Kaynak Adı': item})
        df_info = pd.DataFrame(info_data)
        df_info.to_excel(writer, sheet_name='Kaynak_Listesi', index=False)
        
        # 3. İş İlerleme şablonu
        df_work = pd.DataFrame(columns=[
            'report_date', 'bolge', 'blok', 'mahal', 'is_turu', 'yapilan_is',
            'birim', 'miktar', 'ilerleme_yuzdesi', 'alt_yuklenici', 'notlar'
        ])
        df_work.to_excel(writer, sheet_name='Is_İlerleme', index=False)
        
    return output.getvalue()

def export_project_data(project_id):
    """Proje verilerini Excel'e aktar"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        
        # 1. Günlük raporlar
        reports = supabase.table("daily_reports").select("*").eq("project_id", project_id).execute()
        if reports.data:
            df = pd.DataFrame(reports.data)
            df.to_excel(writer, sheet_name='Günlük_Raporlar', index=False)
        
        # 2. Kaynaklar (tüm kategoriler)
        resources = supabase.table("daily_resources").select("*").eq("project_id", project_id).execute()
        if resources.data:
            df = pd.DataFrame(resources.data)
            df.to_excel(writer, sheet_name='Kaynaklar', index=False)
        
        # 3. İş ilerleme
        work = supabase.table("daily_work_progress").select("*").eq("project_id", project_id).execute()
        if work.data:
            df = pd.DataFrame(work.data)
            df.to_excel(writer, sheet_name='Is_İlerleme', index=False)
    
    return output.getvalue()

def validate_and_import(excel_file, project_id):
    """Yüklenen Excel'i doğrula ve veritabanına aktar (Kaynak türü kontrolü ile)"""
    try:
        df_reports = pd.read_excel(excel_file, sheet_name='Günlük_Raporlar')
        df_resources = pd.read_excel(excel_file, sheet_name='Kaynaklar')
        df_work = pd.read_excel(excel_file, sheet_name='Is_İlerleme')
    except Exception as e:
        return False, f"Excel okunamadı: {str(e)}"
    
    errors = []
    
    # Günlük Raporlar validasyonu
    required_cols = ['report_date', 'activity', 'trade']
    for col in required_cols:
        if col not in df_reports.columns:
            errors.append(f"Günlük_Raporlar sayfasında '{col}' sütunu eksik")
    
    # Kaynaklar validasyonu (kategori kontrolü eklendi)
    required_cols = ['report_date', 'category', 'item_name', 'value']
    for col in required_cols:
        if col not in df_resources.columns:
            errors.append(f"Kaynaklar sayfasında '{col}' sütunu eksik")
    
    # Geçerli kategoriler
    valid_categories = ['Endirekt Personel', 'Direkt Personel', 'Yapı Malzemesi', 
                       'Demirbaşlar', 'Sarf Malzemeler', 'Makina']
    
    for idx, row in df_resources.iterrows():
        category = row.get('category', '')
        if category and category not in valid_categories:
            errors.append(f"Kaynaklar satır {idx+2}: '{category}' geçersiz kategori. Geçerli kategoriler: {', '.join(valid_categories)}")
    
    # İş İlerleme validasyonu
    required_cols = ['report_date', 'yapilan_is', 'ilerleme_yuzdesi']
    for col in required_cols:
        if col not in df_work.columns:
            errors.append(f"Is_İlerleme sayfasında '{col}' sütunu eksik")
    
    if errors:
        return False, "\n".join(errors)
    
    # Verileri temizle ve kaydet
    try:
        # Önce mevcut verileri temizle (tarih bazında)
        dates = set()
        if not df_reports.empty:
            dates.update(df_reports['report_date'].dropna().astype(str).unique())
        if not df_resources.empty:
            dates.update(df_resources['report_date'].dropna().astype(str).unique())
        if not df_work.empty:
            dates.update(df_work['report_date'].dropna().astype(str).unique())
        
        for date_str in dates:
            supabase.table("daily_reports").delete().eq("project_id", project_id).eq("report_date", date_str).execute()
            supabase.table("daily_resources").delete().eq("project_id", project_id).eq("report_date", date_str).execute()
            supabase.table("daily_work_progress").delete().eq("project_id", project_id).eq("report_date", date_str).execute()
        
        # Günlük raporları kaydet
        for _, row in df_reports.iterrows():
            if pd.notna(row.get('report_date')):
                data = {
                    "project_id": project_id,
                    "report_date": str(row['report_date']),
                    "activity": str(row.get('activity', '')),
                    "trade": str(row.get('trade', '')),
                    "planned_manpower": int(row.get('planned_manpower', 0)) if pd.notna(row.get('planned_manpower')) else 0,
                    "actual_manpower": int(row.get('actual_manpower', 0)) if pd.notna(row.get('actual_manpower')) else 0,
                    "planned_machine_hours": float(row.get('planned_machine_hours', 0)) if pd.notna(row.get('planned_machine_hours')) else 0.0,
                    "actual_machine_hours": float(row.get('actual_machine_hours', 0)) if pd.notna(row.get('actual_machine_hours')) else 0.0,
                    "planned_quantity": float(row.get('planned_quantity', 0)) if pd.notna(row.get('planned_quantity')) else 0.0,
                    "actual_quantity": float(row.get('actual_quantity', 0)) if pd.notna(row.get('actual_quantity')) else 0.0,
                    "cost": float(row.get('cost', 0)) if pd.notna(row.get('cost')) else 0.0,
                    "notes": str(row.get('notes', '')) if pd.notna(row.get('notes')) else ''
                }
                supabase.table("daily_reports").insert(data).execute()
        
        # Kaynakları kaydet
        for _, row in df_resources.iterrows():
            if pd.notna(row.get('report_date')):
                data = {
                    "project_id": project_id,
                    "report_date": str(row['report_date']),
                    "category": str(row.get('category', '')),
                    "item_name": str(row.get('item_name', '')),
                    "value": float(row.get('value', 0)) if pd.notna(row.get('value')) else 0,
                    "unit": str(row.get('unit', '')) if pd.notna(row.get('unit')) else '',
                    "notes": str(row.get('notes', '')) if pd.notna(row.get('notes')) else ''
                }
                supabase.table("daily_resources").insert(data).execute()
        
        # İş ilerleme kaydet
        for _, row in df_work.iterrows():
            if pd.notna(row.get('report_date')) and pd.notna(row.get('yapilan_is')):
                data = {
                    "project_id": project_id,
                    "report_date": str(row['report_date']),
                    "bolge": str(row.get('bolge', '')) if pd.notna(row.get('bolge')) else '',
                    "blok": str(row.get('blok', '')) if pd.notna(row.get('blok')) else '',
                    "mahal": str(row.get('mahal', '')) if pd.notna(row.get('mahal')) else '',
                    "is_turu": str(row.get('is_turu', '')) if pd.notna(row.get('is_turu')) else '',
                    "yapilan_is": str(row.get('yapilan_is', '')),
                    "birim": str(row.get('birim', '')) if pd.notna(row.get('birim')) else '',
                    "miktar": float(row.get('miktar', 0)) if pd.notna(row.get('miktar')) else 0,
                    "ilerleme_yuzdesi": float(row.get('ilerleme_yuzdesi', 0)) if pd.notna(row.get('ilerleme_yuzdesi')) else 0,
                    "alt_yuklenici": str(row.get('alt_yuklenici', '')) if pd.notna(row.get('alt_yuklenici')) else '',
                    "notlar": str(row.get('notlar', '')) if pd.notna(row.get('notlar')) else ''
                }
                supabase.table("daily_work_progress").insert(data).execute()
        
        return True, "Tüm veriler başarıyla içe aktarıldı!"
        
    except Exception as e:
        return False, f"Veri kaydedilirken hata oluştu: {str(e)}"