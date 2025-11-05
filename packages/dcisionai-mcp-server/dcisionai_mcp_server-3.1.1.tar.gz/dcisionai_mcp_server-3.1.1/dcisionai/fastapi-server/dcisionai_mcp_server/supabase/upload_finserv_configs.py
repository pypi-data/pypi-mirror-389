#!/usr/bin/env python3
"""
Upload FinServ Domain Configs to Supabase
==========================================

Uploads 3 new FinServ domain configurations:
1. customer_onboarding (Wealth Management)
2. pe_exit_timing (Private Equity)
3. hf_rebalancing (Hedge Funds)
"""

import json
import os
from pathlib import Path
from supabase import create_client, Client

def load_config(config_file: str) -> dict:
    """Load JSON config file"""
    config_path = Path(__file__).parent / "configs" / config_file
    with open(config_path, 'r') as f:
        return json.load(f)

def upload_to_supabase(client: Client, config: dict):
    """Upload or update config in Supabase"""
    domain_id = config['domain_id']
    
    # Transform config to match Supabase schema
    category = config.get('category', 'optimization')
    
    # Create domain expert profile based on category
    domain_expert_profiles = {
        'wealth_management': {
            'title': 'Wealth Management Advisor',
            'profile': 'Expert in portfolio construction, risk management, and client asset allocation',
            'priorities': ['Client risk tolerance alignment', 'Fee minimization', 'Tax efficiency', 'Diversification']
        },
        'private_equity': {
            'title': 'Private Equity Principal',
            'profile': 'Expert in portfolio company value creation, market timing, and exit strategy',
            'priorities': ['Exit value maximization', 'Tax optimization', 'Market timing', 'Fund lifecycle management']
        },
        'hedge_fund': {
            'title': 'Quantitative Portfolio Manager',
            'profile': 'Expert in factor investing, transaction cost analysis, and portfolio rebalancing',
            'priorities': ['Factor exposure management', 'Cost minimization', 'Alpha generation', 'Risk control']
        }
    }
    
    math_expert_profiles = {
        'wealth_management': {
            'title': 'Portfolio Optimization Specialist',
            'profile': 'Expert in mean-variance optimization and multi-objective portfolio construction',
            'formulation': 'Multi-objective optimization with risk, return, cost, and tax objectives',
            'problem_class': 'Quadratic Programming with Linear Constraints'
        },
        'private_equity': {
            'title': 'Time-Series Optimization Specialist',
            'profile': 'Expert in scenario analysis and temporal decision making under uncertainty',
            'formulation': 'Dynamic optimization with market condition modeling',
            'problem_class': 'Stochastic Dynamic Programming'
        },
        'hedge_fund': {
            'title': 'Transaction Cost Modeling Specialist',
            'profile': 'Expert in market microstructure and cost-aware portfolio rebalancing',
            'formulation': 'Multi-objective optimization with transaction cost constraints',
            'problem_class': 'Mixed Integer Programming with Non-Linear Costs'
        }
    }
    
    # Add synthetic_generator_method to parsing_config
    parsing_config = config.get('parsing_config', {}).copy()
    generator_methods = {
        'customer_onboarding': 'generate_customer_onboarding',
        'pe_exit_timing': 'generate_pe_exit_timing',
        'hf_rebalancing': 'generate_hf_rebalancing'
    }
    if domain_id in generator_methods:
        parsing_config['synthetic_generator_method'] = generator_methods[domain_id]
    
    config_for_db = {
        'id': f"{domain_id}_v1",
        'domain': domain_id,
        'name': config.get('name', ''),
        'problem_type': category,
        'description': config.get('description', ''),
        'is_active': config.get('enabled', True),
        'enabled': config.get('enabled', True),
        'version': int(config.get('version', '1.0.0').split('.')[0]),  # Extract major version
        'domain_expert': domain_expert_profiles.get(category, domain_expert_profiles['wealth_management']),
        'math_expert': math_expert_profiles.get(category, math_expert_profiles['wealth_management']),
        'objective_config': config.get('objective_config', {}),
        'constraint_config': config.get('constraints_config', {}),  # Note: without s in DB
        'constraints_config': config.get('constraints_config', {}),  # And also with s for new field
        'ga_params': config.get('ga_params', {}),
        'parse_config': config.get('parsing_config', {}),  # Note: without ing in DB
        'parsing_config': parsing_config,  # Use updated parsing_config with synthetic_generator_method
        'result_config': config.get('output_format', {'primary_metrics': []}),  # Result configuration
        'created_by': 'upload_script'
    }
    
    try:
        # Check if config already exists
        result = client.table('domain_configs').select('*').eq('domain', domain_id).execute()
        
        if result.data:
            # Update existing
            print(f"✏️  Updating existing config: {domain_id}")
            client.table('domain_configs').update(config_for_db).eq('domain', domain_id).execute()
            print(f"✅ Updated {domain_id}")
        else:
            # Insert new
            print(f"➕ Inserting new config: {domain_id}")
            client.table('domain_configs').insert(config_for_db).execute()
            print(f"✅ Inserted {domain_id}")
    
    except Exception as e:
        print(f"❌ Error uploading {domain_id}: {e}")
        raise

def main():
    # Initialize Supabase client
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_API_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_API_KEY must be set")
        print("   Source them from .env.staging:")
        print("   export SUPABASE_URL=... SUPABASE_API_KEY=...")
        return
    
    client = create_client(supabase_url, supabase_key)
    print("🔗 Connected to Supabase")
    
    # Upload 3 FinServ configs
    configs = [
        'customer_onboarding_config.json',
        'pe_exit_timing_config.json',
        'hf_rebalancing_config.json'
    ]
    
    print("\n📤 Uploading FinServ domain configs...\n")
    
    for config_file in configs:
        config = load_config(config_file)
        upload_to_supabase(client, config)
        print()
    
    # Verify uploads
    print("\n🔍 Verifying uploads...\n")
    
    for config_file in configs:
        config = load_config(config_file)
        domain_id = config['domain_id']
        
        result = client.table('domain_configs').select('domain, name, version, enabled').eq('domain', domain_id).execute()
        
        if result.data:
            data = result.data[0]
            print(f"✅ {domain_id}:")
            print(f"   Name: {data['name']}")
            print(f"   Version: {data['version']}")
            print(f"   Enabled: {data['enabled']}")
        else:
            print(f"❌ {domain_id}: Not found in database")
    
    print("\n✨ Upload complete!\n")
    
    # Print next steps
    print("📋 Next Steps:")
    print("1. Update HybridSolver routing to recognize new domains")
    print("2. Update UI to display new domain types")
    print("3. Create CLI tests for all 3 domains")
    print("4. Test end-to-end with market data integration")

if __name__ == "__main__":
    main()

