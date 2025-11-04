#!/usr/bin/env python3
"""
Session Manager for DcisionAI MCP Platform
Manages workflow sessions using Supabase for persistence and rate limiting
"""

import os
import json
import uuid
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncio

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logging.warning("Supabase not available. Install with: pip install supabase")

logger = logging.getLogger(__name__)

class SessionManager:
    """
    Manages workflow sessions using Supabase for persistence
    Provides natural delays between API calls and session state management
    """
    
    def __init__(self):
        self.supabase: Optional[Client] = None
        self.session_cache: Dict[str, Dict[str, Any]] = {}
        
        # Initialize Supabase client
        self._initialize_supabase()
    
    def _initialize_supabase(self):
        """Initialize Supabase client"""
        if not SUPABASE_AVAILABLE:
            logger.warning("Supabase not available, using in-memory session storage")
            return
        
        try:
            # Supabase configuration from environment variables
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_API_KEY')
            
            if not supabase_url or not supabase_key:
                logger.warning("⚠️ Supabase credentials not found in environment variables. Using in-memory storage.")
                return
            
            self.supabase = create_client(supabase_url, supabase_key)
            logger.info("✅ Supabase client initialized successfully")
            
            # Ensure tables exist
            self._ensure_tables_exist()
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase: {e}")
            self.supabase = None
    
    def _ensure_tables_exist(self):
        """Ensure required tables exist in Supabase"""
        if not self.supabase:
            return
        
        try:
            # Check if sessions table exists by trying to query it
            result = self.supabase.table("dcisionai-mcp-server-session").select("id").limit(1).execute()
            logger.info("✅ DcisionAI MCP Server sessions table exists")
        except Exception as e:
            logger.warning(f"⚠️ Sessions table may not exist: {e}")
            logger.info("📋 Please create the table manually in Supabase dashboard")
            logger.info("📄 See SUPABASE_TABLE_SETUP.md for instructions")
            # Continue with in-memory fallback
    
    def create_session(self, problem_description: str, model_preference: str = "fine-tuned") -> str:
        """Create a new workflow session"""
        session_id = str(uuid.uuid4())
        
        session_data = {
            "id": session_id,
            "problem_description": problem_description,
            "model_preference": model_preference,
            "status": "created",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "steps": {},
            "reasoning_chain": {},
            "provider_distribution": {
                "intent": "claude",
                "data": "gpt-4",
                "model": "fine-tuned"
            },
            "execution_strategy": "sequential_provider_distribution",
            "errors": [],
            "summary": {}
        }
        
        # Store in cache
        self.session_cache[session_id] = session_data
        
        # Store in Supabase
        if self.supabase:
            try:
                self.supabase.table("dcisionai-mcp-server-session").insert(session_data).execute()
                logger.info(f"✅ Session {session_id} created in Supabase")
            except Exception as e:
                logger.error(f"❌ Failed to store session in Supabase: {e}")
                logger.info("💡 Continuing with in-memory storage")
        
        logger.info(f"🆕 Created session: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        # Try cache first
        if session_id in self.session_cache:
            return self.session_cache[session_id]
        
        # Try Supabase
        if self.supabase:
            try:
                result = self.supabase.table("dcisionai-mcp-server-session").select("*").eq("id", session_id).execute()
                if result.data:
                    session_data = result.data[0]
                    # Cache it
                    self.session_cache[session_id] = session_data
                    return session_data
            except Exception as e:
                logger.error(f"❌ Failed to get session from Supabase: {e}")
        
        return None
    
    def update_session_step(self, session_id: str, step_name: str, step_data: Dict[str, Any]) -> bool:
        """Update a specific step in the session"""
        session = self.get_session(session_id)
        if not session:
            logger.error(f"❌ Session {session_id} not found")
            return False
        
        # Update session data
        session["steps"][step_name] = step_data
        session["updated_at"] = datetime.now().isoformat()
        
        # Update cache
        self.session_cache[session_id] = session
        
        # Update Supabase
        if self.supabase:
            try:
                self.supabase.table("dcisionai-mcp-server-session").update({
                    "steps": session["steps"],
                    "updated_at": session["updated_at"]
                }).eq("id", session_id).execute()
                logger.info(f"✅ Updated step {step_name} for session {session_id}")
            except Exception as e:
                logger.error(f"❌ Failed to update session in Supabase: {e}")
                return False
        
        return True
    
    def update_session_status(self, session_id: str, status: str, summary: Optional[Dict[str, Any]] = None) -> bool:
        """Update session status"""
        session = self.get_session(session_id)
        if not session:
            logger.error(f"❌ Session {session_id} not found")
            return False
        
        # Update session data
        session["status"] = status
        session["updated_at"] = datetime.now().isoformat()
        if summary:
            session["summary"] = summary
        
        # Update cache
        self.session_cache[session_id] = session
        
        # Update Supabase
        if self.supabase:
            try:
                update_data = {
                    "status": status,
                    "updated_at": session["updated_at"]
                }
                if summary:
                    update_data["summary"] = summary
                
                self.supabase.table("dcisionai-mcp-server-session").update(update_data).eq("id", session_id).execute()
                logger.info(f"✅ Updated status to {status} for session {session_id}")
            except Exception as e:
                logger.error(f"❌ Failed to update session status in Supabase: {e}")
                return False
        
        return True
    
    def add_session_error(self, session_id: str, error: str) -> bool:
        """Add an error to the session"""
        session = self.get_session(session_id)
        if not session:
            logger.error(f"❌ Session {session_id} not found")
            return False
        
        # Add error
        session["errors"].append({
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
        session["updated_at"] = datetime.now().isoformat()
        
        # Update cache
        self.session_cache[session_id] = session
        
        # Update Supabase
        if self.supabase:
            try:
                self.supabase.table("dcisionai-mcp-server-session").update({
                    "errors": session["errors"],
                    "updated_at": session["updated_at"]
                }).eq("id", session_id).execute()
                logger.info(f"✅ Added error to session {session_id}")
            except Exception as e:
                logger.error(f"❌ Failed to add error to session in Supabase: {e}")
                return False
        
        return True
    
    def get_session_step(self, session_id: str, step_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific step from the session"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        return session.get("steps", {}).get(step_name)
    
    def list_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent sessions"""
        if self.supabase:
            try:
                result = self.supabase.table("dcisionai-mcp-server-session").select("*").order("created_at", desc=True).limit(limit).execute()
                return result.data
            except Exception as e:
                logger.error(f"❌ Failed to list sessions from Supabase: {e}")
        
        # Fallback to cache
        sessions = list(self.session_cache.values())
        sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return sessions[:limit]
    
    async def wait_for_step_completion(self, session_id: str, step_name: str, timeout: int = 300) -> bool:
        """Wait for a specific step to complete (for debugging/monitoring)"""
        start_time = datetime.now()
        
        while (datetime.now() - start_time).seconds < timeout:
            session = self.get_session(session_id)
            if not session:
                return False
            
            if step_name in session.get("steps", {}):
                step_data = session["steps"][step_name]
                if step_data.get("status") in ["success", "error", "completed"]:
                    return True
            
            await asyncio.sleep(1)
        
        return False
    
    def cleanup_old_sessions(self, days_old: int = 7) -> int:
        """Clean up old sessions"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        cutoff_str = cutoff_date.isoformat()
        
        cleaned_count = 0
        
        # Clean cache
        sessions_to_remove = []
        for session_id, session in self.session_cache.items():
            if session.get("created_at", "") < cutoff_str:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.session_cache[session_id]
            cleaned_count += 1
        
        # Clean Supabase
        if self.supabase:
            try:
                result = self.supabase.table("dcisionai-mcp-server-session").delete().lt("created_at", cutoff_str).execute()
                cleaned_count += len(result.data) if result.data else 0
                logger.info(f"✅ Cleaned up {cleaned_count} old sessions")
            except Exception as e:
                logger.error(f"❌ Failed to clean up old sessions: {e}")
        
        return cleaned_count

# Global session manager instance
session_manager = SessionManager()
