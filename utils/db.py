import pandas as pd
import datetime
from .supabase_client import get_supabase

def create_project(project_name, start_date=None, end_date=None):
    supabase = get_supabase()
    try:
        data = {
            "project_name": project_name,
            "start_date": start_date,
            "end_date": end_date
        }
        response = supabase.table("projects").insert(data).execute()
        return response.data[0], None
    except Exception as e:
        return None, str(e)

def add_daily_report(project_id, report_date, activity, trade, planned_manpower, actual_manpower,
                     planned_machine_hours, actual_machine_hours, planned_quantity, actual_quantity,
                     cost, notes):
    supabase = get_supabase()
    try:
        data = {
            "project_id": project_id,
            "report_date": report_date,
            "activity": activity,
            "trade": trade,
            "planned_manpower": planned_manpower,
            "actual_manpower": actual_manpower,
            "planned_machine_hours": planned_machine_hours,
            "actual_machine_hours": actual_machine_hours,
            "planned_quantity": planned_quantity,
            "actual_quantity": actual_quantity,
            "cost": cost,
            "notes": notes
        }
        response = supabase.table("daily_reports").insert(data).execute()
        return response.data[0], None
    except Exception as e:
        return None, str(e)

def get_user_projects():
    supabase = get_supabase()
    try:
        response = supabase.table("projects").select("*").execute()
        return response.data, None
    except Exception as e:
        return None, str(e)

def add_bulk_reports(project_id, df):
    """
    DataFrame'deki tüm satırları toplu olarak daily_reports tablosuna ekler.
    """
    supabase = get_supabase()
    try:
        records = []
        for _, row in df.iterrows():
            record = {
                "project_id": project_id,
                "report_date": str(row.get('date', datetime.date.today())),
                "activity": str(row.get('activity', '')) if pd.notna(row.get('activity')) else None,
                "trade": str(row.get('trade', '')) if pd.notna(row.get('trade')) else None,
                "planned_manpower": int(row.get('planned_manpower', 0)) if pd.notna(row.get('planned_manpower')) else 0,
                "actual_manpower": int(row.get('actual_manpower', 0)) if pd.notna(row.get('actual_manpower')) else 0,
                "planned_machine_hours": float(row.get('planned_machine_hours', 0)) if pd.notna(row.get('planned_machine_hours')) else 0.0,
                "actual_machine_hours": float(row.get('actual_machine_hours', 0)) if pd.notna(row.get('actual_machine_hours')) else 0.0,
                "planned_quantity": float(row.get('planned_quantity', 0)) if pd.notna(row.get('planned_quantity')) else 0.0,
                "actual_quantity": float(row.get('actual_quantity', 0)) if pd.notna(row.get('actual_quantity')) else 0.0,
                "cost": float(row.get('cost', 0)) if pd.notna(row.get('cost')) else 0.0,
                "notes": str(row.get('notes', '')) if pd.notna(row.get('notes')) else None
            }
            records.append(record)
        
        response = supabase.table("daily_reports").insert(records).execute()
        return len(response.data), None
    except Exception as e:
        return 0, str(e)

def get_project_reports(project_id):
    supabase = get_supabase()
    try:
        response = supabase.table("daily_reports").select("*").eq("project_id", project_id).execute()
        return response.data, None
    except Exception as e:
        return None, str(e)