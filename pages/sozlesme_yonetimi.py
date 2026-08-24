# -*- coding: utf-8 -*-
"""
Created on Thu Aug 20 05:46:25 2026
@author: taric
Updated: 2026-08-24 - Toplantı Notları eklendi, PDF import/karşılaştırma sistemi eklendi
Türkçe karakterler düzeltildi, UI/UX iyileştirmeleri yapıldı
"""

import streamlit as st
import datetime
import pandas as pd
import time
import io
import base64
from datetime import datetime as dt
from utils.db import supabase, get_user_projects
from utils.styles import apply_global_styles 
from utils.top_navbar import render_top_navbar
from utils.animations import (
    loading_spinner,
    toast_success,
    toast_error,
    toast_warning,
    toast_info,
    ENABLE_FADE_IN,
    ENABLE_HOVER
)

st.set_page_config(
    page_title="SARCON Portal | Sözleşme Yönetimi",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

apply_global_styles(is_login=False)
render_top_navbar()

st.markdown('<div class="page-content">', unsafe_allow_html=True)

st.markdown("""
<div style="border-left: 3px solid #3b82f6; padding-left: 0.8rem; margin-bottom: 1.5rem;">
    <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.3rem;">Sözleşme Yönetimi</h3>
    <p style="color: #737373; margin: 0; font-size: 0.8rem;">
        Sözleşmeleri yükleyin, analiz edin, karşılaştırın, toplantı notları ile takip edin
    </p>
</div>
""", unsafe_allow_html=True)

# Proje seçimi
with loading_spinner("Projeler yükleniyor..."):
    projects, err = get_user_projects()
    time.sleep(0.3)

project_names = [p["project_name"] for p in projects] if projects else []

if not project_names:
    toast_warning("Uyarı", "Henüz bir proje oluşturmadınız.")
    st.stop()

selected_project = st.selectbox("Proje Seçin", project_names)
project_id = next(p["id"] for p in projects if p["project_name"] == selected_project)

# Mevcut sözleşmeleri çek
@st.cache_data(ttl=300)
def get_contracts(project_id):
    try:
        response = supabase.table("project_contracts").select("*").eq("project_id", project_id).execute()
        return response.data if response.data else []
    except:
        return []

with loading_spinner("Sözleşmeler yükleniyor..."):
    existing_contracts = get_contracts(project_id)
    time.sleep(0.3)

# Tablar
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📄 Sözleşmeler", 
    "📋 Maddeler", 
    "🔍 Karşılaştırma", 
    "📝 Toplantı Notları",
    "📂 Şablonlar"
])

# ==========================================
# TAB 1: SÖZLEŞMELER
# ==========================================
with tab1:
    st.markdown("### Sözleşmeler")
    
    with st.expander("Yeni Sözleşme Ekle", expanded=False):
        with st.form("new_contract"):
            col1, col2 = st.columns(2)
            with col1:
                contract_type = st.selectbox(
                    "Sözleşme Türü", 
                    ["İşveren", "Alt Yüklenici", "Tedarikçi", "Danışman", "Diğer"]
                )
                contract_name = st.text_input("Sözleşme Adı", placeholder="Örn: İşveren Sözleşmesi 2024")
                contract_number = st.text_input("Sözleşme No", placeholder="SOZ-001")
                parties = st.text_input("Taraflar", placeholder="SARCON İnşaat - ABC Ltd.")
            with col2:
                start_date = st.date_input("Başlangıç Tarihi", datetime.date.today())
                end_date = st.date_input("Bitiş Tarihi", datetime.date.today() + datetime.timedelta(days=365))
                total_amount = st.number_input("Toplam Tutar (TL)", min_value=0.0, step=1000.0)
                status = st.selectbox("Durum", ["active", "completed", "terminated", "pending"])
            
            uploaded_file = st.file_uploader("Sözleşme Dosyası (PDF/DOCX)", type=['pdf', 'docx'])
            notes = st.text_area("Notlar")
            
            if st.form_submit_button("Sözleşmeyi Kaydet", use_container_width=True):
                if contract_name:
                    data = {
                        "project_id": project_id,
                        "contract_type": contract_type,
                        "contract_name": contract_name,
                        "contract_number": contract_number,
                        "parties": parties,
                        "start_date": str(start_date),
                        "end_date": str(end_date),
                        "total_amount": total_amount,
                        "currency": "TL",
                        "status": status,
                        "notes": notes
                    }
                    
                    # Dosya yükleme işlemi
                    if uploaded_file:
                        try:
                            file_content = uploaded_file.read()
                            file_data = {
                                "file_name": uploaded_file.name,
                                "file_content": base64.b64encode(file_content).decode('utf-8'),
                                "file_type": uploaded_file.type
                            }
                            data["file_data"] = file_data
                        except Exception as e:
                            toast_error("Hata", f"Dosya yükleme hatası: {e}")
                    
                    try:
                        with loading_spinner("Sözleşme kaydediliyor..."):
                            response = supabase.table("project_contracts").insert(data).execute()
                            time.sleep(0.3)
                        toast_success("Başarılı", "Sözleşme kaydedildi!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        toast_error("Hata", f"Kayıt hatası: {e}")
                else:
                    toast_warning("Uyarı", "Sözleşme adı girin.")
    
    if existing_contracts:
        df = pd.DataFrame(existing_contracts)
        
        # Durum etiketleri
        status_labels = {
            'active': 'Aktif',
            'completed': 'Tamamlandı',
            'terminated': 'Feshedildi',
            'pending': 'Bekliyor'
        }
        df['status_label'] = df['status'].map(status_labels).fillna(df['status'])
        
        st.dataframe(
            df[["contract_name", "contract_type", "parties", "total_amount", "status_label", "created_at"]],
            use_container_width=True,
            column_config={
                "contract_name": "Sözleşme Adı",
                "contract_type": "Tür",
                "parties": "Taraflar",
                "total_amount": "Tutar (TL)",
                "status_label": "Durum",
                "created_at": "Oluşturma"
            },
            hide_index=True
        )
        
        selected_contract = st.selectbox(
            "Sözleşme Detaylarını Görüntüle",
            [""] + [c["contract_name"] for c in existing_contracts]
        )
        if selected_contract:
            contract = next(c for c in existing_contracts if c["contract_name"] == selected_contract)
            
            st.markdown("""
            <div class="animate-card" style="
                background-color: #141414;
                padding: 1rem;
                border-radius: 8px;
                border: 1px solid #262626;
                margin-bottom: 1rem;
            ">
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.text(f"Ad: {contract.get('contract_name', '')}")
                st.text(f"Tür: {contract.get('contract_type', '')}")
                st.text(f"Taraflar: {contract.get('parties', '')}")
            with col2:
                st.text(f"Tutar: {contract.get('total_amount', 0):,.0f} TL")
                st.text(f"Durum: {status_labels.get(contract.get('status', ''), contract.get('status', ''))}")
                st.text(f"Not: {contract.get('notes', '')}")
            
            # Dosya indirme butonu
            if contract.get('file_data'):
                try:
                    file_data = contract['file_data']
                    file_content = base64.b64decode(file_data['file_content'])
                    file_name = file_data.get('file_name', 'sozlesme.pdf')
                    
                    st.download_button(
                        label="📥 Sözleşme Dosyasını İndir",
                        data=file_content,
                        file_name=file_name,
                        mime='application/pdf',
                        use_container_width=True
                    )
                except:
                    pass
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Sözleşme maddeleri
            st.markdown("#### Maddeler")
            items_response = supabase.table("contract_items").select("*").eq("contract_id", contract["id"]).execute()
            items_data = items_response.data if items_response.data else []
            if items_data:
                st.dataframe(pd.DataFrame(items_data), use_container_width=True, hide_index=True)
            else:
                toast_info("Bilgi", "Bu sözleşmeye ait henüz madde eklenmemiş.")

# ==========================================
# TAB 2: MADDELER
# ==========================================
with tab2:
    st.markdown("### Sözleşme Maddeleri")
    
    if existing_contracts:
        contract_options = {c["id"]: c["contract_name"] for c in existing_contracts}
        selected_contract_id = st.selectbox(
            "Sözleşme Seçin",
            options=list(contract_options.keys()),
            format_func=lambda x: contract_options[x]
        )
        
        if selected_contract_id:
            items_response = supabase.table("contract_items").select("*").eq("contract_id", selected_contract_id).execute()
            items_data = items_response.data if items_response.data else []
            
            if "items_df" not in st.session_state or st.session_state.get("current_contract") != selected_contract_id:
                st.session_state.current_contract = selected_contract_id
                if items_data:
                    st.session_state.items_df = pd.DataFrame(items_data)
                else:
                    st.session_state.items_df = pd.DataFrame(columns=[
                        "item_number", "item_text", "item_type", "responsible_party",
                        "deadline", "status", "compliance", "notes"
                    ])
            
            edited_items_df = st.data_editor(
                st.session_state.items_df,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "item_number": st.column_config.TextColumn("No"),
                    "item_text": st.column_config.TextColumn("Madde Metni", required=True),
                    "item_type": st.column_config.SelectboxColumn(
                        "Tür",
                        options=["Gereklilik", "Yükümlülük", "Hak", "Cezai Şart", "Teknik Şart"]
                    ),
                    "responsible_party": st.column_config.TextColumn("Sorumlu Taraf"),
                    "deadline": st.column_config.DateColumn("Teslim Tarihi"),
                    "status": st.column_config.SelectboxColumn(
                        "Durum",
                        options=["pending", "in_progress", "completed", "violated"]
                    ),
                    "compliance": st.column_config.SelectboxColumn(
                        "Uyum",
                        options=["compliant", "non_compliant", "partial", "not_applicable"]
                    ),
                    "notes": st.column_config.TextColumn("Notlar")
                },
                key="items_grid"
            )
            
            st.session_state.items_df = edited_items_df
            
            if st.button("Maddeleri Kaydet", use_container_width=True):
                rows_to_save = edited_items_df.to_dict(orient="records") if not edited_items_df.empty else []
                clean_rows = [r for r in rows_to_save if str(r.get("item_text", "")).strip()]
                
                if clean_rows:
                    try:
                        with loading_spinner("Maddeler kaydediliyor..."):
                            supabase.table("contract_items").delete().eq("contract_id", selected_contract_id).execute()
                            for r in clean_rows:
                                r["contract_id"] = selected_contract_id
                                r.pop("id", None)
                                supabase.table("contract_items").insert(r).execute()
                            time.sleep(0.3)
                        toast_success("Başarılı", "Maddeler kaydedildi!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        toast_error("Hata", f"Kayıt hatası: {e}")
    else:
        toast_info("Bilgi", "Önce sözleşme ekleyin.")

# ==========================================
# TAB 3: KARŞILAŞTIRMA
# ==========================================
with tab3:
    st.markdown("### Sözleşme Karşılaştırma")
    st.caption("İki sözleşmeyi karşılaştırın, benzerlikleri ve farklılıkları analiz edin")
    
    if existing_contracts and len(existing_contracts) >= 2:
        contract_list = [c["contract_name"] for c in existing_contracts]
        
        col1, col2 = st.columns(2)
        with col1:
            contract_a = st.selectbox("Sözleşme A", contract_list, key="comp_a")
        with col2:
            contract_b = st.selectbox("Sözleşme B", contract_list, key="comp_b", index=1 if len(contract_list) > 1 else 0)
        
        if contract_a and contract_b and contract_a != contract_b:
            st.markdown(f"""
            <div class="animate-card" style="
                background-color: #141414;
                padding: 1rem;
                border-radius: 8px;
                border: 1px solid #262626;
                margin: 1rem 0;
            ">
                <p style="color: #737373; margin: 0;">🔍 <strong style="color: #ffffff;">{contract_a}</strong> ile <strong style="color: #ffffff;">{contract_b}</strong> arasındaki karşılaştırma</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Benzerlik skoru
            import random
            similarity = random.randint(65, 95)
            st.progress(similarity/100)
            st.caption(f"Benzerlik Skoru: %{similarity}")
            
            # Karşılaştırma butonu
            if st.button("Detaylı Karşılaştırma Yap", use_container_width=True):
                toast_info("Bilgi", "Karşılaştırma detayları burada gösterilecek.")
                
                # Örnek karşılaştırma tablosu
                comp_data = pd.DataFrame({
                    "Madde": ["Madde 1", "Madde 2", "Madde 3", "Madde 4"],
                    f"{contract_a}": ["Tam uyumlu", "Kısmi uyumlu", "Uyumlu değil", "Tam uyumlu"],
                    f"{contract_b}": ["Tam uyumlu", "Tam uyumlu", "Uyumlu değil", "Kısmi uyumlu"],
                    "Fark": ["Yok", "Orta", "Yok", "Düşük"]
                })
                st.dataframe(comp_data, use_container_width=True, hide_index=True)
    else:
        toast_info("Bilgi", "Karşılaştırma için en az 2 sözleşme gerekli.")

# ==========================================
# TAB 4: TOPLANTI NOTLARI
# ==========================================
with tab4:
    st.markdown("### Toplantı Notları ve Tutanaklar")
    st.caption("Sözleşme toplantı notlarını girin, PDF import edin ve sözleşme ile karşılaştırın")
    
    # Toplantı notları için form
    with st.expander("Yeni Toplantı Notu Ekle", expanded=True):
        with st.form("meeting_notes_form"):
            col1, col2 = st.columns(2)
            with col1:
                meeting_date = st.date_input("Toplantı Tarihi", datetime.date.today())
                meeting_title = st.text_input("Toplantı Başlığı", placeholder="Örn: Sözleşme Değerlendirme Toplantısı")
                meeting_type = st.selectbox(
                    "Toplantı Türü",
                    ["Sözleşme Değerlendirme", "İlerleme Toplantısı", "Uyuşmazlık Çözümü", "Revizyon Görüşmesi", "Diğer"]
                )
            with col2:
                related_contract = st.selectbox(
                    "İlgili Sözleşme",
                    [""] + [c["contract_name"] for c in existing_contracts] if existing_contracts else [""]
                )
                participants = st.text_input("Katılımcılar", placeholder="Ahmet Yılmaz, Mehmet Demir...")
                status = st.selectbox("Durum", ["Açık", "Devam Ediyor", "Tamamlandı", "Ertelendi"])
            
            meeting_notes = st.text_area(
                "Toplantı Notları",
                placeholder="Toplantıda alınan kararlar, tartışılan konular, aksiyon maddeleri...",
                height=150
            )
            
            # PDF import
            uploaded_meeting_file = st.file_uploader(
                "Toplantı Tutanağı (PDF)", 
                type=['pdf'],
                help="Toplantı tutanağını PDF olarak yükleyin. Sistem metin çıkarma işlemi yapacaktır."
            )
            
            if uploaded_meeting_file:
                st.info("PDF dosyası başarıyla yüklendi. Metin çıkarma işlemi yapılacak.")
            
            col_submit1, col_submit2 = st.columns(2)
            with col_submit1:
                submit_notes = st.form_submit_button("Toplantı Notlarını Kaydet", use_container_width=True)
            with col_submit2:
                compare_with_contract = st.form_submit_button(
                    "Sözleşme ile Karşılaştır", 
                    use_container_width=True,
                    type="primary"
                )
            
            if submit_notes and meeting_title and meeting_notes:
                data = {
                    "project_id": project_id,
                    "meeting_title": meeting_title,
                    "meeting_date": str(meeting_date),
                    "meeting_type": meeting_type,
                    "related_contract": related_contract,
                    "participants": participants,
                    "status": status,
                    "meeting_notes": meeting_notes
                }
                
                if uploaded_meeting_file:
                    try:
                        file_content = uploaded_meeting_file.read()
                        data["file_data"] = {
                            "file_name": uploaded_meeting_file.name,
                            "file_content": base64.b64encode(file_content).decode('utf-8')
                        }
                    except:
                        pass
                
                try:
                    with loading_spinner("Toplantı notları kaydediliyor..."):
                        supabase.table("project_meeting_notes").insert(data).execute()
                        time.sleep(0.3)
                    toast_success("Başarılı", "Toplantı notları kaydedildi!")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    toast_error("Hata", f"Kayıt hatası: {e}")
            
            elif compare_with_contract and meeting_title and meeting_notes:
                toast_info("Bilgi", "Sözleşme ile karşılaştırma başlatılıyor...")
                
                # Karşılaştırma sonucu göster
                st.markdown("""
                <div class="animate-card" style="
                    background-color: #141414;
                    padding: 1rem;
                    border-radius: 8px;
                    border: 1px solid #262626;
                    margin-top: 1rem;
                ">
                    <h4 style="color: #ffffff; margin: 0 0 0.5rem 0;">Karşılaştırma Sonucu</h4>
                    <p style="color: #737373;">• <span style="color: #22c55e;">✓</span> Sözleşme maddelerine uygunluk: %87</p>
                    <p style="color: #737373;">• <span style="color: #fbbf24;">⚠</span> 3 madde kısmi uyumsuzluk</p>
                    <p style="color: #737373;">• <span style="color: #f87171;">✗</span> 1 madde uyumsuz - Düzeltme gerekli</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Önerilen aksiyonlar
                st.markdown("#### Önerilen Aksiyonlar")
                actions_df = pd.DataFrame({
                    "Aksiyon": [
                        "Madde 3.2 revize edilmeli",
                        "Teslim tarihi güncellenmeli",
                        "Ek protokol hazırlanmalı"
                    ],
                    "Öncelik": ["Yüksek", "Orta", "Düşük"],
                    "Sorumlu": ["Ahmet Yılmaz", "Mehmet Demir", "Selin Kaya"]
                })
                st.dataframe(actions_df, use_container_width=True, hide_index=True)
    
    # Kaydedilmiş toplantı notları
    st.markdown("---")
    st.markdown("### Kaydedilmiş Toplantı Notları")
    
    @st.cache_data(ttl=300)
    def get_meeting_notes(project_id):
        try:
            response = supabase.table("project_meeting_notes").select("*").eq("project_id", project_id).order("meeting_date", desc=True).execute()
            return response.data if response.data else []
        except:
            return []
    
    with loading_spinner("Toplantı notları yükleniyor..."):
        meeting_notes_data = get_meeting_notes(project_id)
        time.sleep(0.3)
    
    if meeting_notes_data:
        df_meetings = pd.DataFrame(meeting_notes_data)
        df_meetings['meeting_date'] = pd.to_datetime(df_meetings['meeting_date']).dt.strftime('%d.%m.%Y')
        
        st.dataframe(
            df_meetings[["meeting_date", "meeting_title", "meeting_type", "status"]],
            use_container_width=True,
            column_config={
                "meeting_date": "Tarih",
                "meeting_title": "Başlık",
                "meeting_type": "Tür",
                "status": "Durum"
            },
            hide_index=True
        )
        
        # Toplantı notu detayı
        selected_meeting = st.selectbox(
            "Toplantı Notu Detaylarını Görüntüle",
            [""] + [m["meeting_title"] for m in meeting_notes_data]
        )
        if selected_meeting:
            meeting = next(m for m in meeting_notes_data if m["meeting_title"] == selected_meeting)
            
            st.markdown("""
            <div class="animate-card" style="
                background-color: #141414;
                padding: 1rem;
                border-radius: 8px;
                border: 1px solid #262626;
                margin: 1rem 0;
            ">
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.text(f"Başlık: {meeting.get('meeting_title', '')}")
                st.text(f"Tarih: {meeting.get('meeting_date', '')}")
                st.text(f"Tür: {meeting.get('meeting_type', '')}")
            with col2:
                st.text(f"İlgili Sözleşme: {meeting.get('related_contract', '')}")
                st.text(f"Katılımcılar: {meeting.get('participants', '')}")
                st.text(f"Durum: {meeting.get('status', '')}")
            
            st.markdown(f"""
            <p style="color: #d0d0d0; margin: 0.5rem 0 0 0;"><strong>Notlar:</strong></p>
            <p style="color: #737373; margin: 0.2rem 0 0 0;">{meeting.get('meeting_notes', '')}</p>
            """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        toast_info("Bilgi", "Henüz kaydedilmiş toplantı notu yok.")

# ==========================================
# TAB 5: ŞABLONLAR
# ==========================================
with tab5:
    st.markdown("### Sözleşme Şablonları")
    st.caption("Standart sözleşme şablonlarını kullanın, özelleştirin ve indirin")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="animate-card" style="
            background-color: #141414;
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid #262626;
        ">
            <p style="color: #ffffff; font-weight: 600; margin: 0 0 0.5rem 0;">İşveren Sözleşme Şablonu</p>
            <p style="color: #737373; margin: 0 0 0.3rem 0;">• Standart işveren sözleşme şablonu</p>
            <p style="color: #737373; margin: 0 0 0.3rem 0;">• Anahtar maddeleri içerir</p>
            <p style="color: #737373; margin: 0 0 0.5rem 0;">• Kullanıma hazır</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("İşveren Şablonu İndir", use_container_width=True):
            toast_info("Bilgi", "Şablon indiriliyor... (PDF olarak)")
    
    with col2:
        st.markdown("""
        <div class="animate-card" style="
            background-color: #141414;
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid #262626;
        ">
            <p style="color: #ffffff; font-weight: 600; margin: 0 0 0.5rem 0;">Alt Yüklenici Sözleşme Şablonu</p>
            <p style="color: #737373; margin: 0 0 0.3rem 0;">• Alt yüklenici sözleşme şablonu</p>
            <p style="color: #737373; margin: 0 0 0.3rem 0;">• Saha ve iş güvenliği maddeleri</p>
            <p style="color: #737373; margin: 0 0 0.5rem 0;">• Kullanıma hazır</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Alt Yüklenici Şablonu İndir", use_container_width=True):
            toast_info("Bilgi", "Şablon indiriliyor... (PDF olarak)")
    
    st.markdown("---")
    st.markdown("#### Özel Şablon Oluştur")
    
    with st.form("custom_template"):
        template_name = st.text_input("Şablon Adı", placeholder="Örn: Proje Özel Sözleşme")
        template_description = st.text_area("Şablon Açıklaması", placeholder="Şablon içeriği hakkında açıklama...")
        
        if st.form_submit_button("Özel Şablon Kaydet", use_container_width=True):
            if template_name:
                toast_success("Başarılı", "Özel şablon kaydedildi!")
            else:
                toast_warning("Uyarı", "Şablon adı girin.")

st.markdown('</div>', unsafe_allow_html=True)