
"""
Dashboard - SARCON Portal
Proje ozeti, metrikler, analizler ve aksiyon listesi
"""

import streamlit as st
import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import io
import base64
from utils.db import (
    get_user_projects, 
    supabase,
    get_actions,
    get_action_stats,
    create_action,
    update_action,
    delete_action,
    export_actions_to_excel,
    import_actions_from_excel
)
from utils.styles import apply_global_styles
from utils.top_navbar import render_top_navbar
from utils.animations import (
    apply_animations,
    animate_plotly,
    loading_spinner,
    toast_success,
    toast_error,
    toast_warning,
    toast_info
)

st.set_page_config(
    page_title="SARCON Portal | Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)


apply_global_styles(is_login=False)
apply_animations()
render_top_navbar()

st.markdown('<div class="page-content">', unsafe_allow_html=True)


st.markdown("""
<style>
.action-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    padding: 1.2rem;
    border-radius: 12px;
    border: 1px solid #262626;
    color: white;
    margin-bottom: 0.5rem;
    transition: all 0.3s ease;
}
.action-card:hover {
    transform: translateY(-2px);
    border-color: #3b82f6;
}
.action-card .count {
    font-size: 2rem;
    font-weight: 700;
    margin: 0.2rem 0;
}
.action-card .label {
    color: #a3a3a3;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.status-badge {
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 500;
    display: inline-block;
}
.status-open { background: #ffe5b4; color: #856404; }
.status-in-progress { background: #bbdefb; color: #0d47a1; }
.status-done { background: #c8e6c9; color: #1b5e20; }
.status-rejected { background: #ffcdd2; color: #b71c1c; }
.priority-high { background: #ff6b6b; color: white; }
.priority-medium { background: #ffd93d; color: #856404; }
.priority-low { background: #6bcb77; color: white; }
.action-table-container {
    background: #0a0a0a;
    padding: 1rem;
    border-radius: 10px;
    border: 1px solid #1a1a1a;
    margin-top: 0.5rem;
}
.edit-btn {
    background: #2563eb;
    color: white;
    border: none;
    padding: 4px 12px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.7rem;
}
.edit-btn:hover {
    background: #1d4ed8;
}
.delete-btn {
    background: #dc2626;
    color: white;
    border: none;
    padding: 4px 12px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.7rem;
}
.delete-btn:hover {
    background: #b91c1c;
}

.stButton > button {
    border: 1px solid #ffffff !important;
    border-radius: 6px !important;
}
.stButton > button:hover {
    border: 1px solid #3b82f6 !important;
}

div[data-testid="stSelectbox"] {
    width: 50% !important;
}

div[data-testid="stExpander"] {
    width: 75% !important;
}

div[data-testid="stMultiSelect"] {
    width: 50% !important;
}

div[data-testid="stExpander"]:last-of-type {
    margin-top: 20px !important;
}
</style>
""", unsafe_allow_html=True)


st.markdown("""
<div style="border-left: 3px solid #3b82f6; padding-left: 0.8rem; margin-bottom: 1.5rem;">
    <h3 style="color: #ffffff; font-weight: 600; margin: 0; font-size: 1.3rem;">Proje Ozeti</h3>
    <p style="color: #737373; margin: 0; font-size: 0.8rem;">Kaynak, ilerleme ve aksiyon verilerinin guncel analizi</p>
</div>
""", unsafe_allow_html=True)


with loading_spinner("Projeler yukleniyor..."):
    projects, err = get_user_projects()
    time.sleep(0.3)

project_names = [p["project_name"] for p in projects] if projects else []

if not project_names:
    toast_info("Bilgi", "Henuz bir proje olusturmadiniz. Veri Girisi sayfasindan proje olusturabilirsiniz.")
    st.stop()

col_proje1, col_proje2 = st.columns([1, 1])
with col_proje1:
    selected_project = st.selectbox("Proje Secin", project_names, label_visibility="collapsed")
with col_proje2:
    if st.button("Yeni Proje", use_container_width=True):
        st.switch_page("pages/02_Veri_Girisi.py")

project_id = next(p["id"] for p in projects if p["project_name"] == selected_project)


if "dashboard_prefs" not in st.session_state:
    st.session_state.dashboard_prefs = {
        "chart_type": "Bar",
        "show_metrics": ["endirect", "direct", "machine", "progress"],
        "time_range": "Son 30 Gun",
        "pivot_view": ["Personel - Is Turu"],
        "progress_period": "Proje Tamami"
    }


with loading_spinner("Veriler yukleniyor..."):
    try:
        res_response = supabase.table("daily_resources").select("*").eq("project_id", project_id).execute()
        resources_data = res_response.data if res_response.data else []
    except:
        resources_data = []

    try:
        work_response = supabase.table("daily_work_progress").select("*").eq("project_id", project_id).execute()
        work_data = work_response.data if work_response.data else []
    except:
        work_data = []

    try:
        items_response = supabase.table("project_items").select("*").eq("project_id", project_id).execute()
        items_data = items_response.data if items_response.data else []
    except:
        items_data = []

    try:
        costs_response = supabase.table("project_costs").select("*").eq("project_id", project_id).execute()
        costs_data = costs_response.data if costs_response.data else []
    except:
        costs_data = []
    
    try:
        cashflow_response = supabase.table("project_cashflow").select("*").eq("project_id", project_id).execute()
        cashflow_data = cashflow_response.data if cashflow_response.data else []
    except:
        cashflow_data = []
    
    actions_data, actions_err = get_actions(project_id)
    actions_df = pd.DataFrame(actions_data) if actions_data else pd.DataFrame()
    
    time.sleep(0.3)

df_resources = pd.DataFrame(resources_data) if resources_data else pd.DataFrame()
df_work = pd.DataFrame(work_data) if work_data else pd.DataFrame()
df_items = pd.DataFrame(items_data) if items_data else pd.DataFrame()
df_costs = pd.DataFrame(costs_data) if costs_data else pd.DataFrame()
df_cashflow = pd.DataFrame(cashflow_data) if cashflow_data else pd.DataFrame()


if not actions_df.empty:
    stats = {
        "total": len(actions_df),
        "open": len(actions_df[actions_df['status'].isin(['Acik', 'Devam Ediyor'])]),
        "completed": len(actions_df[actions_df['status'] == 'Tamamlandi']),
        "high": len(actions_df[actions_df['priority'] == 'Yuksek'])
    }
else:
    stats = {"total": 0, "open": 0, "completed": 0, "high": 0}

st.markdown("---")
st.markdown("#### Aksiyon Ozeti")

col_a1, col_a2, col_a3, col_a4 = st.columns(4)

with col_a1:
    st.markdown(f"""
    <div class="action-card">
        <div class="label">Toplam Aksiyon</div>
        <div class="count">{stats['total']}</div>
    </div>
    """, unsafe_allow_html=True)

with col_a2:
    st.markdown(f"""
    <div class="action-card" style="border-color: #ffd93d;">
        <div class="label">Acik / Devam Eden</div>
        <div class="count" style="color: #ffd93d;">{stats['open']}</div>
    </div>
    """, unsafe_allow_html=True)

with col_a3:
    st.markdown(f"""
    <div class="action-card" style="border-color: #6bcb77;">
        <div class="label">Tamamlanan</div>
        <div class="count" style="color: #6bcb77;">{stats['completed']}</div>
    </div>
    """, unsafe_allow_html=True)

with col_a4:
    st.markdown(f"""
    <div class="action-card" style="border-color: #ff6b6b;">
        <div class="label">Yuksek Oncelikli</div>
        <div class="count" style="color: #ff6b6b;">{stats['high']}</div>
    </div>
    """, unsafe_allow_html=True)


st.markdown("#### Aksiyon Listesi")


col_exp1, col_exp2, col_exp3 = st.columns([1, 1, 4])
with col_exp1:
    if not actions_df.empty:
        excel_data, err = export_actions_to_excel(actions_data)
        if excel_data:
            with open("aksiyon_listesi.xlsx", "rb") as f:
                st.download_button(
                    label="Excel Export",
                    data=f,
                    file_name=f"aksiyon_listesi_{selected_project}_{datetime.date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

with col_exp2:
    with st.expander("Excel Import"):
        uploaded_file = st.file_uploader(
            "Excel dosyasi secin",
            type=['xlsx', 'xls'],
            key="excel_import"
        )
        if uploaded_file is not None:
            if st.button("Iceri Aktar", type="primary"):
                with loading_spinner("Aksiyonlar iceri aktariliyor..."):
                    success, msg = import_actions_from_excel(uploaded_file, project_id, selected_project)
                    if success:
                        toast_success("Basari", msg)
                        st.rerun()
                    else:
                        toast_error("Hata", msg)

if not actions_df.empty:
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        status_filter = st.multiselect(
            "Durum",
            options=actions_df['status'].unique(),
            default=actions_df['status'].unique(),
            key="status_filter"
        )
    with col_f2:
        priority_filter = st.multiselect(
            "Oncelik",
            options=actions_df['priority'].unique(),
            default=actions_df['priority'].unique(),
            key="priority_filter"
        )
    with col_f3:
        assigned_filter = st.multiselect(
            "Atanan",
            options=actions_df['assigned_to'].unique(),
            default=actions_df['assigned_to'].unique(),
            key="assigned_filter"
        )
    
    filtered_df = actions_df[
        (actions_df['status'].isin(status_filter)) &
        (actions_df['priority'].isin(priority_filter)) &
        (actions_df['assigned_to'].isin(assigned_filter))
    ]
    
    if not filtered_df.empty:
        display_df = filtered_df[[
            'id', 'created_by', 'assigned_to', 'title', 'work_type',
            'description', 'project', 'created_date', 'updated_date',
            'status', 'priority'
        ]].copy()
        
        display_df.columns = [
            'ID', 'Olusturan', 'Atanan', 'Konu', 'Is Turu',
            'Aciklama', 'Proje', 'Olusturma', 'Guncelleme',
            'Durum', 'Oncelik'
        ]
        
        def format_status(val):
            classes = {
                'Acik': 'status-open',
                'Devam Ediyor': 'status-in-progress',
                'Tamamlandi': 'status-done',
                'Reddedildi': 'status-rejected'
            }
            return f'<span class="status-badge {classes.get(val, "status-open")}">{val}</span>'
        
        def format_priority(val):
            classes = {
                'Yuksek': 'priority-high',
                'Orta': 'priority-medium',
                'Dusuk': 'priority-low'
            }
            return f'<span class="status-badge {classes.get(val, "priority-medium")}">{val}</span>'
        
        st.dataframe(
            display_df,
            column_config={
                "ID": st.column_config.NumberColumn("ID", width="small"),
                "Olusturan": st.column_config.TextColumn("Olusturan", width="small"),
                "Atanan": st.column_config.TextColumn("Atanan", width="small"),
                "Konu": st.column_config.TextColumn("Konu", width="medium"),
                "Is Turu": st.column_config.TextColumn("Is Turu", width="small"),
                "Aciklama": st.column_config.TextColumn("Aciklama", width="large"),
                "Proje": st.column_config.TextColumn("Proje", width="small"),
                "Olusturma": st.column_config.DateColumn("Olusturma", width="small"),
                "Guncelleme": st.column_config.DateColumn("Guncelleme", width="small"),
                "Durum": st.column_config.TextColumn("Durum", width="small"),
                "Oncelik": st.column_config.TextColumn("Oncelik", width="small"),
            },
            hide_index=True,
            use_container_width=True,
            height=400
        )
        
        status_counts = filtered_df['status'].value_counts()
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            color=status_counts.index,
            color_discrete_map={
                'Acik': '#ffe5b4',
                'Devam Ediyor': '#bbdefb',
                'Tamamlandi': '#c8e6c9',
                'Reddedildi': '#ffcdd2'
            },
            hole=0.4
        )
        fig.update_layout(
            height=200,
            margin=dict(l=10, r=10, t=10, b=10),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
    else:
        st.info("Filtrelerle eslesen aksiyon bulunamadi.")
    
    with st.expander("Yeni Aksiyon Ekle", expanded=False):
        with st.form("new_action_form"):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                new_title = st.text_input("Konu *", placeholder="Aksiyon basligi")
                new_assigned = st.text_input("Atanan Kisi *", placeholder="Kisi adi")
                new_priority = st.selectbox("Oncelik", ['Yuksek', 'Orta', 'Dusuk'])
                new_status = st.selectbox("Durum", ['Acik', 'Devam Ediyor', 'Tamamlandi', 'Reddedildi'])
            with col_f2:
                new_work_type = st.text_input("Is Turu", placeholder="Orn: Veri Guncelleme")
                new_desc = st.text_area("Aciklama", placeholder="Detayli aciklama")
                new_created_by = st.text_input("Olusturan", placeholder="Kisi adi")
            
            submitted = st.form_submit_button("Olustur", type="primary")
            if submitted:
                if new_title and new_assigned:
                    action_data = {
                        "project_id": str(project_id),
                        "project": selected_project,
                        "created_by": new_created_by or st.session_state.get("user_email", "Sistem"),
                        "assigned_to": new_assigned,
                        "title": new_title,
                        "work_type": new_work_type or "Genel",
                        "description": new_desc or "",
                        "status": new_status,
                        "priority": new_priority,
                        "created_date": datetime.date.today().isoformat(),
                        "updated_date": datetime.date.today().isoformat()
                    }
                    result, err = create_action(action_data)
                    if result:
                        toast_success("Basari", "Aksiyon olusturuldu!")
                        st.rerun()
                    else:
                        toast_error("Hata", f"Aksiyon olusturulamadi: {err}")
                else:
                    toast_warning("Uyari", "Konu ve Atanan alanlari zorunludur.")
    
    with st.expander("Aksiyon Duzenle / Sil", expanded=False):
        action_ids = filtered_df['id'].tolist() if not filtered_df.empty else []
        if action_ids:
            selected_action_id = st.selectbox(
                "Duzenlenecek Aksiyon Secin",
                options=action_ids,
                format_func=lambda x: f"#{x} - {filtered_df[filtered_df['id']==x]['title'].iloc[0]}"
            )
            
            if selected_action_id:
                action_row = filtered_df[filtered_df['id'] == selected_action_id].iloc[0]
                
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    edit_title = st.text_input("Konu", value=action_row['title'])
                    edit_assigned = st.text_input("Atanan", value=action_row['assigned_to'])
                    edit_status = st.selectbox(
                        "Durum",
                        ['Acik', 'Devam Ediyor', 'Tamamlandi', 'Reddedildi'],
                        index=['Acik', 'Devam Ediyor', 'Tamamlandi', 'Reddedildi'].index(action_row['status'])
                    )
                with col_e2:
                    edit_priority = st.selectbox(
                        "Oncelik",
                        ['Yuksek', 'Orta', 'Dusuk'],
                        index=['Yuksek', 'Orta', 'Dusuk'].index(action_row['priority'])
                    )
                    edit_work_type = st.text_input("Is Turu", value=action_row.get('work_type', ''))
                    edit_desc = st.text_area("Aciklama", value=action_row.get('description', ''))
                
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    if st.button("Guncelle", type="primary", use_container_width=True):
                        update_data = {
                            "title": edit_title,
                            "assigned_to": edit_assigned,
                            "status": edit_status,
                            "priority": edit_priority,
                            "work_type": edit_work_type,
                            "description": edit_desc,
                            "updated_date": datetime.date.today().isoformat()
                        }
                        result, err = update_action(selected_action_id, update_data)
                        if result:
                            toast_success("Basari", "Aksiyon guncellendi!")
                            st.rerun()
                        else:
                            toast_error("Hata", f"Guncelleme basarisiz: {err}")
                
                with col_b2:
                    if st.button("Sil", type="secondary", use_container_width=True):
                        if st.checkbox("Silmek istediginize emin misiniz?"):
                            result, err = delete_action(selected_action_id)
                            if result:
                                toast_success("Basari", "Aksiyon silindi!")
                                st.rerun()
                            else:
                                toast_error("Hata", f"Silme basarisiz: {err}")
        else:
            st.info("Duzenlenecek aksiyon bulunmuyor.")

else:
    st.info("Bu projeye ait henuz aksiyon bulunmuyor.")


endirect_total = 0
endirect_avg = 0
direct_total = 0
direct_avg = 0
machine_total = 0
machine_avg = 0

if not df_resources.empty:
    endirect_df = df_resources[df_resources['category'] == 'Endirekt Personel']
    if not endirect_df.empty:
        endirect_total = endirect_df['value'].sum()
        endirect_avg = endirect_df['value'].mean()
    
    direct_df = df_resources[df_resources['category'] == 'Direkt Personel']
    if not direct_df.empty:
        direct_total = direct_df['value'].sum()
        direct_avg = direct_df['value'].mean()
    
    machine_df = df_resources[df_resources['category'] == 'Makina']
    if not machine_df.empty:
        machine_total = machine_df['value'].sum()
        machine_avg = machine_df['value'].mean()

total_quantity = 0
total_completed = 0
avg_progress = 0

if not df_items.empty:
    total_quantity = df_items['quantity'].sum() if 'quantity' in df_items.columns else 0
    total_completed = df_items['completed_quantity'].sum() if 'completed_quantity' in df_items.columns else 0
    if total_quantity > 0:
        avg_progress = (total_completed / total_quantity) * 100

completed_tasks = 0
if not df_work.empty and 'ilerleme_yuzdesi' in df_work.columns:
    completed_tasks = len(df_work[df_work['ilerleme_yuzdesi'] >= 100])

total_cost = 0
total_revenue = 0

if not df_costs.empty:
    total_cost = df_costs['total_price'].sum() if 'total_price' in df_costs.columns else 0

if not df_items.empty and 'unit_price' in df_items.columns and 'completed_quantity' in df_items.columns:
    df_items['revenue'] = df_items['unit_price'] * df_items['completed_quantity']
    total_revenue = df_items['revenue'].sum()


st.markdown("---")
st.markdown("#### Finansal ve Fiziksel Metrikler")

col_m1, col_m2, col_m3, col_m4 = st.columns(4)

with col_m1:
    st.markdown(f"""
    <div class="action-card">
        <div class="label">Fiziksel Ilerleme</div>
        <div class="count" style="color: #3b82f6;">%{avg_progress:.1f}</div>
    </div>
    """, unsafe_allow_html=True)

with col_m2:
    st.markdown(f"""
    <div class="action-card" style="border-color: #ef4444;">
        <div class="label">Gerceklesen Maliyet</div>
        <div class="count" style="color: #ef4444;">{total_cost:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

with col_m3:
    st.markdown(f"""
    <div class="action-card" style="border-color: #22c55e;">
        <div class="label">Gerceklesen Gelir</div>
        <div class="count" style="color: #22c55e;">{total_revenue:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

with col_m4:
    if total_cost > 0:
        profit_margin = ((total_revenue - total_cost) / total_cost) * 100
    else:
        profit_margin = 0
    st.markdown(f"""
    <div class="action-card" style="border-color: #a78bfa;">
        <div class="label">Kar Marj</div>
        <div class="count" style="color: #a78bfa;">%{profit_margin:.1f}</div>
    </div>
    """, unsafe_allow_html=True)


st.markdown("---")
st.markdown("#### Fiziksel Ilerleme Grafigi")

col_period1, col_period2 = st.columns([1, 3])
with col_period1:
    progress_period = st.selectbox(
        "Periyot Secin",
        ["Gunluk", "Haftalik", "Aylik", "Proje Tamami"],
        index=["Gunluk", "Haftalik", "Aylik", "Proje Tamami"].index(
            st.session_state.dashboard_prefs.get("progress_period", "Proje Tamami")
        ),
        label_visibility="collapsed"
    )
    st.session_state.dashboard_prefs["progress_period"] = progress_period

with col_period2:
    if not df_work.empty and 'report_date' in df_work.columns and 'ilerleme_yuzdesi' in df_work.columns:
        df_work['report_date'] = pd.to_datetime(df_work['report_date'])
        
        if progress_period == "Gunluk":
            progress_data = df_work.groupby('report_date')['ilerleme_yuzdesi'].mean().reset_index()
            period_label = "Gun"
        elif progress_period == "Haftalik":
            df_work['hafta'] = df_work['report_date'].dt.isocalendar().week
            progress_data = df_work.groupby('hafta')['ilerleme_yuzdesi'].mean().reset_index()
            progress_data['hafta'] = progress_data['hafta'].astype(str) + ". Hafta"
            period_label = "Hafta"
        elif progress_period == "Aylik":
            df_work['ay'] = df_work['report_date'].dt.strftime('%Y-%m')
            progress_data = df_work.groupby('ay')['ilerleme_yuzdesi'].mean().reset_index()
            period_label = "Ay"
        else:
            progress_data = pd.DataFrame({
                'Donem': ['Proje Tamami'],
                'Ilerleme': [avg_progress]
            })
            period_label = "Donem"
        
        if progress_period != "Proje Tamami":
            progress_data = progress_data.sort_values(progress_data.columns[0])
            fig = px.bar(
                progress_data,
                x=progress_data.columns[0],
                y='ilerleme_yuzdesi',
                title=f'{progress_period} Fiziksel Ilerleme',
                labels={'ilerleme_yuzdesi': 'Ilerleme %', progress_data.columns[0]: period_label},
                color_discrete_sequence=['#3b82f6']
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=10, r=10, t=40, b=10),
                height=300,
                xaxis=dict(showgrid=False, color='#a3a3a3'),
                yaxis=dict(showgrid=True, gridcolor='#1f1f1f', color='#a3a3a3')
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.metric(
                label="Proje Tamami Fiziksel Ilerleme",
                value=f"%{avg_progress:.1f}",
                delta=f"{total_completed:.1f} / {total_quantity:.1f} birim tamamlandi" if total_quantity > 0 else None
            )
    else:
        toast_info("Bilgi", "Henuz ilerleme verisi bulunmuyor.")


st.markdown("---")
st.markdown("#### Toplam Adam-Saat Grafigi")

if not df_resources.empty and 'report_date' in df_resources.columns and 'value' in df_resources.columns:
    df_resources['report_date'] = pd.to_datetime(df_resources['report_date'])
    personel_df = df_resources[df_resources['category'].isin(['Direkt Personel', 'Endirekt Personel'])].copy()
    
    if not personel_df.empty:
        personel_df['adamsaat'] = personel_df['value'] * 8
        daily_manhours = personel_df.groupby('report_date')['adamsaat'].sum().reset_index()
        daily_manhours = daily_manhours.sort_values('report_date')
        daily_manhours['report_date_str'] = daily_manhours['report_date'].dt.strftime('%Y-%m-%d')
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily_manhours['report_date_str'],
            y=daily_manhours['adamsaat'],
            mode='lines+markers',
            name='Toplam Adam-Saat',
            line=dict(color='#3b82f6', width=2.5),
            marker=dict(color='#3b82f6', size=8)
        ))
        
        fig.update_layout(
            title='Gunluk Toplam Adam-Saat',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=40, b=10),
            height=300,
            xaxis=dict(showgrid=False, color='#a3a3a3', title='Tarih'),
            yaxis=dict(showgrid=True, gridcolor='#1f1f1f', color='#a3a3a3', title='Adam-Saat')
        )
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        total_manhours = daily_manhours['adamsaat'].sum()
        avg_manhours = daily_manhours['adamsaat'].mean()
        
        col_mh1, col_mh2 = st.columns(2)
        with col_mh1:
            st.metric("Toplam Adam-Saat", f"{total_manhours:,.0f}")
        with col_mh2:
            st.metric("Ortalama Gunluk Adam-Saat", f"{avg_manhours:,.1f}")
    else:
        toast_info("Bilgi", "Personel verisi bulunmuyor. Adam-saat grafigi gosterilemiyor.")
else:
    toast_info("Bilgi", "Kaynak verisi bulunmuyor.")


# ==========================================
# NAKIT AKISI GRAFIKLERI (Dashboard)
# ==========================================
st.markdown("---")
st.markdown("#### Nakit Akisi Analizi")

if not df_cashflow.empty:
    # Verileri düzenle
    df_cashflow['period_date'] = pd.to_datetime(df_cashflow['period_date'])
    df_cashflow = df_cashflow.sort_values('period_date')
    
    # Planlanan vs Gerceklesen Net Nakit
    fig_cash = go.Figure()
    
    fig_cash.add_trace(go.Scatter(
        x=df_cashflow['period_date'],
        y=df_cashflow['planned_inflow'] - df_cashflow['planned_outflow'],
        name="Planlanan Net",
        line=dict(color="#3b82f6", width=2)
    ))
    
    fig_cash.add_trace(go.Scatter(
        x=df_cashflow['period_date'],
        y=df_cashflow['actual_inflow'] - df_cashflow['actual_outflow'],
        name="Gerceklesen Net",
        line=dict(color="#34d399", width=2)
    ))
    
    fig_cash.add_trace(go.Bar(
        x=df_cashflow['period_date'],
        y=df_cashflow['actual_inflow'] - df_cashflow['actual_outflow'],
        name="Gerceklesen Net (Bar)",
        marker_color="#34d399",
        opacity=0.3,
        yaxis="y2"
    ))
    
    fig_cash.update_layout(
        title="Planlanan vs Gerceklesen Net Nakit",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=350,
        showlegend=True,
        legend=dict(font=dict(color="white"), orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        xaxis=dict(
            tickfont=dict(color="white"),
            gridcolor="#262626",
            title="Donem"
        ),
        yaxis=dict(
            title="Net Nakit",
            tickfont=dict(color="white"),
            gridcolor="#262626"
        ),
        yaxis2=dict(
            overlaying="y",
            side="right",
            showgrid=False
        )
    )
    
    st.plotly_chart(fig_cash, use_container_width=True, config={'displayModeBar': False})
    
    # Kumulatif Nakit Grafigi
    fig_cum = go.Figure()
    
    fig_cum.add_trace(go.Scatter(
        x=df_cashflow['period_date'],
        y=df_cashflow['cumulative_cash'],
        name="Kumulatif Nakit",
        line=dict(color="#a78bfa", width=2.5),
        fill='tozeroy',
        fillcolor='rgba(167, 139, 250, 0.2)'
    ))
    
    fig_cum.update_layout(
        title="Kumulatif Nakit Akisi",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=250,
        showlegend=True,
        legend=dict(font=dict(color="white"), orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        xaxis=dict(
            tickfont=dict(color="white"),
            gridcolor="#262626",
            title="Donem"
        ),
        yaxis=dict(
            title="Kumulatif Nakit",
            tickfont=dict(color="white"),
            gridcolor="#262626"
        )
    )
    
    st.plotly_chart(fig_cum, use_container_width=True, config={'displayModeBar': False})
    
    # Özet metrikler
    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
    
    with col_c1:
        total_planned_inflow = df_cashflow['planned_inflow'].sum()
        st.metric(
            "Toplam Planlanan Giris",
            f"{total_planned_inflow:,.0f}"
        )
    
    with col_c2:
        total_actual_inflow = df_cashflow['actual_inflow'].sum()
        st.metric(
            "Toplam Gerceklesen Giris",
            f"{total_actual_inflow:,.0f}"
        )
    
    with col_c3:
        variance = total_actual_inflow - total_planned_inflow
        variance_pct = (variance / total_planned_inflow * 100) if total_planned_inflow > 0 else 0
        st.metric(
            "Giris Sapmasi",
            f"{variance:,.0f}",
            delta=f"%{variance_pct:.1f}"
        )
    
    with col_c4:
        cumulative_actual = df_cashflow['cumulative_cash'].iloc[-1] if not df_cashflow.empty else 0
        st.metric(
            "Kumulatif Nakit (Gercek)",
            f"{cumulative_actual:,.0f}"
        )
    
    # Detay tablosu
    with st.expander("Nakit Akisi Detay Tablosu", expanded=False):
        display_cashflow = df_cashflow[['period_date', 'planned_inflow', 'actual_inflow', 
                                         'planned_outflow', 'actual_outflow', 'cumulative_cash']].copy()
        display_cashflow.columns = ['Donem', 'Planlanan Giris', 'Gerceklesen Giris',
                                     'Planlanan Cikis', 'Gerceklesen Cikis', 'Kumulatif Nakit']
        st.dataframe(display_cashflow, use_container_width=True)
        
else:
    toast_info("Bilgi", "Nakit akisi verisi bulunmuyor. Veri Girisi sayfasindan nakit akisi ekleyebilirsiniz.")


st.markdown("---")
st.markdown("""
<div style="border-left: 3px solid #3b82f6; padding-left: 0.8rem; margin-bottom: 1rem;">
    <h4 style="color: #ffffff; font-weight: 500; margin: 0; font-size: 1.1rem;">Ozetsel Tablolar</h4>
</div>
""", unsafe_allow_html=True)

with st.expander("Ozetsel Tablo Ayarlari", expanded=False):
    col_pivot1, col_pivot2, col_pivot3 = st.columns([1, 2, 1])
    with col_pivot1:
        pivot_options = st.multiselect(
            "Gosterilecek Tablolar",
            options=["Personel - Is Turu", "Personel - Tarih", "Makina - Tarih", "Is Turu - Ilerleme", "Bolge - Ilerleme"],
            default=st.session_state.dashboard_prefs.get("pivot_view", ["Personel - Is Turu"]),
            key="pivot_multiselect"
        )
        st.session_state.dashboard_prefs["pivot_view"] = pivot_options

if not df_work.empty and not df_resources.empty:
    pivot_dataframes = {}
    
    if "Personel - Is Turu" in pivot_options:
        personel_df = df_resources[df_resources['category'].isin(['Endirekt Personel', 'Direkt Personel'])]
        if not personel_df.empty:
            pivot_data = personel_df.groupby('category')['value'].sum().reset_index()
            pivot_data.columns = ['Personel Turu', 'Toplam']
            pivot_dataframes["Personel - Is Turu"] = pivot_data
    
    if "Personel - Tarih" in pivot_options:
        personel_df = df_resources[df_resources['category'].isin(['Endirekt Personel', 'Direkt Personel'])]
        if not personel_df.empty:
            pivot_data = personel_df.groupby(['report_date', 'category'])['value'].sum().unstack().fillna(0)
            pivot_dataframes["Personel - Tarih"] = pivot_data
    
    if "Makina - Tarih" in pivot_options:
        machine_df = df_resources[df_resources['category'] == 'Makina']
        if not machine_df.empty:
            pivot_data = machine_df.groupby(['report_date', 'item_name'])['value'].sum().unstack().fillna(0)
            pivot_dataframes["Makina - Tarih"] = pivot_data
    
    if "Is Turu - Ilerleme" in pivot_options:
        if not df_work.empty:
            pivot_data = df_work.groupby('is_turu')['ilerleme_yuzdesi'].agg(['mean', 'count']).reset_index()
            pivot_data.columns = ['Is Turu', 'Ortalama Ilerleme %', 'Kalem Sayisi']
            pivot_dataframes["Is Turu - Ilerleme"] = pivot_data
    
    if "Bolge - Ilerleme" in pivot_options:
        if not df_work.empty and 'bolge' in df_work.columns:
            pivot_data = df_work.groupby('bolge')['ilerleme_yuzdesi'].mean().reset_index()
            pivot_data.columns = ['Bolge', 'Ortalama Ilerleme %']
            pivot_dataframes["Bolge - Ilerleme"] = pivot_data
    
    for title, data in pivot_dataframes.items():
        st.markdown(f"**{title}**")
        st.dataframe(data, use_container_width=True)
        st.markdown("---")
else:
    toast_info("Bilgi", "Tablo verisi bulunamadi.")


if not df_work.empty:
    st.markdown("---")
    st.markdown("""
    <div style="border-left: 3px solid #3b82f6; padding-left: 0.8rem; margin-bottom: 1rem;">
        <h4 style="color: #ffffff; font-weight: 500; margin: 0; font-size: 1.1rem;">Is Ilerleme Ozeti</h4>
    </div>
    """, unsafe_allow_html=True)
    
    col_w1, col_w2, col_w3 = st.columns(3)
    
    with col_w1:
        st.markdown(f"""
        <div class="animate-card" style="
            background-color: #141414;
            padding: 1rem;
            border-radius: 12px;
            border: 1px solid #262626;
            text-align: center;
        ">
            <p style="color: #737373; font-size: 0.7rem; margin: 0;">Toplam Is Kalemi</p>
            <h3 style="color: #ffffff; margin: 0.2rem 0;">{len(df_work)}</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col_w2:
        st.markdown(f"""
        <div class="animate-card" style="
            background-color: #141414;
            padding: 1rem;
            border-radius: 12px;
            border: 1px solid #262626;
            text-align: center;
        ">
            <p style="color: #737373; font-size: 0.7rem; margin: 0;">Tamamlanan Is</p>
            <h3 style="color: #22c55e; margin: 0.2rem 0;">{completed_tasks}</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col_w3:
        st.markdown(f"""
        <div class="animate-card" style="
            background-color: #141414;
            padding: 1rem;
            border-radius: 12px;
            border: 1px solid #262626;
            text-align: center;
        ">
            <p style="color: #737373; font-size: 0.7rem; margin: 0;">Ortalama Ilerleme</p>
            <h3 style="color: #3b82f6; margin: 0.2rem 0;">{df_work['ilerleme_yuzdesi'].mean():.1f}%</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with st.expander("Son 10 Is Ilerleme Kaydi", expanded=False):
        if 'report_date' in df_work.columns and 'yapilan_is' in df_work.columns:
            st.dataframe(
                df_work.tail(10)[['report_date', 'yapilan_is', 'is_turu', 'ilerleme_yuzdesi', 'kesif_miktari', 'yapilan_miktar']],
                use_container_width=True,
                column_config={
                    'report_date': 'Tarih',
                    'yapilan_is': 'Yapilan Is',
                    'is_turu': 'Is Turu',
                    'ilerleme_yuzdesi': 'Ilerleme %',
                    'kesif_miktari': 'Kesif',
                    'yapilan_miktar': 'Yapilan'
                }
            )

st.markdown('</div>', unsafe_allow_html=True)