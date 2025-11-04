#!/usr/bin/env python3
"""
Add synthetic_generator_method and generator_param_mapping to all domain configs in Supabase.
This enables the universal parser to work without domain-specific code.
"""

import os
import json
from supabase import create_client, Client

# Load Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_API_KEY')  # Note: it's SUPABASE_API_KEY in .env

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_API_KEY in environment")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Define generator method and param mappings for each domain
GENERATOR_CONFIGS = {
    'retail_layout': {
        'method': 'generate_retail_layout',
        'param_mapping': {
            'product_count': 'product_count',
            'shelf_count': 'shelf_count'
        }
    },
    'vrp': {
        'method': 'generate_vrp_data',
        'param_mapping': {
            'customer_count': 'customer_count',
            'vehicle_count': 'vehicle_count'
        }
    },
    'job_shop': {
        'method': 'generate_job_shop_data',
        'param_mapping': {
            'job_count': 'job_count',
            'machine_count': 'machine_count'
        }
    },
    'workforce': {
        'method': 'generate_workforce_data',
        'param_mapping': {
            'worker_count': 'worker_count',
            'shift_count': 'shift_count',
            'days': 'days'
        }
    },
    'maintenance': {
        'method': 'generate_maintenance_data',
        'param_mapping': {
            'equipment_count': 'equipment_count',
            'task_count': 'task_count',
            'technician_count': 'technician_count'
        }
    },
    'promotion': {
        'method': 'generate_promotion_data',
        'param_mapping': {
            'product_count': 'product_count',
            'promotion_count': 'promotion_count',
            'weeks': 'weeks'
        }
    },
    'portfolio': {
        'method': 'generate_portfolio',
        'param_mapping': {
            'asset_count': 'asset_count',
            'portfolio_value': 'portfolio_value'
        }
    },
    'trading': {
        'method': 'generate_trading_schedule',
        'param_mapping': {
            'position_count': 'position_count',
            'time_periods': 'time_periods'
        }
    },
    'customer_onboarding': {
        'method': 'generate_customer_onboarding',
        'param_mapping': {
            'client_count': 'client_count',
            'advisor_count': 'advisor_count'
        }
    },
    'pe_exit_timing': {
        'method': 'generate_pe_exit_timing',
        'param_mapping': {
            'portfolio_company_count': 'portfolio_company_count',
            'time_periods': 'time_periods'
        }
    },
    'hf_rebalancing': {
        'method': 'generate_hf_rebalancing',
        'param_mapping': {
            'position_count': 'position_count',
            'time_periods': 'time_periods'
        }
    }
}

def update_domain_configs():
    """Update all domain configs with generator methods"""
    print("🔧 Updating domain configs with generator methods...")
    
    for domain_id, gen_config in GENERATOR_CONFIGS.items():
        print(f"\n📦 Processing: {domain_id}")
        
        try:
            # Fetch current config
            response = supabase.table('domain_configs').select('*').eq('id', domain_id).execute()
            
            if not response.data or len(response.data) == 0:
                print(f"   ⚠️  No config found for {domain_id}, skipping...")
                continue
            
            current_config = response.data[0]
            
            # Get parse_config (or parsing_config)
            parse_config = current_config.get('parsing_config') or current_config.get('parse_config') or {}
            
            # Add generator method and param mapping
            parse_config['synthetic_generator_method'] = gen_config['method']
            parse_config['generator_param_mapping'] = gen_config['param_mapping']
            
            # Update in Supabase (use parsing_config as the canonical name)
            update_data = {
                'parsing_config': parse_config,
                'version': str(int(current_config['version']) + 1)  # Bump version
            }
            
            update_response = supabase.table('domain_configs').update(update_data).eq('id', domain_id).execute()
            
            print(f"   ✅ Updated {domain_id} v{update_data['version']}")
            print(f"      Method: {gen_config['method']}")
            print(f"      Params: {list(gen_config['param_mapping'].keys())}")
            
        except Exception as e:
            print(f"   ❌ Failed to update {domain_id}: {e}")
    
    print("\n✅ All domain configs updated!")

if __name__ == '__main__':
    update_domain_configs()

