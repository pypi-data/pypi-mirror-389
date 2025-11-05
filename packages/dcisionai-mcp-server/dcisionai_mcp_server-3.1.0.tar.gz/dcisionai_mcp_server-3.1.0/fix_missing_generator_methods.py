#!/usr/bin/env python3
"""
Quick fix: Add synthetic_generator_method to existing FinServ configs in Supabase
"""

import os
from supabase import create_client

# Use default credentials
url = "https://nbhrvwegrveoiurnwbij.supabase.co"
key = "sb_secret_Rp3EG4cJlCg9ZU5cGlLZ5g_SimVHcgy"

print("🔗 Connecting to Supabase...")
supabase = create_client(url, key)

# Map domains to their generator methods
generator_methods = {
    'customer_onboarding': 'generate_customer_onboarding',
    'pe_exit_timing': 'generate_pe_exit_timing',
    'hf_rebalancing': 'generate_hf_rebalancing'
}

print("\n🔧 Updating FinServ configs...\n")

for domain_id, method in generator_methods.items():
    print(f"Processing {domain_id}...")
    
    try:
        # Get current config
        result = supabase.table('domain_configs').select('*').eq('domain', domain_id).execute()
        
        if not result.data:
            print(f"  ❌ Not found in database")
            continue
        
        config = result.data[0]
        parsing_config = config.get('parsing_config', {})
        
        # Add synthetic_generator_method if missing
        if 'synthetic_generator_method' not in parsing_config:
            parsing_config['synthetic_generator_method'] = method
            
            # Update in Supabase
            supabase.table('domain_configs').update({
                'parsing_config': parsing_config
            }).eq('domain', domain_id).execute()
            
            print(f"  ✅ Added synthetic_generator_method: {method}")
        else:
            print(f"  ✓ Already has synthetic_generator_method: {parsing_config['synthetic_generator_method']}")
    
    except Exception as e:
        print(f"  ❌ Error: {e}")

print("\n✅ Migration complete!\n")

