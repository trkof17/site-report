# -*- coding: utf-8 -*-

# ==========================================
# ENDİREKT PERSONEL (KATEGORİLERE AYRILMIŞ)
# ==========================================
ENDIRECT_PERSONEL = [
    # YÖNETİM
    "Proje Müdürü", "İnşaat Müdürü", "Kalite Yöneticisi", "Kaba İşler Şefi",
    "İdari İşler Müdürü", "Teknik Ofis Şefi",
    
    # MÜHENDİSLİK
    "İnşaat Mühendisi", "Makine Mühendisi", "Elektrik Mühendisi", "Harita Mühendisi",
    "Teknik Ofis Müh.",
    
    # TEKNİK PERSONEL
    "İnşaat Teknikeri", "Elektrik Tes. Tek.", "Harita Teknikeri",
    "Saha Kalfası",
    
    # İSG & SAĞLIK
    "İSG Sorumlusu", "İş Yeri Hekimi", "Sağlık Memuru",
    
    # İDARİ & DESTEK
    "Muhasebe", "Satınalma", "Personel/İdari İşler", "Sekreter",
    "Bilgi İşlem", "Ambar/Kantar Sor.", "Puantör",
    
    # SAHA
    "SEÇ Gözlemci", "Kamp Amiri", "Şoför", "Tekniker"
]

# Hızlı Erişim İçin Kategori Haritası
ENDIRECT_CATEGORIES = {
    "Yönetim": ["Proje Müdürü", "İnşaat Müdürü", "Kalite Yöneticisi", "Kaba İşler Şefi", "İdari İşler Müdürü", "Teknik Ofis Şefi"],
    "Mühendislik": ["İnşaat Mühendisi", "Makine Mühendisi", "Elektrik Mühendisi", "Harita Mühendisi", "Teknik Ofis Müh."],
    "Teknik": ["İnşaat Teknikeri", "Elektrik Tes. Tek.", "Harita Teknikeri", "Saha Kalfası"],
    "İSG & Sağlık": ["İSG Sorumlusu", "İş Yeri Hekimi", "Sağlık Memuru"],
    "İdari & Destek": ["Muhasebe", "Satınalma", "Personel/İdari İşler", "Sekreter", "Bilgi İşlem", "Ambar/Kantar Sor.", "Puantör"],
    "Saha": ["SEÇ Gözlemci", "Kamp Amiri", "Şoför", "Tekniker"]
}

DIRECT_PERSONEL = ["Usta", "Düz İşçi", "Operatör"]

YAPI_MALZEME = [
    "Ø150 Drenaj Borusu", "19-38 Mıcır", "Grobeton", "İnşaat Demiri",
    "C20 B.A. Betonu", "C25 B.A. Betonu (Mobilizasyon)", "C30 B.A. Betonu",
    "7,5 Luk Gazbeton", "20 Lik Gazbeton", "Örgü Tutkalı", "Seramik",
    "Çelik hasır", "Balast Malzemesi (Mobilizasyon)", "Balast Malzemesi (Grobeton altı)",
    "Polietilen Folyo", "Polimer Bitümlü Membran (3mm)", "Geotekstil Keçe",
    "Kum (İnce)", "Kereste (10*10- 5*10)", "Nevresim Takımı", "Battaniye",
    "Yastık", "Sıvı El sabunu", "Su Deposu", "Çiroz", "Çimento", "Kum"
]

DEMIRBASLAR = ["Plywood", "Perde-Kolon Kalıbı", "Teleskopik direk"]
SARF_MALZEMELER = ["İnşaat Çivisi", "Bağ Teli"]
EL_ALETLERI = ["El arabası", "Kürek", "Kazma", "Balta", "Çekiç", "Mala", "Şakül", "Su Terazisi"]

MAKINA = [
    "JCB Bekoloder", "Cat 955", "Ekskavatör", "Ekskavatör Kırıcı", "Bobcat",
    "Silindir", "Yükleyici", "Kamyon", "Kamyonet", "High-Up Vinç", "Mobil Vinç",
    "Kule Vinç", "Total Station", "Cephe Asansörü", "Paket hidrofor", "Jeneratör",
    "Hidrofor", "Dalgıç pompa", "Nivo", "Motopomp", "Vibratör", "Dozer",
    "Hava Kompresörü", "Binek Araç", "Pick-up", "Kompresör", "Ytong Kesme Makinası",
    "Teleskopik Yükleyici", "Forklift"
]

IS_TURLERI = ["Kaba İşler", "İnce İşler", "Mekanik", "Elektrik", "Peyzaj", "Diğer"]
