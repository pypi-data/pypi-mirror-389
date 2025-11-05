#!/usr/bin/env python3
"""
Domain Configuration Loader for DcisionAI-Solver
Loads domain-specific configurations from Supabase
"""

import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from supabase import create_client, Client

logger = logging.getLogger(__name__)


class DomainConfigLoader:
    """
    Loads domain configurations from Supabase for DcisionAI-Solver
    
    Features:
    - In-memory caching for performance
    - Automatic usage tracking
    - Support for config versioning
    - Fallback to defaults if Supabase unavailable
    """
    
    def __init__(self, cache_ttl_minutes: int = 60):
        """
        Initialize loader with Supabase connection
        
        Args:
            cache_ttl_minutes: How long to cache configs (default: 60 minutes)
        """
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_API_KEY')
        
        if not supabase_url or not supabase_key:
            logger.warning("⚠️ SUPABASE_URL or SUPABASE_API_KEY not set - will use fallback configs")
            self.supabase = None
        else:
            try:
                self.supabase: Client = create_client(supabase_url, supabase_key)
                logger.info(f"✅ Connected to Supabase for domain configs")
            except Exception as e:
                logger.error(f"❌ Failed to connect to Supabase: {e}")
                self.supabase = None
        
        # In-memory cache
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
    
    def load_config(
        self, 
        domain_id: str, 
        use_cache: bool = True,
        version: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Load domain configuration from Supabase
        
        Args:
            domain_id: Domain identifier (e.g., 'retail_layout')
            use_cache: Use cached config if available and fresh
            version: Specific version to load (None = latest)
        
        Returns:
            Domain configuration dictionary or None if not found
        """
        # Check cache first
        if use_cache and self._is_cache_fresh(domain_id):
            logger.info(f"📦 Using cached config for {domain_id}")
            return self._cache[domain_id]
        
        # If no Supabase connection, use fallback
        if self.supabase is None:
            logger.warning(f"⚠️ No Supabase connection - using fallback config for {domain_id}")
            return self._get_fallback_config(domain_id)
        
        try:
            # Query Supabase by domain field (not id, which has version suffix like "_v1")
            query = self.supabase.table('domain_configs').select('*').eq('domain', domain_id)
            
            # Add filters
            if version:
                query = query.eq('version', version)
            else:
                query = query.eq('is_active', True)
            
            result = query.single().execute()
            
            if not result.data:
                logger.error(f"❌ Domain config not found: {domain_id}")
                return self._get_fallback_config(domain_id)
            
            config = result.data
            
            # Update usage tracking (fire and forget)
            try:
                self.supabase.table('domain_configs').update({
                    'usage_count': config.get('usage_count', 0) + 1,
                    'last_used_at': datetime.now().isoformat()
                }).eq('domain', domain_id).execute()
            except Exception as e:
                logger.warning(f"Failed to update usage tracking: {e}")
            
            # Cache the config
            self._cache[domain_id] = config
            self._cache_timestamps[domain_id] = datetime.now()
            
            logger.info(f"✅ Loaded config for {domain_id} from Supabase (v{config.get('version', 1)})")
            
            return config
            
        except Exception as e:
            logger.error(f"❌ Failed to load config for {domain_id}: {e}")
            
            # Try cache even if expired
            if domain_id in self._cache:
                logger.warning(f"⚠️ Using stale cached config for {domain_id}")
                return self._cache[domain_id]
            
            return self._get_fallback_config(domain_id)
    
    def list_active_domains(self) -> List[Dict[str, str]]:
        """
        List all active domain IDs and names
        
        Returns:
            List of dicts with 'id', 'name', 'domain', 'problem_type'
        """
        if self.supabase is None:
            logger.warning("⚠️ No Supabase connection - returning empty list")
            return []
        
        try:
            result = self.supabase.table('domain_configs')\
                .select('id, name, domain, problem_type, usage_count')\
                .eq('is_active', True)\
                .order('usage_count', desc=True)\
                .execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"❌ Failed to list domains: {e}")
            return []
    
    def invalidate_cache(self, domain_id: Optional[str] = None):
        """
        Invalidate cache for specific domain or all domains
        
        Args:
            domain_id: Specific domain to invalidate, or None for all
        """
        if domain_id:
            self._cache.pop(domain_id, None)
            self._cache_timestamps.pop(domain_id, None)
            logger.info(f"🗑️ Invalidated cache for {domain_id}")
        else:
            self._cache.clear()
            self._cache_timestamps.clear()
            logger.info("🗑️ Invalidated all cached configs")
    
    def upsert_config(
        self, 
        domain_id: str, 
        config: Dict[str, Any],
        updated_by: Optional[str] = None
    ) -> bool:
        """
        Create or update a domain configuration
        
        Args:
            domain_id: Domain identifier
            config: Complete configuration dictionary
            updated_by: Who is making this update
        
        Returns:
            True if successful, False otherwise
        """
        if self.supabase is None:
            logger.error("❌ Cannot upsert config - no Supabase connection")
            return False
        
        try:
            config['id'] = domain_id
            config['updated_by'] = updated_by
            
            result = self.supabase.table('domain_configs').upsert(config).execute()
            
            if result.data:
                # Invalidate cache
                self.invalidate_cache(domain_id)
                logger.info(f"✅ Upserted config for {domain_id}")
                return True
            else:
                logger.error(f"❌ Failed to upsert config for {domain_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to upsert config for {domain_id}: {e}")
            return False
    
    def _is_cache_fresh(self, domain_id: str) -> bool:
        """Check if cached config is still fresh"""
        if domain_id not in self._cache:
            return False
        
        if domain_id not in self._cache_timestamps:
            return False
        
        age = datetime.now() - self._cache_timestamps[domain_id]
        return age < self.cache_ttl
    
    def _get_fallback_config(self, domain_id: str) -> Optional[Dict[str, Any]]:
        """
        Get hardcoded fallback config if Supabase unavailable
        
        This is a safety mechanism for development/testing
        """
        logger.warning(f"⚠️ Using hardcoded fallback config for {domain_id}")
        
        # For now, return None to force proper Supabase setup
        # TODO: Add hardcoded configs for critical domains
        return None
    
    def get_config_history(
        self, 
        domain_id: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get change history for a domain configuration
        
        Args:
            domain_id: Domain identifier
            limit: Maximum number of history entries
        
        Returns:
            List of history entries
        """
        if self.supabase is None:
            return []
        
        try:
            result = self.supabase.table('domain_config_history')\
                .select('*')\
                .eq('config_id', domain_id)\
                .order('changed_at', desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"❌ Failed to get config history: {e}")
            return []


# Singleton instance for global use
_loader_instance: Optional[DomainConfigLoader] = None

def get_domain_config_loader() -> DomainConfigLoader:
    """Get singleton instance of DomainConfigLoader"""
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = DomainConfigLoader()
    return _loader_instance

