# -*- coding: utf-8 -*-
"""
Created on Thu Aug 20 19:20:57 2026
@author: taric
Updated: 2026-08-22 - Birim Selectbox olarak güncellendi
"""

import streamlit as st
import datetime
import pandas as pd
import io
import time
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
    page_title="SARCON Portal | Teklif Analizi",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

apply_global_styles(is_login=False)
render_top_navbar()

st.markdown('<div class="page-content">', unsafe_allow_html=True)

st.markdown("""
<div style="border-left: 3px solid #3b82f6; padding-left: 0.8rem; margin-bottom: 1.5rem;">
    <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.3rem;">Teklif Analizi</h3>
    <p style="color: #737373; margin: 0; font-size: 0.8rem;">Teklifleri girin, analiz edin ve karsilastirin</p>
</div>
""", unsafe_allow_html=True)

# Proje secimi
with loading_spinner("Projeler yukleniyor..."):
    projects, err = get_user_projects()
    time.sleep(0.3)

project_names = [p["project_name"] for p in projects] if projects else []

if not project_names:
    toast_warning("Uyari", "Henuz bir proje olusturmadiniz.")
    st.stop()

selected_project = st.selectbox("Proje Secin", project_names)
project_id = next(p["id"] for p in projects if p["project_name"] == selected_project)

# Tablar
tab1, tab2, tab3, tab4 = st.tabs(["Teklifler", "Karsilastirma", "Teklif Raporu", "Excel Bulk Edit"])

# ==========================================
# TAB 1: TEKLIFLER
# ==========================================
with tab1:
    st.markdown("### Teklifler")
    
    @st.cache_data(ttl=300)
    def get_offers(project_id):
        try:
            response = supabase.table("project_offers").select("*").eq("project_id", project_id).execute()
            return response.data if response.data else []
        except:
            return []
    
    with loading_spinner("Veriler yukleniyor..."):
        existing_offers = get_offers(project_id)
        time.sleep(0.3)
    
    with st.expander("Yeni Teklif Ekle", expanded=False):
        with st.form("new_offer"):
            col1, col2 = st.columns(2)
            with col1:
                offer_name = st.text_input("Teklif Adi", placeholder="Orn: ABC Insaat Teklifi")
                supplier = st.text_input("Tedarikci / Yuklenici")
                offer_date = st.date_input("Teklif Tarihi", datetime.date.today())
            with col2:
                total_amount = st.number_input("Toplam Tutar (TL)", min_value=0.0, step=1000.0)
                status = st.selectbox("Durum", ["active", "accepted", "rejected"])
            
            st.markdown("**Once sablonu indirin, doldurun ve yukleyin**")
            
            notes = st.text_area("Notlar")
            
            if st.form_submit_button("Teklifi Kaydet", use_container_width=True):
                if offer_name:
                    data = {
                        "project_id": project_id,
                        "offer_name": offer_name,
                        "offer_date": str(offer_date),
                        "supplier": supplier,
                        "total_amount": total_amount,
                        "status": status,
                        "notes": notes
                    }
                    try:
                        with loading_spinner("Teklif kaydediliyor..."):
                            response = supabase.table("project_offers").insert(data).execute()
                            time.sleep(0.3)
                        toast_success("Basarili", "Teklif kaydedildi!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        toast_error("Hata", f"Kayit hatasi: {e}")
                else:
                    toast_warning("Uyari", "Teklif adi girin.")
    
    if existing_offers:
        df = pd.DataFrame(existing_offers)
        
        # Durum etiketleri
        status_labels = {
            'active': 'Aktif',
            'accepted': 'Kabul Edildi',
            'rejected': 'Reddedildi'
        }
        df['status_label'] = df['status'].map(status_labels).fillna(df['status'])
        
        st.dataframe(
            df[["offer_name", "supplier", "total_amount", "status_label", "created_at"]],
            use_container_width=True,
            column_config={
                "offer_name": "Teklif Adi",
                "supplier": "Tedarikci",
                "total_amount": "Tutar (TL)",
                "status_label": "Durum",
                "created_at": "Olusturma"
            },
            hide_index=True
        )
        
        selected_offer = st.selectbox(
            "Teklif Detaylarini Goruntule",
            [""] + [o["offer_name"] for o in existing_offers]
        )
        if selected_offer:
            offer = next(o for o in existing_offers if o["offer_name"] == selected_offer)
            
            items_response = supabase.table("offer_items").select("*").eq("offer_id", offer["id"]).execute()
            items_data = items_response.data if items_response.data else []
            
            if "offer_items_df" not in st.session_state or st.session_state.get("current_offer") != offer["id"]:
                st.session_state.current_offer = offer["id"]
                if items_data:
                    st.session_state.offer_items_df = pd.DataFrame(items_data)
                else:
                    st.session_state.offer_items_df = pd.DataFrame(columns=[
                        "item_name", "quantity", "unit", "unit_price", 
                        "total_price", "notes"
                    ])
            
            edited_items_df = st.data_editor(
                st.session_state.offer_items_df,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "item_name": st.column_config.TextColumn("Kalem Adi", required=True),
                    "quantity": st.column_config.NumberColumn("Miktar", min_value=0.0, step=1.0, format="%.2f"),
                    "unit": st.column_config.SelectboxColumn(
                        "Birim",
                        options=["m²", "m³", "m", "adet", "ton", "kg", "lt", "km", "saat", "gun", "takim", "kalip"],
                        required=True
                    ),
                    "unit_price": st.column_config.NumberColumn("Birim Fiyat (TL)", min_value=0.0, step=0.01, format="%.2f"),
                    "total_price": st.column_config.NumberColumn("Toplam", disabled=True, format="%.2f"),
                    "notes": st.column_config.TextColumn("Notlar")
                },
                key="offer_items_grid"
            )
            
            if not edited_items_df.empty:
                edited_items_df["total_price"] = edited_items_df["quantity"].fillna(0) * edited_items_df["unit_price"].fillna(0)
                offer_total = edited_items_df["total_price"].sum()
                st.metric("Teklif Toplami", f"{offer_total:,.2f} TL")
            
            st.session_state.offer_items_df = edited_items_df
            
            if st.button("Kalemleri Kaydet", use_container_width=True):
                rows_to_save = edited_items_df.to_dict(orient="records") if not edited_items_df.empty else []
                clean_rows = [r for r in rows_to_save if str(r.get("item_name", "")).strip()]
                
                if clean_rows:
                    try:
                        with loading_spinner("Kalemler kaydediliyor..."):
                            supabase.table("offer_items").delete().eq("offer_id", offer["id"]).execute()
                            for r in clean_rows:
                                r["offer_id"] = offer["id"]
                                r.pop("id", None)
                                supabase.table("offer_items").insert(r).execute()
                            time.sleep(0.3)
                        toast_success("Basarili", "Kalemler kaydedildi!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        toast_error("Hata", f"Kayit hatasi: {e}")

# ==========================================
# TAB 2: KARSILASTIRMA
# ==========================================
with tab2:
    st.markdown("### Teklif Karsilastirma")
    
    if existing_offers and len(existing_offers) >= 2:
        offer_list = [o["offer_name"] for o in existing_offers]
        
        col1, col2 = st.columns(2)
        with col1:
            offer_a = st.selectbox("Teklif A", offer_list, key="comp_a")
        with col2:
            offer_b = st.selectbox("Teklif B", offer_list, key="comp_b", index=1 if len(offer_list) > 1 else 0)
        
        if offer_a and offer_b and offer_a != offer_b:
            offer_a_id = next(o["id"] for o in existing_offers if o["offer_name"] == offer_a)
            offer_b_id = next(o["id"] for o in existing_offers if o["offer_name"] == offer_b)
            
            items_a = supabase.table("offer_items").select("*").eq("offer_id", offer_a_id).execute().data or []
            items_b = supabase.table("offer_items").select("*").eq("offer_id", offer_b_id).execute().data or []
            
            if items_a and items_b:
                df_a = pd.DataFrame(items_a)
                df_b = pd.DataFrame(items_b)
                
                merged = pd.merge(
                    df_a[["item_name", "total_price"]],
                    df_b[["item_name", "total_price"]],
                    on="item_name",
                    how="outer",
                    suffixes=("_A", "_B")
                ).fillna(0)
                
                merged["Fark"] = merged["total_price_A"] - merged["total_price_B"]
                merged["Fark %"] = (merged["Fark"] / merged["total_price_B"] * 100).round(1)
                
                st.dataframe(merged, use_container_width=True, hide_index=True)
                
                total_a = merged["total_price_A"].sum()
                total_b = merged["total_price_B"].sum()
                diff = total_a - total_b
                diff_pct = (diff / total_b * 100) if total_b > 0 else 0
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"""
                    <div class="animate-card" style="
                        background-color: #141414;
                        padding: 0.8rem;
                        border-radius: 12px;
                        border: 1px solid #262626;
                        text-align: center;
                    ">
                        <p style="color: #737373; font-size: 0.6rem; margin: 0;">{offer_a}</p>
                        <h4 style="color: #3b82f6; margin: 0.2rem 0;">{total_a:,.2f} TL</h4>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="animate-card" style="
                        background-color: #141414;
                        padding: 0.8rem;
                        border-radius: 12px;
                        border: 1px solid #262626;
                        text-align: center;
                    ">
                        <p style="color: #737373; font-size: 0.6rem; margin: 0;">{offer_b}</p>
                        <h4 style="color: #22c55e; margin: 0.2rem 0;">{total_b:,.2f} TL</h4>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    diff_color = "#f87171" if diff < 0 else "#fbbf24"
                    st.markdown(f"""
                    <div class="animate-card" style="
                        background-color: #141414;
                        padding: 0.8rem;
                        border-radius: 12px;
                        border: 1px solid #262626;
                        text-align: center;
                    ">
                        <p style="color: #737373; font-size: 0.6rem; margin: 0;">Fark</p>
                        <h4 style="color: {diff_color}; margin: 0.2rem 0;">{diff:,.2f} TL</h4>
                        <p style="color: #737373; font-size: 0.6rem; margin: 0;">{diff_pct:.1f}%</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                toast_info("Bilgi", "Teklif kalemleri eksik.")
    else:
        toast_info("Bilgi", "Karsilastirma icin en az 2 teklif gerekli.")

# ==========================================
# TAB 3: TEKLIF RAPORU
# ==========================================
with tab3:
    st.markdown("### Teklif Raporu")
    
    if existing_offers:
        selected_offer = st.selectbox(
            "Rapor olusturulacak teklifi secin",
            [""] + [o["offer_name"] for o in existing_offers]
        )
        
        if selected_offer:
            offer = next(o for o in existing_offers if o["offer_name"] == selected_offer)
            items = supabase.table("offer_items").select("*").eq("offer_id", offer["id"]).execute().data or []
            
            if items:
                df = pd.DataFrame(items)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                st.markdown("""
                <div class="animate-card" style="
                    background-color: #141414;
                    padding: 1rem;
                    border-radius: 8px;
                    border: 1px solid #262626;
                    margin: 1rem 0;
                ">
                    <h4 style="color: #ffffff; margin: 0;">Rapor Ozeti</h4>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Toplam Kalem", len(df))
                with col2:
                    st.metric("Toplam Tutar", f"{df['total_price'].sum():,.2f} TL")
                with col3:
                    st.metric("Ortalama Birim Fiyat", f"{df['unit_price'].mean():,.2f} TL")
                
                if st.button("Rapor Olustur", use_container_width=True):
                    toast_info("Bilgi", "Teklif raporu PDF olarak olusturulacak.")
            else:
                toast_info("Bilgi", "Bu teklife ait kalem yok.")
    else:
        toast_info("Bilgi", "Once teklif olusturun.")

# ==========================================
# TAB 4: EXCEL BULK EDIT
# ==========================================
with tab4:
    st.markdown("### Excel Bulk Edit")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="animate-card" style="
            background-color: #141414;
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid #262626;
        ">
            <p style="color: #ffffff; font-weight: 600; margin: 0 0 0.5rem 0;">Excel Sablonunu Indir</p>
            <p style="color: #737373; margin: 0 0 0.3rem 0;">• Kalem adi, miktar, birim, birim fiyat</p>
            <p style="color: #737373; margin: 0 0 0.3rem 0;">• Toplam tutar otomatik hesaplanir</p>
            <p style="color: #737373; margin: 0 0 0.5rem 0;">• Diger giderler icin notlar alani</p>
        </div>
        """, unsafe_allow_html=True)
        
        def get_offer_template():
            """Bos teklif sablonu olustur"""
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df = pd.DataFrame(columns=[
                    "Kalem Adi", "Miktar", "Birim", "Birim Fiyat (TL)", 
                    "Toplam Tutar (TL)", "Notlar"
                ])
                # Ornek veri
                sample_data = [
                    ["Kazi Isleri", 1000, "m³", 150, 150000, ""],
                    ["Demir Isleri", 50, "ton", 18000, 900000, ""],
                    ["Beton Isleri", 500, "m³", 1200, 600000, ""],
                ]
                for row in sample_data:
                    df.loc[len(df)] = row
                df.to_excel(writer, sheet_name='Teklif_Kalemleri', index=False)
                
                # Ikinci sayfa: Diger Giderler
                df2 = pd.DataFrame(columns=[
                    "Gider Turu", "Aciklama", "Tutar (TL)", "Notlar"
                ])
                df2.to_excel(writer, sheet_name='Diger_Giderler', index=False)
                
            return output.getvalue()
        
        if st.button("Teklif Sablonu Indir", use_container_width=True):
            template_data = get_offer_template()
            st.download_button(
                label="Excel Sablonu Indir",
                data=template_data,
                file_name=f"SARCON_Teklif_Sablonu_{selected_project}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_template",
                use_container_width=True
            )
    
    with col2:
        st.markdown("""
        <div class="animate-card" style="
            background-color: #141414;
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid #262626;
        ">
            <p style="color: #ffffff; font-weight: 600; margin: 0 0 0.5rem 0;">Doldurulmus Excel'i Yukle</p>
            <p style="color: #737373; margin: 0 0 0.3rem 0;">Sablonu doldurduktan sonra buraya yukleyin.</p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Excel dosyasi secin",
            type=['xlsx'],
            key="offer_upload"
        )
        
        if uploaded_file:
            if st.button("Verileri Yukle", type="primary", use_container_width=True):
                try:
                    with loading_spinner("Veriler yukleniyor..."):
                        df = pd.read_excel(uploaded_file, sheet_name='Teklif_Kalemleri')
                        
                        # Verileri temizle
                        df = df.dropna(how='all')
                        df = df[df["Kalem Adi"].notna()]
                        
                        if df.empty:
                            toast_warning("Uyari", "Yuklenecek veri bulunamadi.")
                        else:
                            # Once mevcut teklifleri al
                            existing = supabase.table("project_offers").select("*").eq("project_id", project_id).execute()
                            existing_data = existing.data if existing.data else []
                            
                            # Yeni teklif olustur
                            offer_name = f"Bulk Import {datetime.date.today()}"
                            offer_data = {
                                "project_id": project_id,
                                "offer_name": offer_name,
                                "offer_date": str(datetime.date.today()),
                                "supplier": "Excel Import",
                                "total_amount": df["Toplam Tutar (TL)"].sum(),
                                "status": "active",
                                "notes": f"Excel'den ice aktarildi - {len(df)} kalem"
                            }
                            
                            offer_response = supabase.table("project_offers").insert(offer_data).execute()
                            offer_id = offer_response.data[0]["id"]
                            
                            # Kalemleri ekle
                            for _, row in df.iterrows():
                                item_data = {
                                    "offer_id": offer_id,
                                    "item_name": str(row["Kalem Adi"]),
                                    "quantity": float(row["Miktar"]) if pd.notna(row["Miktar"]) else 0,
                                    "unit": str(row["Birim"]) if pd.notna(row["Birim"]) else "",
                                    "unit_price": float(row["Birim Fiyat (TL)"]) if pd.notna(row["Birim Fiyat (TL)"]) else 0,
                                    "total_price": float(row["Toplam Tutar (TL)"]) if pd.notna(row["Toplam Tutar (TL)"]) else 0,
                                    "notes": str(row["Notlar"]) if pd.notna(row["Notlar"]) else ""
                                }
                                supabase.table("offer_items").insert(item_data).execute()
                            
                            # Diger giderleri de ekle (varsa)
                            try:
                                df_gider = pd.read_excel(uploaded_file, sheet_name='Diger_Giderler')
                                df_gider = df_gider.dropna(how='all')
                                if not df_gider.empty:
                                    for _, row in df_gider.iterrows():
                                        if pd.notna(row["Gider Turu"]):
                                            # Ozel bir tablo yoksa, notlara ekle
                                            pass
                            except:
                                pass
                            
                            time.sleep(0.3)
                    toast_success("Basarili", f"{len(df)} kalem basariyla ice aktarildi!")
                    st.cache_data.clear()
                    st.rerun()
                    
                except Exception as e:
                    toast_error("Hata", f"Yukleme hatasi: {e}")
                    
st.markdown('</div>', unsafe_allow_html=True)