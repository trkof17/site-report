# -*- coding: utf-8 -*-
"""
Created on Wed Aug 12 05:08:04 2026

@author: taric
"""

from .supabase_client import get_supabase

def sign_up(email, password):
    supabase = get_supabase()
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        return response.user, None
    except Exception as e:
        return None, str(e)

def sign_in(email, password):
    supabase = get_supabase()
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return response.user, None
    except Exception as e:
        return None, str(e)

def sign_out():
    supabase = get_supabase()
    supabase.auth.sign_out()

def get_current_user():
    supabase = get_supabase()
    try:
        user = supabase.auth.get_user()
        return user.user if user else None
    except:
        return None