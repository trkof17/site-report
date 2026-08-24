# seed.py - UNIT KOLONU KALDIRILDI VE RLS FIX

from utils.db import supabase
import uuid
from datetime import datetime, timedelta
import random
import os

# ==========================================
# TABLO İSİMLERI
# ==========================================

T_PROJECTS = "projects"
T_ITEMS = "project_items"
T_SCHEDULE = "project_schedule"
T_COSTS = "project_costs"
T_CASHFLOW = "project_cashflow"
T_RESOURCES = "daily_resources"
T_WORK = "daily_work_progress"
T_ACTIONS = "actions"

# ==========================================

def get_supabase_admin():
    """Admin yetkileri ile Supabase client oluştur"""
    try:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
        if not url or not key:
            print("UYARI: Service role key bulunamadi, normal client kullaniliyor...")
            return supabase
        admin_client = create_client(url, key)
        print("Admin client olusturuldu (RLS bypass)")
        return admin_client
    except Exception as e:
        print(f"Admin client olusturma hatasi: {e}")
        return supabase

def seed_all():
    print("Ornek Proje Seed Basliyor...")
    
    # Admin client al (RLS bypass için)
    admin_supabase = get_supabase_admin()
    
    # Proje ID olustur
    PROJECT_ID = str(uuid.uuid4())
    
    # 1. Eski verileri temizle (opsiyonel)
    print("Eski veriler temizleniyor...")
    try:
        admin_supabase.table(T_CASHFLOW).delete().eq("project_id", PROJECT_ID).execute()
        admin_supabase.table(T_COSTS).delete().eq("project_id", PROJECT_ID).execute()
        admin_supabase.table(T_SCHEDULE).delete().eq("project_id", PROJECT_ID).execute()
        admin_supabase.table(T_ITEMS).delete().eq("project_id", PROJECT_ID).execute()
        admin_supabase.table(T_RESOURCES).delete().eq("project_id", PROJECT_ID).execute()
        admin_supabase.table(T_WORK).delete().eq("project_id", PROJECT_ID).execute()
        admin_supabase.table(T_ACTIONS).delete().eq("project_id", PROJECT_ID).execute()
        admin_supabase.table(T_PROJECTS).delete().eq("id", PROJECT_ID).execute()
        print("Eski veriler temizlendi")
    except Exception as e:
        print(f"Temizlik hatasi: {e}")
    
    # 2. Proje - ORNEK PROJE
    print("Proje olusturuluyor...")
    project_data = {
        "id": PROJECT_ID,
        "project_name": "Ornek Proje",
        "start_date": "2026-08-01",
        "end_date": "2026-09-15",
        "created_at": datetime.now().isoformat()
    }
    
    try:
        admin_supabase.table(T_PROJECTS).insert(project_data).execute()
        print(f"Proje olusturuldu: Ornek Proje (ID: {PROJECT_ID})")
    except Exception as e:
        print(f"Proje hatasi: {e}")
        return
    
    # 3. Keşif Kalemleri
    print("Kesif kalemleri ekleniyor...")
    items = [
        {"project_id": PROJECT_ID, "item_code": "ORJ-01-001", "item_name": "Yikim Isleri", "category": "Kaba Isler", "unit": "m3", "quantity": 45, "unit_price": 350.00, "wbs_kodu": "ORJ-01"},
        {"project_id": PROJECT_ID, "item_code": "ORJ-01-002", "item_name": "Hafriyat ve Tasima", "category": "Kaba Isler", "unit": "m3", "quantity": 45, "unit_price": 180.00, "wbs_kodu": "ORJ-01"},
        {"project_id": PROJECT_ID, "item_code": "ORJ-02-001", "item_name": "Duvarlar", "category": "Kaba Isler", "unit": "m2", "quantity": 120, "unit_price": 520.00, "wbs_kodu": "ORJ-02"},
        {"project_id": PROJECT_ID, "item_code": "ORJ-02-002", "item_name": "Beton Siva", "category": "Kaba Isler", "unit": "m2", "quantity": 180, "unit_price": 85.00, "wbs_kodu": "ORJ-02"},
        {"project_id": PROJECT_ID, "item_code": "ORJ-02-003", "item_name": "Tesviye ve Sap", "category": "Kaba Isler", "unit": "m2", "quantity": 200, "unit_price": 115.00, "wbs_kodu": "ORJ-02"},
        {"project_id": PROJECT_ID, "item_code": "ORJ-03-001", "item_name": "Alci Siva", "category": "Ince Isler", "unit": "m2", "quantity": 180, "unit_price": 125.00, "wbs_kodu": "ORJ-03"},
        {"project_id": PROJECT_ID, "item_code": "ORJ-03-002", "item_name": "Fayans Duvar", "category": "Ince Isler", "unit": "m2", "quantity": 65, "unit_price": 420.00, "wbs_kodu": "ORJ-03"},
        {"project_id": PROJECT_ID, "item_code": "ORJ-03-003", "item_name": "Fayans Zemin", "category": "Ince Isler", "unit": "m2", "quantity": 80, "unit_price": 380.00, "wbs_kodu": "ORJ-03"},
        {"project_id": PROJECT_ID, "item_code": "ORJ-03-004", "item_name": "Boya", "category": "Ince Isler", "unit": "m2", "quantity": 180, "unit_price": 95.00, "wbs_kodu": "ORJ-03"},
        {"project_id": PROJECT_ID, "item_code": "ORJ-04-001", "item_name": "Tesisat Borulari", "category": "Mekanik", "unit": "m", "quantity": 95, "unit_price": 165.00, "wbs_kodu": "ORJ-04"},
        {"project_id": PROJECT_ID, "item_code": "ORJ-04-002", "item_name": "Armatur Montaj", "category": "Mekanik", "unit": "adet", "quantity": 12, "unit_price": 1250.00, "wbs_kodu": "ORJ-04"},
        {"project_id": PROJECT_ID, "item_code": "ORJ-05-001", "item_name": "Elektrik Tesisati", "category": "Elektrik", "unit": "m", "quantity": 120, "unit_price": 145.00, "wbs_kodu": "ORJ-05"},
        {"project_id": PROJECT_ID, "item_code": "ORJ-05-002", "item_name": "Aydinlatma Montaj", "category": "Elektrik", "unit": "adet", "quantity": 18, "unit_price": 320.00, "wbs_kodu": "ORJ-05"},
    ]
    for item in items:
        try:
            admin_supabase.table(T_ITEMS).insert(item).execute()
        except Exception as e:
            print(f"Kesif hatasi: {e}")
    print("Kesif eklendi")
    
    # 4. İş Programı
    print("Is programi ekleniyor...")
    schedule = [
        {"project_id": PROJECT_ID, "activity_code": "ORJ-S01", "activity_name": "Proje Baslangici", "level": 0, "start_date": "2026-08-01", "end_date": "2026-08-01", "duration": 1, "progress_pct": 100, "is_milestone": True},
        {"project_id": PROJECT_ID, "activity_code": "ORJ-S02", "activity_name": "Hazirlik ve Yikim", "level": 1, "start_date": "2026-08-01", "end_date": "2026-08-07", "duration": 7, "progress_pct": 100, "is_milestone": False},
        {"project_id": PROJECT_ID, "activity_code": "ORJ-S03", "activity_name": "Kaba Insaat", "level": 1, "start_date": "2026-08-08", "end_date": "2026-08-21", "duration": 14, "progress_pct": 85, "is_milestone": False},
        {"project_id": PROJECT_ID, "activity_code": "ORJ-S04", "activity_name": "Ince Isler", "level": 1, "start_date": "2026-08-22", "end_date": "2026-09-04", "duration": 14, "progress_pct": 60, "is_milestone": False},
        {"project_id": PROJECT_ID, "activity_code": "ORJ-S05", "activity_name": "Mekanik Isler", "level": 1, "start_date": "2026-08-25", "end_date": "2026-09-08", "duration": 15, "progress_pct": 45, "is_milestone": False},
        {"project_id": PROJECT_ID, "activity_code": "ORJ-S06", "activity_name": "Elektrik Isleri", "level": 1, "start_date": "2026-08-28", "end_date": "2026-09-10", "duration": 14, "progress_pct": 40, "is_milestone": False},
        {"project_id": PROJECT_ID, "activity_code": "ORJ-S07", "activity_name": "Proje Bitisi", "level": 0, "start_date": "2026-09-15", "end_date": "2026-09-15", "duration": 1, "progress_pct": 0, "is_milestone": True},
    ]
    for s in schedule:
        try:
            admin_supabase.table(T_SCHEDULE).insert(s).execute()
        except Exception as e:
            print(f"Program hatasi: {e}")
    print("Program eklendi")
    
    # 5. Maliyetler
    print("Maliyetler ekleniyor...")
    costs = [
        {"project_id": PROJECT_ID, "cost_name": "Yikim", "unit_price": 350.00, "quantity": 45, "total_price": 24750.00, "cost_category": "Isçilik", "wbs_kodu": "ORJ-01"},
        {"project_id": PROJECT_ID, "cost_name": "Hafriyat", "unit_price": 180.00, "quantity": 45, "total_price": 16200.00, "cost_category": "Nakliye", "wbs_kodu": "ORJ-01"},
        {"project_id": PROJECT_ID, "cost_name": "Duvarlar", "unit_price": 520.00, "quantity": 120, "total_price": 90000.00, "cost_category": "Malzeme", "wbs_kodu": "ORJ-02"},
        {"project_id": PROJECT_ID, "cost_name": "Beton Siva", "unit_price": 85.00, "quantity": 180, "total_price": 26100.00, "cost_category": "Isçilik", "wbs_kodu": "ORJ-02"},
        {"project_id": PROJECT_ID, "cost_name": "Tesviye", "unit_price": 115.00, "quantity": 200, "total_price": 33000.00, "cost_category": "Isçilik", "wbs_kodu": "ORJ-02"},
        {"project_id": PROJECT_ID, "cost_name": "Alci Siva", "unit_price": 125.00, "quantity": 180, "total_price": 32400.00, "cost_category": "Isçilik", "wbs_kodu": "ORJ-03"},
        {"project_id": PROJECT_ID, "cost_name": "Fayans Duvar", "unit_price": 420.00, "quantity": 65, "total_price": 38025.00, "cost_category": "Malzeme", "wbs_kodu": "ORJ-03"},
        {"project_id": PROJECT_ID, "cost_name": "Fayans Zemin", "unit_price": 380.00, "quantity": 80, "total_price": 42000.00, "cost_category": "Malzeme", "wbs_kodu": "ORJ-03"},
        {"project_id": PROJECT_ID, "cost_name": "Boya", "unit_price": 95.00, "quantity": 180, "total_price": 25740.00, "cost_category": "Malzeme", "wbs_kodu": "ORJ-03"},
        {"project_id": PROJECT_ID, "cost_name": "Tesisat Borulari", "unit_price": 165.00, "quantity": 95, "total_price": 23750.00, "cost_category": "Malzeme", "wbs_kodu": "ORJ-04"},
        {"project_id": PROJECT_ID, "cost_name": "Armatur Montaj", "unit_price": 1250.00, "quantity": 12, "total_price": 19200.00, "cost_category": "Isçilik", "wbs_kodu": "ORJ-04"},
        {"project_id": PROJECT_ID, "cost_name": "Elektrik Tesisati", "unit_price": 145.00, "quantity": 120, "total_price": 25800.00, "cost_category": "Malzeme", "wbs_kodu": "ORJ-05"},
        {"project_id": PROJECT_ID, "cost_name": "Aydinlatma", "unit_price": 320.00, "quantity": 18, "total_price": 7470.00, "cost_category": "Malzeme", "wbs_kodu": "ORJ-05"},
    ]
    for cost in costs:
        try:
            admin_supabase.table(T_COSTS).insert(cost).execute()
        except Exception as e:
            print(f"Maliyet hatasi: {e}")
    print("Maliyetler eklendi")
    
    # 6. Nakit Akışı
    print("Nakit akisi ekleniyor...")
    cashflow = [
        {"project_id": PROJECT_ID, "period_date": "2026-08-01", "planned_inflow": 200000, "actual_inflow": 180000, "planned_outflow": 150000, "actual_outflow": 165000, "net_cash": 15000, "cumulative_cash": 15000},
        {"project_id": PROJECT_ID, "period_date": "2026-08-15", "planned_inflow": 150000, "actual_inflow": 140000, "planned_outflow": 120000, "actual_outflow": 130000, "net_cash": 10000, "cumulative_cash": 25000},
        {"project_id": PROJECT_ID, "period_date": "2026-09-01", "planned_inflow": 180000, "actual_inflow": 160000, "planned_outflow": 140000, "actual_outflow": 150000, "net_cash": 10000, "cumulative_cash": 35000},
        {"project_id": PROJECT_ID, "period_date": "2026-09-15", "planned_inflow": 200000, "actual_inflow": 190000, "planned_outflow": 100000, "actual_outflow": 110000, "net_cash": 80000, "cumulative_cash": 115000},
    ]
    for cf in cashflow:
        try:
            admin_supabase.table(T_CASHFLOW).insert(cf).execute()
        except Exception as e:
            print(f"Nakit hatasi: {e}")
    print("Nakit akisi eklendi")
    
    # 7. Günlük Kaynak Verileri (UNIT kolonu kaldırıldı)
    print("Gunluk kaynak verileri ekleniyor...")
    start_date = datetime(2026, 8, 1)
    end_date = datetime(2026, 9, 10)
    
    resources = []
    current_date = start_date
    while current_date <= end_date:
        # Direkt Personel (8-12 arası)
        direct = random.randint(8, 12)
        # Endirekt Personel (3-6 arası)
        endirect = random.randint(3, 6)
        # Makina (1-3 arası)
        machine = random.randint(1, 3)
        
        # Direkt Personel
        resources.append({
            "project_id": PROJECT_ID,
            "report_date": current_date.isoformat(),
            "category": "Direkt Personel",
            "item_name": "Isci",
            "value": direct
        })
        
        # Endirekt Personel
        resources.append({
            "project_id": PROJECT_ID,
            "report_date": current_date.isoformat(),
            "category": "Endirekt Personel",
            "item_name": "Teknik Personel",
            "value": endirect
        })
        
        # Makina
        resources.append({
            "project_id": PROJECT_ID,
            "report_date": current_date.isoformat(),
            "category": "Makina",
            "item_name": "Ekskavator",
            "value": machine
        })
        
        current_date += timedelta(days=1)
    
    for res in resources:
        try:
            admin_supabase.table(T_RESOURCES).insert(res).execute()
        except Exception as e:
            print(f"Kaynak hatasi: {e}")
    print(f"Gunluk kaynak verileri eklendi ({len(resources)} kayit)")
    
    # 8. Günlük İş İlerleme Verileri
    print("Gunluk is ilerleme verileri ekleniyor...")
    work_types = ["Kazi", "Beton", "Donati", "Kalip", "Siva", "Fayans", "Boya"]
    work_items = [
        "Yikim calismalari",
        "Hafriyat tasima",
        "Doseme betonu",
        "Kolon betonu",
        "Kiris betonu",
        "Donati baglama",
        "Kalip isleri",
        "Siva isleri",
        "Fayans doseme",
        "Boya isleri",
        "Tesisat cekme",
        "Elektrik tesisati",
        "Armatur montaji",
        "Aydinlatma montaji"
    ]
    
    work_data = []
    current_date = datetime(2026, 8, 1)
    progress = 0
    
    while current_date <= datetime(2026, 9, 10):
        # Progres artışı (günlük %2-5 arası)
        progress_daily = random.uniform(2, 5)
        progress = min(progress + progress_daily, 100)
        
        # 3-5 iş kalemi ekle
        num_items = random.randint(3, 5)
        selected_items = random.sample(work_items, min(num_items, len(work_items)))
        
        for item in selected_items:
            work_data.append({
                "project_id": PROJECT_ID,
                "report_date": current_date.isoformat(),
                "is_turu": random.choice(work_types),
                "yapilan_is": item,
                "ilerleme_yuzdesi": min(progress + random.uniform(-5, 5), 100),
                "kesif_miktari": random.uniform(50, 200),
                "yapilan_miktar": random.uniform(20, 150),
                "bolge": random.choice(["Giris Kat", "1. Kat", "2. Kat", "Bodrum"])
            })
        
        current_date += timedelta(days=1)
    
    for work in work_data:
        try:
            admin_supabase.table(T_WORK).insert(work).execute()
        except Exception as e:
            print(f"Is ilerleme hatasi: {e}")
    print(f"Gunluk is ilerleme verileri eklendi ({len(work_data)} kayit)")
    
    # 9. Aksiyon Verileri (RLS bypass ile)
    print("Aksiyon verileri ekleniyor...")
    actions = [
        {
            "project_id": PROJECT_ID,
            "project": "Ornek Proje",
            "created_by": "Ahmet Yilmaz",
            "assigned_to": "Mehmet Demir",
            "title": "Saha guvenlik onlemleri alinmali",
            "work_type": "Saha Yonetimi",
            "description": "Tum saha personeli icin is guvenligi egitimi yapilacak ve kisisel koruyucu donanimlar kontrol edilecek.",
            "status": "Acik",
            "priority": "Yuksek",
            "created_date": "2026-08-01",
            "updated_date": "2026-08-01"
        },
        {
            "project_id": PROJECT_ID,
            "project": "Ornek Proje",
            "created_by": "Ayse Kaya",
            "assigned_to": "Ali Yildiz",
            "title": "Beton kalitesi kontrol edilmeli",
            "work_type": "Kalite",
            "description": "C30 beton numuneleri alinacak ve laboratuvara gonderilecek.",
            "status": "Devam Ediyor",
            "priority": "Yuksek",
            "created_date": "2026-08-03",
            "updated_date": "2026-08-10"
        },
        {
            "project_id": PROJECT_ID,
            "project": "Ornek Proje",
            "created_by": "Mehmet Demir",
            "assigned_to": "Ahmet Yilmaz",
            "title": "Malzeme siparisi verilmeli",
            "work_type": "Tedarik",
            "description": "Demir ve beton malzemeleri icin 3 farkli tedarikciden teklif alinacak.",
            "status": "Devam Ediyor",
            "priority": "Orta",
            "created_date": "2026-08-05",
            "updated_date": "2026-08-12"
        },
        {
            "project_id": PROJECT_ID,
            "project": "Ornek Proje",
            "created_by": "Zeynep Celik",
            "assigned_to": "Mehmet Demir",
            "title": "Ilerleme raporu hazirlanmali",
            "work_type": "Dokumantasyon",
            "description": "Haftalik ilerleme raporu hazirlanip proje sahibine gonderilecek.",
            "status": "Tamamlandi",
            "priority": "Orta",
            "created_date": "2026-08-07",
            "updated_date": "2026-08-14"
        },
        {
            "project_id": PROJECT_ID,
            "project": "Ornek Proje",
            "created_by": "Ali Yildiz",
            "assigned_to": "Ayse Kaya",
            "title": "Mekanik proje revize edilmeli",
            "work_type": "Proje Yonetimi",
            "description": "Saha durumuna gore mekanik projede degisiklik yapilacak.",
            "status": "Acik",
            "priority": "Dusuk",
            "created_date": "2026-08-10",
            "updated_date": "2026-08-10"
        },
        {
            "project_id": PROJECT_ID,
            "project": "Ornek Proje",
            "created_by": "Ayse Kaya",
            "assigned_to": "Zeynep Celik",
            "title": "Hakedis dosyasi hazirlanmali",
            "work_type": "Finans",
            "description": "Aylik hakedis dosyasi hazirlanip kontrolluk onayina sunulacak.",
            "status": "Devam Ediyor",
            "priority": "Yuksek",
            "created_date": "2026-08-15",
            "updated_date": "2026-08-20"
        },
        {
            "project_id": PROJECT_ID,
            "project": "Ornek Proje",
            "created_by": "Mehmet Demir",
            "assigned_to": "Ahmet Yilmaz",
            "title": "NCR kapatilmali",
            "work_type": "Kalite",
            "description": "NCR-001 kodlu kalite sorunu cozuldu, kapatilacak.",
            "status": "Tamamlandi",
            "priority": "Orta",
            "created_date": "2026-08-12",
            "updated_date": "2026-08-18"
        },
        {
            "project_id": PROJECT_ID,
            "project": "Ornek Proje",
            "created_by": "Zeynep Celik",
            "assigned_to": "Ali Yildiz",
            "title": "Is makinalari bakimi yapilmali",
            "work_type": "Bakim",
            "description": "Ekskavator ve vinclerin periyodik bakimlari yapilacak.",
            "status": "Acik",
            "priority": "Dusuk",
            "created_date": "2026-08-18",
            "updated_date": "2026-08-18"
        },
        {
            "project_id": PROJECT_ID,
            "project": "Ornek Proje",
            "created_by": "Ahmet Yilmaz",
            "assigned_to": "Mehmet Demir",
            "title": "Toplu isci nakliyesi planlanmali",
            "work_type": "Lojistik",
            "description": "Sahada calisan isciler icin servis aracı temin edilecek.",
            "status": "Devam Ediyor",
            "priority": "Orta",
            "created_date": "2026-08-20",
            "updated_date": "2026-08-22"
        },
        {
            "project_id": PROJECT_ID,
            "project": "Ornek Proje",
            "created_by": "Ali Yildiz",
            "assigned_to": "Ayse Kaya",
            "title": "As-built cizimler guncellenecek",
            "work_type": "Dokumantasyon",
            "description": "Sahada yapilan degisiklikler as-built cizimlere islenecek.",
            "status": "Tamamlandi",
            "priority": "Dusuk",
            "created_date": "2026-08-22",
            "updated_date": "2026-08-25"
        },
        {
            "project_id": PROJECT_ID,
            "project": "Ornek Proje",
            "created_by": "Mehmet Demir",
            "assigned_to": "Zeynep Celik",
            "title": "Maliyet analizi guncellenecek",
            "work_type": "Finans",
            "description": "Guncel maliyetler ile hedef maliyetler karsilastirilacak.",
            "status": "Acik",
            "priority": "Yuksek",
            "created_date": "2026-08-25",
            "updated_date": "2026-08-25"
        },
        {
            "project_id": PROJECT_ID,
            "project": "Ornek Proje",
            "created_by": "Ayse Kaya",
            "assigned_to": "Ahmet Yilmaz",
            "title": "Son kontrol listesi hazirlanmali",
            "work_type": "Kalite",
            "description": "Proje bitimi icin yapilacak kontrollerin listesi hazirlanacak.",
            "status": "Acik",
            "priority": "Orta",
            "created_date": "2026-08-28",
            "updated_date": "2026-08-28"
        }
    ]
    
    for action in actions:
        try:
            admin_supabase.table(T_ACTIONS).insert(action).execute()
        except Exception as e:
            print(f"Aksiyon hatasi: {e}")
    print("Aksiyon verileri eklendi")
    
    print("")
    print("=" * 50)
    print("ORNEK PROJE SEED TAMAMLANDI")
    print("=" * 50)
    print(f"Proje ID: {PROJECT_ID}")
    print(f"Proje Adi: Ornek Proje")
    print(f"Kesif Kalemleri: {len(items)}")
    print(f"Program Aktiviteleri: {len(schedule)}")
    print(f"Maliyet Kalemleri: {len(costs)}")
    print(f"Nakit Akisi: {len(cashflow)}")
    print(f"Gunluk Kaynak: {len(resources)}")
    print(f"Gunluk Is Ilerleme: {len(work_data)}")
    print(f"Aksiyon: {len(actions)}")
    print("=" * 50)

if __name__ == "__main__":
    seed_all()