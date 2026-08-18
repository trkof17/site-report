# -*- coding: utf-8 -*-
"""
Created on Wed Aug 12 03:53:57 2026

@author: taric
"""

import os
from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")    