#!/usr/bin/env python3
"""
Add result_formatter_config to all domain configs in Supabase.

This enables the universal result formatter to work without domain-specific code.
For Phase 2, we'll start with a minimal config that's better than fallback.
"""

import os
import json
from supabase import create_client, Client

# Load Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_API_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_API_KEY in environment")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Minimal result formatter configs for Phase 2
# Full configs will be created after testing
RESULT_FORMATTER_CONFIGS = {
    'retail_layout': {
        'entity_keys': [
            {'key': 'products', 'display_name': 'Products'},
            {'key': 'shelves', 'display_name': 'Shelves'}
        ],
        'data_provenance': {
            'problem_type': 'Store Layout Optimization',
            'data_provided_template': '{products} products and {shelves} shelves extracted from description'
        },
        'structured_results': {
            'a_model_development': {
                'title': 'Store Layout Model Development',
                'description': 'Multi-objective retail layout optimization for {products} products across {shelves} shelves'
            }
        }
    },
    'vrp': {
        'entity_keys': [
            {'key': 'customers', 'display_name': 'Customers'},
            {'key': 'vehicles', 'display_name': 'Vehicles'}
        ],
        'data_provenance': {
            'problem_type': 'Vehicle Routing Problem (VRP)',
            'data_provided_template': '{customers} delivery locations and {vehicles} vehicles extracted'
        }
    },
    'job_shop': {
        'entity_keys': [
            {'key': 'jobs', 'display_name': 'Jobs'},
            {'key': 'machines', 'display_name': 'Machines'}
        ],
        'data_provenance': {
            'problem_type': 'Job Shop Scheduling',
            'data_provided_template': '{jobs} jobs across {machines} machines extracted'
        }
    },
    'workforce': {
        'entity_keys': [
            {'key': 'workers', 'display_name': 'Workers'},
            {'key': 'shifts', 'display_name': 'Shifts'}
        ],
        'data_provenance': {
            'problem_type': 'Workforce Rostering',
            'data_provided_template': '{workers} workers across {shifts} shifts extracted'
        }
    },
    'maintenance': {
        'entity_keys': [
            {'key': 'equipment', 'display_name': 'Equipment'},
            {'key': 'tasks', 'display_name': 'Tasks'}
        ],
        'data_provenance': {
            'problem_type': 'Predictive Maintenance Scheduling',
            'data_provided_template': '{equipment} equipment items with {tasks} maintenance tasks extracted'
        }
    },
    'promotion': {
        'entity_keys': [
            {'key': 'products', 'display_name': 'Products'},
            {'key': 'promotions', 'display_name': 'Promotions'}
        ],
        'data_provenance': {
            'problem_type': 'Promotion Scheduling',
            'data_provided_template': '{products} products with {promotions} promotion opportunities extracted'
        }
    },
    'portfolio': {
        'entity_keys': [
            {'key': 'assets', 'display_name': 'Assets'}
        ],
        'data_provenance': {
            'problem_type': 'Portfolio Rebalancing',
            'data_provided_template': '{assets} portfolio assets extracted'
        }
    },
    'trading': {
        'entity_keys': [
            {'key': 'positions', 'display_name': 'Positions'}
        ],
        'data_provenance': {
            'problem_type': 'Trading Schedule Optimization',
            'data_provided_template': '{positions} trading positions extracted'
        }
    }
}

def update_result_formatter_configs():
    """Update all domain configs with minimal result_formatter_config"""
    print("🔧 Adding result_formatter_config to domain configs...")
    
    for domain_id, formatter_config in RESULT_FORMATTER_CONFIGS.items():
        print(f"\n📦 Processing: {domain_id}")
        
        try:
            # Fetch current config
            response = supabase.table('domain_configs').select('*').eq('id', domain_id).execute()
            
            if not response.data or len(response.data) == 0:
                print(f"   ⚠️  No config found for {domain_id}, skipping...")
                continue
            
            current_config = response.data[0]
            
            # Add result_formatter_config
            update_data = {
                'result_formatter_config': formatter_config,
                'version': str(int(current_config['version']) + 1)  # Bump version
            }
            
            update_response = supabase.table('domain_configs').update(update_data).eq('id', domain_id).execute()
            
            print(f"   ✅ Updated {domain_id} v{update_data['version']}")
            print(f"      Entity keys: {[e['key'] for e in formatter_config['entity_keys']]}")
            
        except Exception as e:
            print(f"   ❌ Failed to update {domain_id}: {e}")
    
    print("\n✅ All domain configs updated with result_formatter_config!")
    print("\n📝 Next steps:")
    print("   1. Test retail_layout with universal formatter")
    print("   2. Expand configs with full structured_results templates")
    print("   3. Test all 8 domains end-to-end")

if __name__ == '__main__':
    update_result_formatter_configs()

