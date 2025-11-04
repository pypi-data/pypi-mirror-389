#!/usr/bin/env python3
"""
Upload ALL Domain Configs to Supabase
======================================

Uploads all 11 domain configurations with personas to Supabase.
Personas are read directly from JSON files (no hardcoding).
"""

import json
import os
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parents[6] / '.env.staging')

def load_config(config_path: Path) -> dict:
    """Load JSON config file"""
    with open(config_path, 'r') as f:
        return json.load(f)

def upload_to_supabase(client: Client, config: dict, config_filename: str):
    """Upload or update config in Supabase"""
    
    # Handle both 'domain_id' (new) and 'id' (old) formats
    domain_id = config.get('domain_id') or config.get('id')
    
    if not domain_id:
        print(f"❌ {config_filename}: No domain_id or id found, skipping")
        return
    
    # Validate personas exist
    if 'domain_expert' not in config or 'math_expert' not in config:
        print(f"❌ {domain_id}: Missing personas (domain_expert or math_expert), skipping")
        return
    
    # Build payload for Supabase
    config_for_db = {
        'id': f"{domain_id}_v1",
        'domain': domain_id,
        'name': config.get('name', ''),
        'problem_type': config.get('category') or config.get('problem_type', 'optimization'),
        'description': config.get('description', ''),
        'is_active': config.get('enabled', True),
        'enabled': config.get('enabled', True),
        'version': int(str(config.get('version', '1.0.0')).split('.')[0]),  # Handle both int and string versions
        
        # Personas (read from JSON - no hardcoding!)
        'domain_expert': config['domain_expert'],
        'math_expert': config['math_expert'],
        
        # Objectives and constraints
        'objective_config': config.get('objective_config', {}),
        'constraint_config': config.get('constraints_config') or config.get('constraint_config', {}),
        'constraints_config': config.get('constraints_config') or config.get('constraint_config', {}),
        
        # GA parameters
        'ga_params': config.get('ga_params', {}),
        
        # Parsing configuration
        'parse_config': config.get('parsing_config') or config.get('parse_config', {}),
        'parsing_config': config.get('parsing_config') or config.get('parse_config', {}),
        
        # Output format
        'result_config': config.get('output_format') or config.get('result_config', {'primary_metrics': []}),
        
        'created_by': 'upload_all_configs_script'
    }
    
    try:
        # Check if config already exists
        result = client.table('domain_configs').select('*').eq('domain', domain_id).execute()
        
        if result.data:
            # Update existing
            print(f"✏️  Updating: {domain_id} ({config['name']})")
            client.table('domain_configs').update(config_for_db).eq('domain', domain_id).execute()
            print(f"    ✅ Domain Expert: {config['domain_expert']['title']}")
            print(f"    ✅ Math Expert: {config['math_expert']['title']}")
        else:
            # Insert new
            print(f"➕ Inserting: {domain_id} ({config['name']})")
            client.table('domain_configs').insert(config_for_db).execute()
            print(f"    ✅ Domain Expert: {config['domain_expert']['title']}")
            print(f"    ✅ Math Expert: {config['math_expert']['title']}")
    
    except Exception as e:
        print(f"❌ Error uploading {domain_id}: {e}")
        raise


def main():
    """Upload all configs to Supabase"""
    
    # Initialize Supabase client
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_API_KEY') or os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_API_KEY must be set")
        return
    
    client = create_client(supabase_url, supabase_key)
    
    # Find all config files
    configs_dir = Path(__file__).parent / 'configs'
    config_files = sorted(configs_dir.glob('*.json'))
    
    print(f"🚀 Uploading {len(config_files)} domain configs to Supabase...\n")
    
    success_count = 0
    for config_file in config_files:
        try:
            config = load_config(config_file)
            upload_to_supabase(client, config, config_file.name)
            success_count += 1
            print()
        except Exception as e:
            print(f"❌ Failed to upload {config_file.name}: {e}\n")
            continue
    
    print(f"{'='*60}")
    print(f"✅ Upload complete: {success_count}/{len(config_files)} configs uploaded")
    print(f"{'='*60}\n")
    
    # Verify all domains in Supabase
    print("🔍 Verifying domains in Supabase...")
    result = client.table('domain_configs').select('domain, name, domain_expert, math_expert').execute()
    
    print(f"\n📊 Total domains in Supabase: {len(result.data)}\n")
    for idx, config in enumerate(sorted(result.data, key=lambda x: x['domain']), 1):
        domain_expert = config.get('domain_expert', {})
        math_expert = config.get('math_expert', {})
        print(f"{idx:2d}. {config['domain']:25s} - {config['name'][:40]}")
        if domain_expert:
            print(f"     🧑‍💼 {domain_expert.get('title', 'N/A')}")
        if math_expert:
            print(f"     🧮 {math_expert.get('title', 'N/A')}")
        print()


if __name__ == '__main__':
    main()

