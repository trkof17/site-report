# -*- coding: utf-8 -*-
"""
Created on Wed Aug 12 05:41:47 2026

@author: taric
"""

import pandas as pd
import numpy as np
from datetime import datetime

def load_excel(file):
    """Excel/CSV dosyasını okur, temizler ve DataFrame döndürür"""
    try:
        if file.name.endswith('.xlsx') or file.name.endswith('.xls'):
            df = pd.read_excel(file)
        elif file.name.endswith('.csv'):
            df = pd.read_csv(file, encoding='utf-8')
        else:
            return None, "Desteklenmeyen dosya formatı. Lütfen .xlsx, .xls veya .csv yükleyin."
        
        # Boş satırları ve sütunları temizle
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        # Sütun isimlerini standartlaştır (küçük harf, boşluk yerine _)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        return df, None
    except Exception as e:
        return None, f"Dosya okuma hatası: {str(e)}"

def detect_errors(df):
    """5 temel hatayı tespit eder"""
    errors = {
        'missing_dates': [],
        'negative_values': [],
        'text_in_numeric': [],
        'date_order': [],
        'blank_activities': []
    }
    
    # 1. Eksik tarih
    if 'date' in df.columns:
        for idx, val in enumerate(df['date']):
            if pd.isna(val) or str(val).strip() == '':
                errors['missing_dates'].append(idx + 2)
    
    # 2. Negatif değerler
    numeric_cols = ['planned_manpower', 'actual_manpower', 'planned_machine_hours', 
                    'actual_machine_hours', 'planned_quantity', 'actual_quantity', 'cost']
    for col in numeric_cols:
        if col in df.columns:
            for idx, val in enumerate(df[col]):
                if pd.notna(val) and isinstance(val, (int, float)) and val < 0:
                    errors['negative_values'].append({'row': idx + 2, 'col': col, 'val': val})
    
    # 3. Sayısal sütunlarda metin
    for col in numeric_cols:
        if col in df.columns:
            for idx, val in enumerate(df[col]):
                if pd.notna(val) and not isinstance(val, (int, float)):
                    try:
                        float(str(val).replace(',', '.'))
                    except:
                        errors['text_in_numeric'].append({'row': idx + 2, 'col': col, 'val': str(val)[:30]})
    
    # 4. Tarih sıralaması (start_date > finish_date)
    if 'start_date' in df.columns and 'finish_date' in df.columns:
        for idx in range(len(df)):
            start = df['start_date'].iloc[idx]
            finish = df['finish_date'].iloc[idx]
            if pd.notna(start) and pd.notna(finish):
                try:
                    if pd.to_datetime(start) > pd.to_datetime(finish):
                        errors['date_order'].append({'row': idx + 2, 'start': start, 'finish': finish})
                except:
                    pass
    
    # 5. Boş aktivite
    if 'activity' in df.columns:
        for idx, val in enumerate(df['activity']):
            if pd.isna(val) or str(val).strip() == '':
                errors['blank_activities'].append(idx + 2)
    
    return errors

def calculate_metrics(df):
    """Metrikleri hesaplar"""
    metrics = {
        'total_manhours': 0,
        'total_machine_hours': 0,
        'schedule_variance': None,
        'completion_percentage': None,
        'trade_data': {}
    }
    
    if 'actual_manpower' in df.columns:
        metrics['total_manhours'] = df['actual_manpower'].sum()
    
    if 'actual_machine_hours' in df.columns:
        metrics['total_machine_hours'] = df['actual_machine_hours'].sum()
    
    if 'start_date' in df.columns and 'finish_date' in df.columns:
        try:
            planned = (pd.to_datetime(df['finish_date']) - pd.to_datetime(df['start_date'])).dt.days.mean()
            if not pd.isna(planned):
                metrics['schedule_variance'] = planned
        except:
            pass
    
    if 'planned_quantity' in df.columns and 'actual_quantity' in df.columns:
        planned_total = df['planned_quantity'].sum()
        actual_total = df['actual_quantity'].sum()
        if planned_total > 0:
            metrics['completion_percentage'] = (actual_total / planned_total) * 100
    
    if 'trade' in df.columns and 'planned_manpower' in df.columns and 'actual_manpower' in df.columns:
        trade_df = df.groupby('trade').agg({
            'planned_manpower': 'sum',
            'actual_manpower': 'sum'
        }).dropna()
        if not trade_df.empty:
            metrics['trade_data'] = {
                'trades': trade_df.index.tolist(),
                'planned': trade_df['planned_manpower'].tolist(),
                'actual': trade_df['actual_manpower'].tolist()
            }
    
    return metrics
