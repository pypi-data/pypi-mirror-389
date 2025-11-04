#!/usr/bin/env python3
"""
Pre-Intent Sanity Check Module
Lightweight LLM check to filter out non-optimization queries before intent classification
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from anthropic import Anthropic

logger = logging.getLogger(__name__)

class PreIntentSanityCheck:
    """Pre-intent sanity check to filter out non-optimization queries"""
    
    def __init__(self):
        try:
            self.openai_client = OpenAI()
            logger.info("✅ OpenAI client initialized for pre-intent sanity check")
        except Exception as e:
            logger.warning(f"⚠️ OpenAI client not available for pre-intent sanity check: {e}")
            self.openai_client = None
    
    async def check_query_sanity(self, problem_description: str) -> Dict[str, Any]:
        """
        Perform pre-intent sanity check to determine if query is optimization-related
        
        Returns:
            Dict with sanity check results including:
            - is_optimization_related: bool
            - confidence: float
            - reasoning: str
            - should_proceed: bool
            - category: str (optimization/personal/technical/other)
        """
        try:
            logger.info("🔍 Performing pre-intent sanity check...")
            
            # Skip sanity check for very short queries
            if len(problem_description.strip()) < 10:
                logger.info("⚠️ Query too short - skipping sanity check")
                return {
                    "is_optimization_related": False,
                    "confidence": 0.9,
                    "reasoning": "Query too short to determine optimization intent",
                    "should_proceed": False,
                    "category": "too_short"
                }
            
            # Quick pattern-based check first
            quick_check = self._detect_obvious_non_optimization(problem_description)
            if quick_check:
                logger.info(f"🚫 Quick pattern match: {quick_check['category']}")
                return quick_check
            
            # Create sanity check prompt
            sanity_prompt = self._create_sanity_check_prompt(problem_description)
            
            # Call LLM for sanity check
            if self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model="ft:gpt-4o-2024-08-06:dcisionai:dcisionai-model:CV0blOhg",
                    messages=[{"role": "user", "content": sanity_prompt}],
                    temperature=0.3,
                    max_tokens=500
                )
                response_text = response.choices[0].message.content
            else:
                raise Exception("OpenAI client not available")
            
            # Parse response
            sanity_result = self._parse_sanity_response(response_text)
            
            logger.info(f"✅ Sanity check completed: {sanity_result['category']} (confidence: {sanity_result['confidence']:.2f})")
            
            return sanity_result
            
        except Exception as e:
            logger.error(f"❌ Sanity check error: {str(e)}")
            # Default to proceeding if sanity check fails
            return {
                "is_optimization_related": True,
                "confidence": 0.5,
                "reasoning": f"Sanity check failed: {str(e)}",
                "should_proceed": True,
                "category": "error"
            }
    
    def _create_sanity_check_prompt(self, problem_description: str) -> str:
        """Create prompt for sanity check"""
        return f"""You are a pre-filter for an optimization platform. Your job is to quickly determine if a user query is related to optimization problems.

User Query: "{problem_description}"

Analyze this query and determine:
1. Is this query related to optimization, scheduling, planning, resource allocation, or business process improvement?
2. Is this a personal question, technical support, or completely unrelated to optimization?

Respond with ONLY a JSON object in this exact format:
{{
    "is_optimization_related": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of your decision",
    "category": "optimization/personal/technical/other"
}}

Categories:
- "optimization": Query is clearly about optimization, scheduling, planning, resource allocation, etc.
- "personal": Personal questions, greetings, casual conversation
- "technical": Technical support, computer problems, non-optimization technical issues
- "other": Random text, non-English, numbers only, special characters, etc.

Examples:
- "Help me optimize production scheduling" → optimization
- "How are you doing?" → personal  
- "My computer is not working" → technical
- "asdfghjkl" → other
- "What is the weather?" → other

Respond with ONLY the JSON object:"""
    
    def _parse_sanity_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response for sanity check"""
        try:
            # Extract JSON from response
            response_clean = response.strip()
            if response_clean.startswith('```json'):
                response_clean = response_clean[7:]
            if response_clean.endswith('```'):
                response_clean = response_clean[:-3]
            
            # Parse JSON
            sanity_data = json.loads(response_clean)
            
            # Validate required fields
            required_fields = ['is_optimization_related', 'confidence', 'reasoning', 'category']
            for field in required_fields:
                if field not in sanity_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Determine if should proceed
            should_proceed = (
                sanity_data['is_optimization_related'] and 
                sanity_data['confidence'] > 0.3 and
                sanity_data['category'] == 'optimization'
            )
            
            return {
                "is_optimization_related": sanity_data['is_optimization_related'],
                "confidence": float(sanity_data['confidence']),
                "reasoning": sanity_data['reasoning'],
                "should_proceed": should_proceed,
                "category": sanity_data['category']
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to parse sanity check response: {str(e)}")
            # Default to proceeding if parsing fails
            return {
                "is_optimization_related": True,
                "confidence": 0.5,
                "reasoning": f"Failed to parse response: {str(e)}",
                "should_proceed": True,
                "category": "parse_error"
            }
    
    def _detect_obvious_non_optimization(self, problem_description: str) -> Optional[Dict[str, Any]]:
        """Quick pattern-based detection for obvious non-optimization queries - DISABLED"""
        # DISABLED: This was causing false positives for portfolio optimization queries
        # The word "rain" was being matched in "constraints" causing valid queries to be rejected
        return None
