#!/usr/bin/env python3
"""DcisionAI Intent Tool - LLM-based problem classification"""
import logging
import os
import json
import re
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class IntentTool:
    def __init__(self):
        self.supabase_client = self._init_supabase()
        self.llm_client = self._init_llm()
        logger.info("✅ IntentTool initialized")
    
    def _init_supabase(self):
        try:
            from supabase import create_client
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_API_KEY")
            if url and key:
                logger.info("✅ Supabase initialized")
                return create_client(url, key)
        except Exception as e:
            logger.warning(f"⚠️ Supabase: {e}")
        return None
    
    def _init_llm(self):
        try:
            from dcisionai_mcp_server.llm.llm_client import LLMClient
            logger.info("✅ LLM initialized")
            return LLMClient()
        except Exception as e:
            logger.error(f"❌ LLM: {e}")
            return None
    
    async def execute(self, problem_description: str, session_id: str) -> Dict[str, Any]:
        """Classify problem, return domain config, persist to session"""
        try:
            classification = await self._classify_with_llm(problem_description)
            if not classification:
                return {'status': 'error', 'error': 'LLM classification failed'}
            logger.info(f"🧠 {classification['optimization_type']} → {classification.get('domain_suggestion')}")
            domain_config = await self._get_domain_config(classification)
            
            result = {
                'status': 'success',
                'session_id': session_id,
                'domain_id': domain_config['domain'],
                'domain_config': domain_config,
                'confidence': classification.get('confidence', 0.8),
                'reasoning': classification.get('reasoning', ''),
                'optimization_type': classification.get('optimization_type', 'unknown'),
                'problem_structure': classification.get('problem_structure', {})
            }
            
            # Persist to session table
            await self._save_to_session(session_id, 'intent', result)
            return result
        except Exception as e:
            logger.error(f"❌ {e}", exc_info=True)
            return {'status': 'error', 'error': str(e)}
    
    async def _classify_with_llm(self, problem: str) -> Optional[Dict[str, Any]]:
        """Use LLM as optimization expert"""
        if not self.llm_client:
            return None
        prompt = f"""You are a mathematical optimization specialist. Analyze:

{problem}

Classify: optimization type (linear_programming, quadratic_programming, mixed_integer_programming, 
nonlinear_programming, combinatorial_optimization), domain (portfolio, routing, scheduling, etc.),
objective, constraints, variables.

Respond ONLY with valid JSON:
{{"optimization_type": "quadratic_programming", "domain_suggestion": "portfolio", "confidence": 0.95,
"reasoning": "Portfolio optimization with quadratic risk", "problem_structure": {{"objective": "minimize_risk",
"objective_type": "quadratic", "constraints": ["budget", "concentration"], "variables": ["weights"],
"variable_count_estimate": 10, "is_convex": true}}}}"""
        try:
            response = await self.llm_client.generate(prompt=prompt, temperature=0.0, max_tokens=500)
            return self._parse_json(response)
        except Exception as e:
            logger.error(f"❌ LLM: {e}")
            return None
    
    def _parse_json(self, text: str) -> Dict[str, Any]:
        """Parse JSON from LLM (handles markdown, extra text)"""
        try:
            return json.loads(text.strip())
        except:
            pass
        for delimiter in ["```json", "```"]:
            if delimiter in text:
                try:
                    return json.loads(text.split(delimiter)[1].split("```")[0].strip())
                except:
                    pass
        matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match)
            except:
                continue
        raise ValueError(f"Parse failed: {text[:200]}")
    
    async def _get_domain_config(self, classification: Dict[str, Any]) -> Dict[str, Any]:
        """Find configured domain or create generic"""
        domain = classification.get('domain_suggestion', '').lower()
        if domain:
            for v in [domain, f"{domain}_optimization", domain.replace('_optimization', ''), domain.replace('_', '')]:
                config = await self._load_from_supabase(v)
                if config:
                    logger.info(f"✅ Match: {v}")
                    return config
        logger.warning("⚠️ No domain, using generic")
        return self._create_generic(classification)
    
    async def _load_from_supabase(self, domain_id: str) -> Optional[Dict[str, Any]]:
        """Load from Supabase or fallback"""
        if self.supabase_client:
            try:
                response = self.supabase_client.table('domain_configs').select('*').eq('domain', domain_id).single().execute()
                if response.data:
                    return response.data
            except:
                pass
        return self._fallback(domain_id) if domain_id in ['portfolio', 'route', 'scheduling'] else None
    
    def _fallback(self, domain_id: str) -> Dict[str, Any]:
        """Minimal fallback for common domains"""
        return {
            'domain': domain_id, 'name': domain_id.replace('_', ' ').title(),
            'industry': 'General', 'version': 1,
            'solver_method': f'_solve_{domain_id}',
            'synthetic_generator_method': f'generate_{domain_id}'
        }
    
    def _create_generic(self, classification: Dict[str, Any]) -> Dict[str, Any]:
        """Generic config from LLM classification"""
        domain = classification.get('domain_suggestion', 'generic')
        return {
            'domain': domain, 'name': domain.replace('_', ' ').title(),
            'industry': 'General', 'version': 1,
            'solver_method': '_solve_generic',
            'synthetic_generator_method': 'generate_generic',
            'optimization_type': classification.get('optimization_type', 'unknown'),
            'problem_structure': classification.get('problem_structure', {}),
            'is_generic': True
        }
    
    async def _save_to_session(self, session_id: str, tool_name: str, results: Dict[str, Any]) -> None:
        """Persist tool results to session table"""
        if not self.supabase_client:
            logger.warning("⚠️ No Supabase, skipping session save")
            return
        try:
            self.supabase_client.table('workflow_sessions').upsert({
                'session_id': session_id,
                'tool_name': tool_name,
                'results': results,
                'timestamp': datetime.utcnow().isoformat()
            }, on_conflict='session_id,tool_name').execute()
            logger.info(f"💾 Saved {tool_name} results to session {session_id[:8]}")
        except Exception as e:
            logger.warning(f"⚠️ Session save failed: {e}")
