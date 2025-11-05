#!/usr/bin/env python3
"""
Run SQL migration to add result_formatter_config column to domain_configs table.
"""

import os
from supabase import create_client, Client

# Load Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_API_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_API_KEY in environment")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# SQL migration
migration_sql = """
ALTER TABLE domain_configs 
ADD COLUMN IF NOT EXISTS result_formatter_config JSONB;
"""

try:
    print("🔧 Running migration: Add result_formatter_config column...")
    
    # Execute raw SQL via Supabase RPC (if available) or direct execute
    # Note: Supabase Python client doesn't have direct SQL execution
    # We'll use a workaround: try to update a fake row to trigger column creation via API
    
    print("⚠️  Cannot run raw SQL via Supabase Python client.")
    print("📝 Please run this SQL manually in Supabase SQL Editor:")
    print("\n" + "="*60)
    print(migration_sql)
    print("="*60)
    print("\n✅ After running SQL, execute: python add_result_formatter_configs.py")
    
except Exception as e:
    print(f"❌ Migration failed: {e}")

if __name__ == '__main__':
    pass

