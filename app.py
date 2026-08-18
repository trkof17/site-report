import datetime
from datetime import timedelta
import streamlit as st
import matplotlib.pyplot as plt
from utils.auth import sign_up, sign_in, sign_out
from utils.db import get_user_projects, create_project, add_daily_report, add_bulk_reports, get_project_reports
from utils.parser import load_excel, detect_errors, calculate_metrics
from utils.supabase_client import get_supabase
from utils.db import get_user_projects, create_project, add_daily_report, add_bulk_reports, get_project_reports

st.set_page_config(page_title="Site Report Intelligence", page_icon="🏗️")

# --- Oturum Yönetimi ---
def get_current_user():
    supabase = get_supabase()
    try:
        user = supabase.auth.get_user()
        return user.user if user else None
    except:
        return None

if "user" not in st.session_state:
    st.session_state.user = None
    st.session_state.logged_in = False

user = st.session_state.user
if user is None:
    user = get_current_user()
    if user:
        st.session_state.user = user
        st.session_state.logged_in = True

if not st.session_state.logged_in:
    st.title("🏗️ Site Report Intelligence")
    tab1, tab2 = st.tabs(["Giriş Yap", "Kayıt Ol"])
    
    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Şifre", type="password", key="login_password")
        if st.button("Giriş Yap"):
            if not email or not password:
                st.warning("Lütfen email ve şifre alanlarını doldurun.")
            else:
                user, err = sign_in(email.strip(), password)
                if user:
                    st.session_state.user = user
                    st.session_state.logged_in = True
                    st.success("Giriş başarılı!")
                    st.rerun()
                else:
                    st.error(f"Hata: {err}")
    
    with tab2:
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Şifre", type="password", key="signup_password")
        if st.button("Kayıt Ol"):
            if not email or not password:
                st.warning("Lütfen email ve şifre alanlarını doldurun.")
            else:
                user, err = sign_up(email.strip(), password)
                if user:
                    st.success("Kayıt başarılı! Şimdi giriş yapabilirsin.")
                else:
                    st.error(f"Hata: {err}")
    st.stop()

# --- Giriş Yapıldıysa ---
st.sidebar.write(f"👤 {st.session_state.user.email}")
if st.sidebar.button("🚪 Çıkış Yap"):
    sign_out()
    st.session_state.user = None
    st.session_state.logged_in = False
    st.rerun()

st.title("📊 Günlük Rapor Girişi")

projects, err = get_user_projects()
project_names = [p["project_name"] for p in projects] if projects else []

if not project_names:
    st.info("Henüz bir proje oluşturmadınız. İlk projenizi oluşturun.")
    with st.form("new_project"):
        pname = st.text_input("Proje Adı")
        start = st.date_input("Başlangıç Tarihi")
        end = st.date_input("Bitiş Tarihi")
        if st.form_submit_button("Proje Oluştur"):
            if pname:
                proj, err = create_project(pname, str(start), str(end))
                if proj:
                    st.success("Proje oluşturuldu! Sayfayı yenileyin.")
                    st.rerun()
                else:
                    st.error(f"Hata: {err}")
            else:
                st.warning("Proje adı boş olamaz.")
    st.stop()

selected_project = st.selectbox("Proje Seçin", project_names)
project_id = next(p["id"] for p in projects if p["project_name"] == selected_project)

# --- Veri Giriş Formu ---
with st.form("daily_report"):
    col1, col2 = st.columns(2)
    with col1:
        report_date = st.date_input("Tarih", datetime.date.today())
        activity = st.text_input("Aktivite / İş Tanımı")
        trade = st.selectbox("İş Türü", ["Beton", "Demir", "Elektrik", "Mekanik", "Diğer"])
        planned_manpower = st.number_input("Planlanan İşçi Sayısı", min_value=0, step=1)
        actual_manpower = st.number_input("Gerçekleşen İşçi Sayısı", min_value=0, step=1)
    with col2:
        planned_machine_hours = st.number_input("Planlanan Makine Saati", min_value=0.0, step=0.1)
        actual_machine_hours = st.number_input("Gerçekleşen Makine Saati", min_value=0.0, step=0.1)
        planned_quantity = st.number_input("Planlanan Miktar", min_value=0.0, step=1.0)
        actual_quantity = st.number_input("Gerçekleşen Miktar", min_value=0.0, step=1.0)
        cost = st.number_input("Maliyet (TL)", min_value=0.0, step=100.0)
        notes = st.text_area("Notlar")
    
    submitted = st.form_submit_button("Raporu Kaydet")
    if submitted:
        if not activity:
            st.warning("Aktivite adı boş olamaz.")
        else:
            result, err = add_daily_report(
                project_id, str(report_date), activity, trade,
                planned_manpower, actual_manpower,
                planned_machine_hours, actual_machine_hours,
                planned_quantity, actual_quantity,
                cost, notes
            )
            if result:
                st.success("Rapor başarıyla kaydedildi!")
            else:
                st.error(f"Kayıt hatası: {err}")

st.divider()

# --- Excel Upload ---
st.subheader("📁 Geçmiş Verileri Excel'den İçe Aktar")
uploaded_file = st.file_uploader("Excel veya CSV dosyası seçin", type=['xlsx', 'xls', 'csv'])

if uploaded_file:
    if uploaded_file.size > 10 * 1024 * 1024:
        st.error("Dosya 10MB'dan büyük. Lütfen daha küçük bir dosya yükleyin.")
    else:
        with st.spinner("Dosya işleniyor..."):
            df, err = load_excel(uploaded_file)
            if err:
                st.error(err)
            else:
                st.success(f"Dosya başarıyla okundu. {len(df)} satır veri bulundu.")
                
                errors = detect_errors(df)
                total_errors = sum(len(v) for v in errors.values())
                st.metric("Toplam Hata", total_errors)
                if total_errors > 0:
                    with st.expander("Hata Detayları"):
                        if errors['missing_dates']:
                            st.write(f"⚠️ Eksik Tarih: {len(errors['missing_dates'])} satır")
                        if errors['negative_values']:
                            st.write(f"⚠️ Negatif Değer: {len(errors['negative_values'])} satır")
                        if errors['text_in_numeric']:
                            st.write(f"⚠️ Sayısal Sütunda Metin: {len(errors['text_in_numeric'])} satır")
                        if errors['date_order']:
                            st.write(f"⚠️ Tarih Sıralama Hatası: {len(errors['date_order'])} satır")
                        if errors['blank_activities']:
                            st.write(f"⚠️ Boş Aktivite: {len(errors['blank_activities'])} satır")
                
                metrics = calculate_metrics(df)
                col1, col2, col3 = st.columns(3)
                col1.metric("Toplam İşçilik Saati", f"{metrics['total_manhours']:.0f}")
                col2.metric("Toplam Makine Saati", f"{metrics['total_machine_hours']:.1f}")
                if metrics['completion_percentage'] is not None:
                    col3.metric("Tamamlanma Yüzdesi", f"{metrics['completion_percentage']:.1f}%")
                
                if metrics['trade_data']:
                    st.subheader("📊 İş Türüne Göre Planlanan vs Gerçekleşen")
                    fig, ax = plt.subplots(figsize=(10, 5))
                    trades = metrics['trade_data']['trades']
                    planned = metrics['trade_data']['planned']
                    actual = metrics['trade_data']['actual']
                    x = range(len(trades))
                    width = 0.35
                    ax.bar([i - width/2 for i in x], planned, width, label='Planlanan', color='#1E3D59')
                    ax.bar([i + width/2 for i in x], actual, width, label='Gerçekleşen', color='#17A2B8')
                    ax.set_xlabel('İş Türü')
                    ax.set_ylabel('İşçilik Saati')
                    ax.set_xticks(x)
                    ax.set_xticklabels(trades, rotation=45, ha='right')
                    ax.legend()
                    st.pyplot(fig)
                
                if st.button("Bu Verileri Projeye Kaydet"):
                    with st.spinner("Veriler kaydediliyor..."):
                        count, err = add_bulk_reports(project_id, df)
                        if err:
                            st.error(f"Kayıt hatası: {err}")
                        else:
                            st.success(f"✅ {count} satır başarıyla veritabanına kaydedildi!")

st.divider()

# --- DASHBOARD ---
st.subheader("📊 Proje Özeti (Dashboard)")
reports, err = get_project_reports(project_id)
if err:
    st.error(f"Veriler alınamadı: {err}")
elif reports:
    import pandas as pd
    df_reports = pd.DataFrame(reports)
    
    # Tarih sütununu datetime'a çevir (öncelikle)
    df_reports['report_date'] = pd.to_datetime(df_reports['report_date'])
    
    # 1. Temel Metrikler
    total_manpower = df_reports['actual_manpower'].sum()
    total_machine = df_reports['actual_machine_hours'].sum()
    total_cost = df_reports['cost'].sum() if 'cost' in df_reports else 0
    total_activities = len(df_reports)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👷 Toplam İşçilik", f"{total_manpower:.0f} saat")
    col2.metric("🏗️ Toplam Makine", f"{total_machine:.1f} saat")
    col3.metric("💰 Toplam Maliyet", f"{total_cost:,.0f} TL")
    col4.metric("📋 Toplam Aktivite", total_activities)
    
    # 2. Son 7 Gün (DÜZELTİLDİ)
    st.subheader("📈 Son 7 Günlük İşçilik")
    
    # Bugünün tarihini al (datetime formatında)
    today = pd.Timestamp(datetime.date.today())
    seven_days_ago = today - pd.Timedelta(days=7)
    
    # Filtreleme
    mask = df_reports['report_date'] >= seven_days_ago
    last_7 = df_reports[mask]
    
    if not last_7.empty:
        # Günlük toplamları hesapla
        daily = last_7.groupby(last_7['report_date'].dt.date)['actual_manpower'].sum().reset_index()
        daily.columns = ['tarih', 'işçilik']
        
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.bar(daily['tarih'].astype(str), daily['işçilik'], color='#1E3D59')
        ax.set_xlabel('Tarih')
        ax.set_ylabel('İşçilik Saati')
        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.info("Son 7 gün içinde veri yok.")
    
    # 3. İş Türüne Göre Dağılım
    st.subheader("📊 İş Türüne Göre Toplam İşçilik")
    if 'trade' in df_reports.columns:
        trade_summary = df_reports.groupby('trade')['actual_manpower'].sum().reset_index()
        if not trade_summary.empty:
            fig2, ax2 = plt.subplots(figsize=(8, 4))
            ax2.pie(trade_summary['actual_manpower'], labels=trade_summary['trade'], autopct='%1.1f%%')
            ax2.axis('equal')
            st.pyplot(fig2)
        else:
            st.info("İş türü verisi bulunamadı.")
    else:
        st.info("İş türü sütunu bulunamadı.")
    
    # 4. Hata Özeti
    st.subheader("⚠️ Hata Özeti")
    missing_count = df_reports.isnull().sum().sum()
    if missing_count > 0:
        st.warning(f"🔍 Verilerde {missing_count} adet eksik/boş değer bulundu.")
        with st.expander("Detaylı Hata Raporu"):
            st.dataframe(df_reports.isnull().sum().rename("Eksik Sayısı"))
    else:
        st.success("✅ Verilerde hata bulunamadı.")
    
    # 5. Son 10 Kayıt
    with st.expander("📋 Son 10 Rapor Kaydı"):
        st.dataframe(df_reports.tail(10)[['report_date', 'activity', 'trade', 'actual_manpower', 'actual_machine_hours']])
        
else:
    st.info("Henüz bu projeye ait rapor yok. Veri girişi yapın veya Excel yükleyin.")
    
    
# --- LEAD CAPTURE (Email Toplama) ---
st.divider()
st.subheader("🚀 Ücretsiz Rapor Analizi İstiyorum")

# Mevcut projedeki hata sayısını hesapla
reports, _ = get_project_reports(project_id)
error_count = 0
total_manhours = 0
if reports:
    import pandas as pd
    df_temp = pd.DataFrame(reports)
    error_count = df_temp.isnull().sum().sum()
    total_manhours = df_temp['actual_manpower'].sum() if 'actual_manpower' in df_temp else 0

with st.container():
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"""
        **📊 Raporunuzu analiz edelim ve size özel bir özet gönderelim.**

        - 🔍 Mevcut verilerinizde **{error_count}** potansiyel hata tespit edildi.
        - 📈 İşçilik, makine ve maliyet özeti çıkaralım.
        - 🎯 Projenizin durumunu değerlendirelim.

        **Üstelik tamamen ücretsiz!**
        """)
    with col2:
        st.info("""
        ✅ **Ne Kazanırsınız?**
        - Hata raporu
        - Performans özeti
        - İyileştirme önerileri
        """)

with st.form("lead_capture_form"):
    col1, col2 = st.columns(2)
    with col1:
        lead_email = st.text_input("📧 Email Adresiniz", placeholder="ornek@firma.com")
    with col2:
        lead_company = st.text_input("🏢 Şirket Adı", placeholder="Şirket Adı")
    
    lead_phone = st.text_input("📱 Telefon (Opsiyonel)", placeholder="5XX XXX XX XX")
    
    st.caption(f"🔍 Mevcut verilerinizde **{error_count}** potansiyel hata var. Bu raporu ücretsiz analiz edelim.")
    
    submitted = st.form_submit_button("📩 Ücretsiz Rapor Analizi İstiyorum", use_container_width=True)
    
    if submitted:
        if not lead_email or not lead_company:
            st.warning("Lütfen email ve şirket adını girin.")
        else:
            from utils.sheets import append_lead
            success = append_lead(
                "Site Report Leads",
                lead_email.strip(),
                lead_company.strip(),
                selected_project,
                error_count,
                total_manhours
            )
            if success:
                st.success("✅ Başvurunuz alındı! Rapor analizinizi emailinize gönderiyoruz.")
                st.balloons()
                st.info("📧 Emailinizi kontrol edin. Önümüzdeki 24 saat içinde detaylı rapor gönderilecektir.")
            else:
                st.error("❌ Kayıt sırasında bir sorun oluştu. Lütfen tekrar deneyin.")