# -*- coding: utf-8 -*-
"""
Created on Thu Aug 20 02:13:00 2026
@author: taric
Updated: 2026-08-22 - Birim sütunu disabled olarak güncellendi
"""

import streamlit as st
import datetime
import pandas as pd
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
    page_title="SARCON Portal | Hakedis",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

apply_global_styles(is_login=False)
render_top_navbar()

st.markdown('<div class="page-content">', unsafe_allow_html=True)

st.markdown("""
<div style="border-left: 3px solid #3b82f6; padding-left: 0.8rem; margin-bottom: 1.5rem;">
    <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.3rem;">Hakedis Olustur</h3>
    <p style="color: #737373; margin: 0; font-size: 0.8rem;">Kesif ve gunluk rapor verilerine gore hakedis olusturun</p>
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

# Donem secimi
col1, col2 = st.columns(2)
with col1:
    period_start = st.date_input("Donem Baslangic", datetime.date.today().replace(day=1))
with col2:
    period_end = st.date_input("Donem Bitis", datetime.date.today())

# Hakedis olustur butonu
if st.button("Hakedis Olustur", type="primary", use_container_width=True):
    with loading_spinner("Hakedis olusturuluyor..."):
        try:
            items_response = supabase.table("project_items").select("*").eq("project_id", project_id).execute()
            items_data = items_response.data if items_response.data else []
            
            if not items_data:
                toast_warning("Uyari", "Once kesif kalemlerini girin.")
                st.stop()
            
            reports_response = supabase.table("daily_reports").select("*").eq("project_id", project_id).execute()
            reports_data = reports_response.data if reports_response.data else []
            
            prev_response = supabase.table("project_payments").select("*").eq("project_id", project_id).execute()
            prev_payments = prev_response.data if prev_response.data else []
            prev_df = pd.DataFrame(prev_payments) if prev_payments else pd.DataFrame()
            
            payment_rows = []
            for item in items_data:
                item_reports = [r for r in reports_data if r.get('activity', '').lower() == item.get('item_name', '').lower()]
                completed_quantity = sum([r.get('actual_quantity', 0) for r in item_reports])
                
                prev_quantity = 0
                if not prev_df.empty:
                    prev_item = prev_df[prev_df['item_id'] == item['id']]
                    if not prev_item.empty:
                        prev_quantity = prev_item.iloc[0].get('cumulative_quantity', 0)
                
                period_quantity = completed_quantity - prev_quantity
                period_amount = period_quantity * item.get('unit_price', 0)
                cumulative_amount = completed_quantity * item.get('unit_price', 0)
                
                payment_rows.append({
                    'item_id': item['id'],
                    'item_name': item['item_name'],
                    'unit': item.get('unit', ''),
                    'total_quantity': item.get('quantity', 0),
                    'completed_quantity': completed_quantity,
                    'previous_quantity': prev_quantity,
                    'period_quantity': period_quantity,
                    'unit_price': item.get('unit_price', 0),
                    'period_amount': period_amount,
                    'cumulative_amount': cumulative_amount,
                    'status': 'draft'
                })
            
            df_payment = pd.DataFrame(payment_rows)
            st.session_state.payment_df = df_payment
            toast_success("Basarili", f"{len(df_payment)} kalem icin hakedis olusturuldu!")
            time.sleep(0.3)
            st.rerun()
            
        except Exception as e:
            toast_error("Hata", f"Hakedis olusturulurken hata olustu: {e}")

# Hakedis tablosu
if "payment_df" in st.session_state and not st.session_state.payment_df.empty:
    st.markdown("---")
    st.markdown("### Hakedis Ozeti")
    
    df = st.session_state.payment_df
    
    total_period = df['period_amount'].sum()
    total_cumulative = df['cumulative_amount'].sum()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="animate-card" style="
            background-color: #141414;
            padding: 1rem;
            border-radius: 12px;
            border: 1px solid #262626;
            text-align: center;
        ">
            <p style="color: #737373; font-size: 0.7rem; margin: 0;">Toplam Kalem</p>
            <h3 style="color: #ffffff; margin: 0.2rem 0;">{len(df)}</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="animate-card" style="
            background-color: #141414;
            padding: 1rem;
            border-radius: 12px;
            border: 1px solid #262626;
            text-align: center;
        ">
            <p style="color: #737373; font-size: 0.7rem; margin: 0;">Donem Tutari</p>
            <h3 style="color: #3b82f6; margin: 0.2rem 0;">{total_period:,.0f} TL</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="animate-card" style="
            background-color: #141414;
            padding: 1rem;
            border-radius: 12px;
            border: 1px solid #262626;
            text-align: center;
        ">
            <p style="color: #737373; font-size: 0.7rem; margin: 0;">Kumulatif Tutar</p>
            <h3 style="color: #22c55e; margin: 0.2rem 0;">{total_cumulative:,.0f} TL</h3>
        </div>
        """, unsafe_allow_html=True)
    
    st.dataframe(
        df,
        use_container_width=True,
        column_config={
            'item_name': 'Is Kalemi',
            'unit': st.column_config.TextColumn("Birim", disabled=True),
            'total_quantity': 'Kesif Miktari',
            'completed_quantity': 'Tamamlanan',
            'previous_quantity': 'Onceki Donem',
            'period_quantity': 'Bu Donem',
            'unit_price': 'Birim Fiyat',
            'period_amount': 'Donem Tutari',
            'cumulative_amount': 'Kumulatif',
            'status': 'Durum'
        },
        hide_index=True
    )
    
    if st.button("Hakedisi Kaydet", type="primary", use_container_width=True):
        try:
            with loading_spinner("Hakedis kaydediliyor..."):
                rows_to_save = df.to_dict(orient="records")
                for r in rows_to_save:
                    r['project_id'] = project_id
                    r['payment_period'] = str(period_start)
                    r.pop('id', None)
                
                supabase.table("project_payments").insert(rows_to_save).execute()
                time.sleep(0.3)
            toast_success("Basarili", "Hakedis basariyla kaydedildi!")
            st.session_state.payment_df = pd.DataFrame()
            st.rerun()
          
        except Exception as e:
            toast_error("Hata", f"Kayit sirasinda hata olustu: {e}")

else:
    toast_info("Bilgi", "Hakedis olusturmak icin 'Hakedis Olustur' butonuna tiklayin.")
    
st.markdown('</div>', unsafe_allow_html=True)