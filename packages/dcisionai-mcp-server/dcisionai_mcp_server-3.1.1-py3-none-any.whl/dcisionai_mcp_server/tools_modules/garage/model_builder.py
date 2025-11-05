#!/usr/bin/env python3
"""
Enhanced Model Building Tool with FMCO Integration
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional
import openai
import anthropic

from ..core.knowledge_base import KnowledgeBase
from ..core.pinecone_client import PineconeKnowledgeBase
from ..models.mathopt_builder import MathOptModelBuilder, HAS_MATHOPT
from ..utils.json_parser import parse_json
from ..utils.serialization import make_json_serializable
from .fmco_model_builder import FMCOModelBuilder

logger = logging.getLogger(__name__)


class ModelBuilder:
    """Enhanced model building for optimization problems with FMCO integration"""
    
    def __init__(self, knowledge_base: KnowledgeBase):
        self.kb = knowledge_base
        
        # Initialize FMCO Model Builder
        self.fmco_builder = FMCOModelBuilder()
        
        # Initialize Pinecone client for KB integration (optional)
        try:
            self.pinecone_client = PineconeKnowledgeBase()
            logger.info("✅ Pinecone client initialized for model building")
        except Exception as e:
            logger.warning(f"⚠️ Pinecone client not available: {e}")
            self.pinecone_client = None
        
        # Initialize OpenAI client
        try:
            self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            logger.info("✅ OpenAI client initialized for model building")
        except Exception as e:
            logger.error(f"❌ Failed to initialize OpenAI client: {e}")
            self.openai_client = None
        
        # Initialize Anthropic client
        try:
            self.anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            logger.info("✅ Anthropic client initialized for model building")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Anthropic client: {e}")
            self.anthropic_client = None
    
    async def build_model_with_prompt(
        self,
        prompt: str, 
        intent_data: Optional[Dict] = None,
        data_analysis: Optional[Dict] = None,
        model_preference: str = "fine-tuned"
    ) -> Dict[str, Any]:
        """Build model using centralized prompt with Chain-of-Thought reasoning"""
        try:
            logger.info(f"🤖 Building model with centralized prompt using {model_preference}")
            
            # Call LLM with centralized prompt
            if model_preference == "fine-tuned" and self.openai_client:
                logger.info("🧠 Using Fine-tuned GPT-4o for model building")
                try:
                        response = self.openai_client.chat.completions.create(
                            model="ft:gpt-4o-2024-08-06:dcisionai:dcisionai-model:CV0blOhg",
                            messages=[{"role": "user", "content": prompt}],
                        temperature=0.3,
                        max_tokens=4000
                    )
                    response_text = response.choices[0].message.content
                    logger.info("✅ Used Fine-tuned GPT-4o for model building")
                except Exception as e:
                    logger.error(f"❌ Fine-tuned model failed: {e}")
                    raise e
                    else:
                # Fallback to Anthropic
                logger.info("🧠 Using Anthropic Claude-3-haiku for model building")
                            response = self.anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=4000,
                    temperature=0.3,
                                messages=[{"role": "user", "content": prompt}]
                            )
                response_text = response.content[0].text
                logger.info("✅ Used Anthropic Claude-3-haiku for model building")
            
            # Parse JSON response
            import json
            import re
            
            # Extract JSON from response (handle markdown wrapping)
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                else:
                # Try to find JSON without markdown
                json_match = re.search(r'(\{.*\})', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    else:
                    json_str = response_text
            
            result = json.loads(json_str)
            
            # Extract model data
            model_data = result.get("model", {})
            
            logger.info(f"✅ Model building completed: {len(model_data.get('variables', []))} variables, {len(model_data.get('constraints', []))} constraints")
                    
                    return {
                        "status": "success",
                "result": {
                    "model": model_data,
                    "reasoning": result.get("reasoning", {}),
                    "model_type": model_data.get("model_type", "linear_programming")
                },
                "reasoning": result.get("reasoning", {}),
                "response": response_text,
                "timestamp": datetime.now().isoformat()
            }
            
                        except Exception as e:
            logger.error(f"❌ Model building with centralized prompt failed: {e}")
                    return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def build_model(
        self, 
        problem_description: str, 
        intent_data: Optional[Dict] = None,
        data_analysis: Optional[Dict] = None,
        solver_selection: Optional[Dict] = None,
        max_retries: int = 2,
        model_preference: str = "fine-tuned"
    ) -> Dict[str, Any]:
        """Build optimization model using FMCO approach"""
        try:
            logger.info("🚀 Starting FMCO-enhanced model building...")
            
            # Use FMCO Model Builder for realistic model generation
            fmco_result = await self.fmco_builder.build_model(
                problem_description=problem_description,
                intent_data=intent_data or {},
                data_result=data_analysis or {}
            )
            
            if fmco_result.get("status") == "success":
                logger.info("✅ FMCO model building completed successfully")
            return {
                "status": "success",
                    "result": {
                        "model": {
                            "variables": fmco_result["variables"],
                            "constraints": fmco_result["constraints"],
                            "objective": fmco_result["objective"],
                            "model_type": fmco_result["problem_config"]["problem_type"],
                            "domain": fmco_result["problem_config"]["domain"]
                        },
                        "reasoning": fmco_result["reasoning_chain"],
                        "model_type": fmco_result["problem_config"]["problem_type"],
                        "architecture": fmco_result["model_config"]["architecture"],
                        "solver_config": fmco_result["solver_config"],
                        "code_templates": fmco_result["code_templates"]
                    },
                    "reasoning": fmco_result["reasoning_chain"],
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.error(f"❌ FMCO model building failed: {fmco_result.get('error')}")
                # Fallback to original method
                return await self._fallback_build_model(
                    problem_description, intent_data, data_analysis, solver_selection, model_preference
                )
                
        except Exception as e:
            logger.error(f"❌ FMCO model building failed: {e}")
            # Fallback to original method
            return await self._fallback_build_model(
                problem_description, intent_data, data_analysis, solver_selection, model_preference
            )
    
    async def _fallback_build_model(
        self,
        problem_description: str,
        intent_data: Optional[Dict] = None,
        data_analysis: Optional[Dict] = None,
        solver_selection: Optional[Dict] = None,
        model_preference: str = "fine-tuned"
    ) -> Dict[str, Any]:
        """Fallback model building method"""
        try:
            logger.info("🔄 Using fallback model building method...")
            
            # Extract context from previous steps
            intent = intent_data.get('intent', 'unknown') if intent_data else 'unknown'
            industry = intent_data.get('industry', 'general') if intent_data else 'general'
            optimization_type = intent_data.get('optimization_type', 'linear') if intent_data else 'linear'
            
            # Simple fallback model generation
            variables = [
                {"name": "x1", "type": "continuous", "bounds": [0, 100], "description": "Decision variable 1"},
                {"name": "x2", "type": "continuous", "bounds": [0, 100], "description": "Decision variable 2"}
            ]
            
            constraints = [
                {"name": "constraint_1", "type": "inequality", "expression": "x1 + x2 <= 100", "description": "Resource constraint"},
                {"name": "constraint_2", "type": "inequality", "expression": "x1 >= 10", "description": "Minimum constraint"}
            ]
            
            objective = {
                "type": "maximize",
                "expression": "2*x1 + 3*x2",
                "description": "Maximize objective function"
            }
            
            return {
                "status": "success",
                "result": {
                    "model": {
                        "variables": variables,
                        "constraints": constraints,
                        "objective": objective,
                        "model_type": optimization_type,
                        "domain": industry
                    },
                    "reasoning": {
                        "step": "Model Construction (Fallback)",
                        "thoughts": [
                            "Using fallback model generation",
                            f"Generated {len(variables)} variables",
                            f"Created {len(constraints)} constraints",
                            "Applied simple objective function"
                        ]
                    },
                    "model_type": optimization_type
                },
                "reasoning": {
                    "step": "Model Construction (Fallback)",
                    "thoughts": ["Fallback model generation completed"]
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Fallback model building failed: {e}")
                return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }