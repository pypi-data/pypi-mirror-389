#!/usr/bin/env python3
"""
Intent Classification Tool - Updated to use Pinecone Knowledge Base
"""

import hashlib
import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional

from ..core.knowledge_base import KnowledgeBase
from ..core.pinecone_client import PineconeKnowledgeBase
from ..utils.json_parser import parse_json
from .critique_tool import CritiqueTool
# from .pre_intent_sanity_check import PreIntentSanityCheck  # Moved to garage - functionality in SessionAwareOrchestrator
from openai import OpenAI
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class IntentClassifier:
    """Intent classification for optimization problems using Pinecone KB"""
    
    def __init__(self, knowledge_base: KnowledgeBase, cache: Dict[str, Any], orchestrator=None):
        self.kb = knowledge_base
        self.cache = cache
        self.orchestrator = orchestrator
        # self.sanity_check = PreIntentSanityCheck()  # Disabled
        
        # Initialize OpenAI client for fine-tuned model
        try:
            self.openai_client = OpenAI()
            logger.info("✅ OpenAI client initialized for intent classification")
        except Exception as e:
            logger.warning(f"⚠️ OpenAI client not available for intent classification: {e}")
            self.openai_client = None
        
        # Initialize Anthropic client as fallback
        try:
            self.anthropic_client = Anthropic()
            logger.info("✅ Anthropic client initialized for intent classification")
        except Exception as e:
            logger.warning(f"⚠️ Anthropic client not available for intent classification: {e}")
            self.anthropic_client = None
        
        # Initialize Pinecone Knowledge Base client
        try:
            self.pinecone_kb = PineconeKnowledgeBase()
            logger.info("✅ Pinecone Knowledge Base client initialized for intent classification")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Pinecone Knowledge Base client: {e}")
            self.pinecone_kb = None
    
    async def classify_intent(self, problem_description: str, context: Optional[str] = None, model_preference: str = "fine-tuned") -> Dict[str, Any]:
        """Classify optimization problem intent using pre-sanity check + KB response"""
        try:
            logger.info("🔍 Starting intent classification with pre-sanity check...")
            
            # Step 0: Pre-Intent Sanity Check (DISABLED - causing false positives)
            logger.info("🧠 Skipping pre-intent sanity check - proceeding directly to KB classification")
            sanity_result = {'should_proceed': True, 'confidence': 1.0}
            
            # Check if query should proceed to intent classification
            if not sanity_result.get('should_proceed', True):
                logger.info(f"⚠️ Sanity check failed - query not optimization-related: {sanity_result.get('category')}")
                return {
                    "status": "unmatched",
                    "step": "intent_classification",
                    "method": "pre_sanity_check",
                    "timestamp": datetime.now().isoformat(),
                    "result": {
                        "intent": "unmatched",
                        "industry": "unknown",
                        "confidence": sanity_result.get('confidence', 0.0),
                        "matched_use_case": "unmatched",
                        "reasoning": sanity_result.get('reasoning', 'Query not optimization-related'),
                        "sanity_check": sanity_result
                    },
                    "message": f"Query appears to be {sanity_result.get('category', 'non-optimization')} related. Please provide an optimization problem description."
                }
            
            logger.info("✅ Sanity check passed - proceeding to KB classification")
            
            # Step 1: Query Knowledge Base ONLY
            logger.info("📚 Querying Bedrock Knowledge Base...")
            kb_result = await self._classify_with_knowledge_base(problem_description, context)
            
            if kb_result:
                logger.info("✅ KB response received - using directly without validation")
                
                # Check if this is a roadmap response
                if kb_result.get('roadmap_response', False):
                    logger.info(f"⚠️ KB identified unsupported use case - providing roadmap response")
                    return {
                        "status": "roadmap",
                        "step": "intent_classification",
                        "method": "kb_only",
                        "timestamp": datetime.now().isoformat(),
                        "result": kb_result,
                        "message": f"DcisionAI currently focuses on Manufacturing, Retail, and Finance optimization. {kb_result.get('industry', 'This type of').title()} optimization is planned for our roadmap. Please check back later or contact us for custom solutions."
                    }
                else:
                    logger.info(f"✅ KB Classification successful: {kb_result.get('intent')} (confidence: {kb_result.get('confidence')})")
                    return {
                        "status": "success",
                        "step": "intent_classification",
                        "method": "kb_only",
                        "timestamp": datetime.now().isoformat(),
                        "result": kb_result,
                        "message": f"Intent: {kb_result['intent']} (Use Case: {kb_result.get('matched_use_case', 'unknown')}) - KB Confidence: {kb_result.get('confidence', 0.8):.2f}"
                    }
            else:
                # KB failed - provide unmatched response
                logger.warning("⚠️ KB classification failed - providing unmatched response")
                return {
                    "status": "unmatched",
                    "step": "intent_classification",
                    "method": "kb_failed",
                    "timestamp": datetime.now().isoformat(),
                    "message": "DcisionAI is building more vast use cases - please revisit later. Your problem may require a custom optimization approach not yet covered in our knowledge base."
                }
            
            
            
        except Exception as e:
            logger.error(f"Intent classification error: {e}")
            return {"status": "error", "step": "intent_classification", "error": str(e)}
    
    async def classify_intent_with_prompt(
        self, 
        prompt: str, 
        model_preference: str = "fine-tuned"
    ) -> Dict[str, Any]:
        """Classify intent using centralized prompt with Chain-of-Thought reasoning"""
        try:
            logger.info(f"🤖 Classifying intent with centralized prompt using {model_preference}")
            
            # Call LLM with centralized prompt
            if model_preference == "fine-tuned" and self.openai_client:
                logger.info("🧠 Using Fine-tuned GPT-4o for intent classification")
                try:
                    response = self.openai_client.chat.completions.create(
                        model="ft:gpt-4o-2024-08-06:dcisionai:dcisionai-model:CV0blOhg",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3,
                        max_tokens=2000
                    )
                    response_text = response.choices[0].message.content
                    logger.info("✅ Used Fine-tuned GPT-4o for intent classification")
                except Exception as e:
                    logger.error(f"❌ Fine-tuned model failed: {e}")
                    raise e
            else:
                # Fallback to Anthropic
                logger.info("🧠 Using Anthropic Claude-3-haiku for intent classification")
                response = self.anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=2000,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = response.content[0].text
                logger.info("✅ Used Anthropic Claude-3-haiku for intent classification")
            
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
            
            logger.info(f"✅ Intent classification completed: {result.get('result', {}).get('intent', 'unknown')}")
            
            return {
                "status": "success",
                "result": result.get("result", {}),
                "reasoning": result.get("reasoning", {}),
                "response": response_text,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Intent classification with centralized prompt failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def classify_intent_simplified(
        self,
        problem_description: str,
        model_preference: str = "fine-tuned"
    ) -> Dict[str, Any]:
        """Simplified intent classification using fine-tuned model directly - NO KB dependency"""
        try:
            logger.info("🔍 Starting simplified intent classification with fine-tuned model (NO KB dependency)")
            
            # Create prompt for fine-tuned model
            prompt = f"""You are an expert at classifying optimization problems. Analyze the following business problem and classify it into the appropriate optimization category.

PROBLEM DESCRIPTION: {problem_description}

Classify this problem and return a JSON response with the following structure:
{{
  "intent": "ACTUAL_INTENT_FROM_LIST_BELOW",
  "industry": "ACTUAL_INDUSTRY_FROM_LIST_BELOW", 
  "matched_use_case": "specific_use_case_name",
  "confidence": 0.85,
  "reasoning": "Provide a detailed, narrative explanation (3-5 sentences) that explains: (1) what key elements in the problem description led to this classification, (2) what specific optimization challenges are present, (3) why this particular intent category is the best match, and (4) what the user can expect from this optimization approach. Make it business-friendly and educational.",
  "optimization_type": "ACTUAL_TYPE_FROM_LIST_BELOW",
  "complexity": "low|medium|high"
}}

IMPORTANT: Replace the placeholder text above with actual values from the lists below. Make the reasoning field rich and informative.

Available optimization categories (choose ONE):
- finance_portfolio_optimization
- manufacturing_production_planning  
- retail_inventory_optimization
- logistics_route_optimization
- healthcare_staffing
- energy_grid_optimization
- supply_chain_optimization

Available industries (choose ONE):
- FINANCE
- MANUFACTURING
- RETAIL
- LOGISTICS
- HEALTHCARE
- ENERGY
- SUPPLY_CHAIN

Available optimization types (choose ONE):
- linear_programming
- mixed_integer_linear_programming
- quadratic_programming
- nonlinear_programming

Make sure to:
1. Choose the most specific and accurate classification from the lists above
2. Provide a confidence score between 0.7-0.95
3. Give clear reasoning for your classification
4. Ensure the optimization type matches the problem complexity
5. DO NOT use placeholder text - use actual values from the lists
"""

            # Call fine-tuned model
            if model_preference == "fine-tuned" and self.openai_client:
                logger.info("🧠 Using Fine-tuned GPT-4o for intent classification")
                try:
                    response = self.openai_client.chat.completions.create(
                        model="ft:gpt-4o-2024-08-06:dcisionai:dcisionai-model:CV0blOhg",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.2,
                        max_tokens=1000
                    )
                    response_text = response.choices[0].message.content
                    logger.info("✅ Used Fine-tuned GPT-4o for intent classification")
                except Exception as e:
                    logger.error(f"❌ Fine-tuned model failed: {e}")
                    raise e  # Re-raise to trigger graceful failure
            else:
                # Fallback to Anthropic
                logger.info("🧠 Using Anthropic Claude-3-haiku for intent classification")
                response = self.anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=1000,
                    temperature=0.2,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = response.content[0].text
                logger.info("✅ Used Anthropic Claude-3-haiku for intent classification")
            
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
            
            intent_result = json.loads(json_str)
            
            logger.info(f"✅ Intent classified: {intent_result.get('intent')} (confidence: {intent_result.get('confidence')})")
            
            return {
                "status": "success",
                "step": "intent_classification",
                "timestamp": datetime.now().isoformat(),
                "result": intent_result,
                "message": f"Intent classified as {intent_result.get('intent')} with {intent_result.get('confidence', 0)*100:.1f}% confidence"
            }
            
        except Exception as e:
            logger.error(f"❌ Simplified intent classification failed: {e}")
            # Graceful failure - no fake data fallback
            raise e
    
    async def _query_knowledge_base(self, problem_description: str) -> str:
        """Query Bedrock Knowledge Base for relevant use cases"""
        try:
            if not self.bedrock_agent_runtime:
                logger.warning("Bedrock Agent Runtime not available, using fallback")
                return "Knowledge base not available"
            
            # Query the knowledge base
            response = self.bedrock_agent_runtime.retrieve_and_generate(
                input={
                    "text": f"Optimization problem: {problem_description}"
                },
                retrieveAndGenerateConfiguration={
                    "type": "KNOWLEDGE_BASE",
                    "knowledgeBaseConfiguration": {
                        "knowledgeBaseId": self.knowledge_base_id,
                        "modelArn": f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
                    }
                }
            )
            
            # Extract the answer and citations
            answer = response.get('output', {}).get('text', '')
            citations = response.get('citations', [])
            
            # Build context string
            context_parts = [f"Knowledge Base Answer: {answer}"]
            
            if citations:
                context_parts.append("Relevant Use Cases:")
                for i, citation in enumerate(citations[:3], 1):
                    if 'retrievedReferences' in citation:
                        for ref in citation['retrievedReferences'][:1]:
                            content = ref.get('content', {}).get('text', '')
                            location = ref.get('location', {}).get('s3Location', {}).get('uri', '')
                            context_parts.append(f"  {i}. {content[:200]}... (Source: {location})")
            
            return "\n".join(context_parts)
            
        except ClientError as e:
            logger.error(f"Bedrock Knowledge Base query failed: {e}")
            return f"Knowledge base query failed: {e.response['Error']['Message']}"
        except Exception as e:
            logger.error(f"Knowledge base query error: {e}")
            return f"Knowledge base query error: {str(e)}"
    
    async def _classify_with_knowledge_base(self, problem_description: str, context: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Classify intent using Pinecone Knowledge Base (or LLM fallback)"""
        try:
            if not self.pinecone_kb:
                logger.warning("⚠️ Pinecone not available - using LLM-only fallback classification")
                # Fallback to direct LLM classification without KB
                return await self._llm_only_classification(problem_description, context)
            
            # Query Pinecone knowledge base
            kb_result = self.pinecone_kb.classify_intent(problem_description)
            
            if kb_result.get("status") == "success":
                logger.info(f"✅ Pinecone KB classification successful: {kb_result.get('intent')}")
                return kb_result
            elif kb_result.get("status") == "roadmap":
                logger.info(f"⚠️ Pinecone KB identified roadmap case: {kb_result.get('industry')}")
                return kb_result
            else:
                logger.warning(f"⚠️ Pinecone KB classification failed: {kb_result.get('error', 'Unknown error')}")
                return None
            
        except Exception as e:
            logger.error(f"❌ Pinecone KB classification error: {e}")
            return None
    
    async def _analyze_kb_response(self, answer: str, citations: list, problem_description: str) -> Optional[Dict[str, Any]]:
        """Analyze KB response to extract intent classification using rich KB text"""
        try:
            # Build prompt to analyze KB response and extract intent
            prompt = f"""Analyze this Knowledge Base response and extract the optimization intent.

PROBLEM: {problem_description}
KB ANSWER: {answer}

Extract the most appropriate intent from the KB response. Use specific intent names:

MANUFACTURING: resource_allocation, production_planning, scheduling, inventory_management, supply_chain_optimization
FINANCE: portfolio_optimization, risk_management, asset_allocation, capital_allocation, trading_optimization
RETAIL: inventory_management, pricing_optimization, demand_forecasting, assortment_planning, markdown_optimization

JSON format:
{{
  "intent": "production_planning|scheduling",
  "industry": "manufacturing",
  "optimization_type": "linear_programming|integer_programming|mixed_integer_programming",
  "complexity": "low|medium|high",
  "confidence": 0.0-1.0,
  "matched_use_case": "01_Production_Scheduling"
}}"""
            
            # Use fine-tuned model for intent classification
            if model_preference.lower() == "fine-tuned" and self.openai_client:
                try:
                    response = self.openai_client.chat.completions.create(
                        model="ft:gpt-4o-2024-08-06:dcisionai:dcisionai-model:CV0blOhg",
                        max_tokens=1000,
                        messages=[{
                            "role": "user",
                            "content": prompt
                        }]
                    )
                    resp = response.choices[0].message.content
                    logger.info("✅ Used Fine-tuned GPT-4o for intent classification")
                except Exception as e:
                    logger.warning(f"Fine-tuned model failed: {e}, falling back to Anthropic")
                    if self.anthropic_client:
                        response = self.anthropic_client.messages.create(
                            model="claude-3-haiku-20240307",
                            max_tokens=1000,
                            messages=[{
                                "role": "user",
                                "content": prompt
                            }]
                        )
                        resp = response.content[0].text
                    else:
                        raise Exception("No LLM client available")
            else:
                # Use Anthropic as default
                if self.anthropic_client:
                    response = self.anthropic_client.messages.create(
                        model="claude-3-haiku-20240307",
                        max_tokens=1000,
                        messages=[{
                            "role": "user",
                            "content": prompt
                        }]
                    )
                    resp = response.content[0].text
                else:
                    raise Exception("No LLM client available")
            result = parse_json(resp)
            
            # Set defaults
            result.setdefault('intent', 'unknown')
            result.setdefault('industry', 'unknown')
            result.setdefault('optimization_type', 'linear_programming')
            result.setdefault('complexity', 'medium')
            result.setdefault('confidence', 0.8)  # High confidence for KB results
            result.setdefault('matched_use_case', 'unknown')
            
            # Use the rich KB response text as reasoning (without citations)
            result['reasoning'] = answer
            
            # Fix use case ID mapping to match our expected format
            matched_use_case = result.get('matched_use_case', 'unknown')
            if matched_use_case != 'unknown':
                result['matched_use_case'] = self._map_kb_use_case_to_expected(matched_use_case, result.get('intent', ''), result.get('industry', ''))
            
            # Validate if this is actually a supported optimization problem
            if not self._validate_supported_use_case(result, answer, problem_description):
                logger.info("⚠️ KB response doesn't match our supported optimization problems - providing roadmap response")
                # Return a special result that indicates roadmap response needed
                return {
                    "intent": "roadmap",
                    "industry": result.get('industry', 'unknown'),
                    "matched_use_case": "roadmap",
                    "confidence": 0.0,
                    "reasoning": "This optimization problem is not yet supported in our current platform",
                    "roadmap_response": True
                }
            
            # If validation passes, return the result
            return result
            
        except Exception as e:
            logger.error(f"KB response analysis failed: {e}")
            return None
    
    async def _classify_with_truth_tool(self, problem_description: str, context: Optional[str] = None, previous_result: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Classify intent using Truth tool validation"""
        try:
            # Build truth validation prompt
            prompt = f"""Validate and classify this optimization problem using truth validation.

PROBLEM: {problem_description}
CONTEXT: {context or "No additional context"}
PREVIOUS_ANALYSIS: {previous_result or "No previous analysis"}

Validate the problem classification and provide the most accurate intent. Use specific intent names:

MANUFACTURING: resource_allocation, production_planning, scheduling, inventory_management, supply_chain_optimization
FINANCE: portfolio_optimization, risk_management, asset_allocation, capital_allocation, trading_optimization
RETAIL: inventory_management, pricing_optimization, demand_forecasting, assortment_planning, markdown_optimization

JSON format:
{{
  "intent": "production_planning|scheduling",
  "industry": "manufacturing",
  "optimization_type": "linear_programming|integer_programming|mixed_integer_programming",
  "complexity": "low|medium|high",
  "confidence": 0.0-1.0,
  "matched_use_case": "01_Production_Scheduling",
  "reasoning": "truth validation explanation",
  "validation_score": 0.0-1.0
}}"""
            
            # Use fine-tuned model for intent classification
            if model_preference.lower() == "fine-tuned" and self.openai_client:
                try:
                    response = self.openai_client.chat.completions.create(
                        model="ft:gpt-4o-2024-08-06:dcisionai:dcisionai-model:CV0blOhg",
                        max_tokens=1000,
                        messages=[{
                            "role": "user",
                            "content": prompt
                        }]
                    )
                    resp = response.choices[0].message.content
                    logger.info("✅ Used Fine-tuned GPT-4o for intent classification")
                except Exception as e:
                    logger.warning(f"Fine-tuned model failed: {e}, falling back to Anthropic")
                    if self.anthropic_client:
                        response = self.anthropic_client.messages.create(
                            model="claude-3-haiku-20240307",
                            max_tokens=1000,
                            messages=[{
                                "role": "user",
                                "content": prompt
                            }]
                        )
                        resp = response.content[0].text
                    else:
                        raise Exception("No LLM client available")
            else:
                # Use Anthropic as default
                if self.anthropic_client:
                    response = self.anthropic_client.messages.create(
                        model="claude-3-haiku-20240307",
                        max_tokens=1000,
                        messages=[{
                            "role": "user",
                            "content": prompt
                        }]
                    )
                    resp = response.content[0].text
                else:
                    raise Exception("No LLM client available")
            result = parse_json(resp)
            
            # Set defaults
            result.setdefault('intent', 'unknown')
            result.setdefault('industry', 'unknown')
            result.setdefault('optimization_type', 'linear_programming')
            result.setdefault('complexity', 'medium')
            result.setdefault('confidence', 0.7)  # Medium confidence for truth validation
            result.setdefault('matched_use_case', 'unknown')
            result.setdefault('reasoning', 'Truth tool validation')
            result.setdefault('validation_score', 0.8)
            
            return result
            
        except Exception as e:
            logger.error(f"Truth tool classification failed: {e}")
            return None
    
    async def _classify_with_llm(self, problem_description: str, context: Optional[str] = None, kb_result: Optional[Dict] = None) -> Dict[str, Any]:
        """Classify intent using LLM fallback"""
        try:
            # Build comprehensive LLM prompt with all previous results
            prompt = f"""Classify this optimization problem using comprehensive analysis.

PROBLEM: {problem_description}
CONTEXT: {context or "No additional context"}

PREVIOUS_ANALYSES:
KB_RESULT: {kb_result or "No KB result"}

Provide the most accurate classification. Use specific intent names:

MANUFACTURING: resource_allocation, production_planning, scheduling, inventory_management, supply_chain_optimization
FINANCE: portfolio_optimization, risk_management, asset_allocation, capital_allocation, trading_optimization
RETAIL: inventory_management, pricing_optimization, demand_forecasting, assortment_planning, markdown_optimization

JSON format:
{{
  "intent": "production_planning|scheduling",
  "industry": "manufacturing",
  "optimization_type": "linear_programming|integer_programming|mixed_integer_programming",
  "complexity": "low|medium|high",
  "confidence": 0.0-1.0,
  "matched_use_case": "01_Production_Scheduling",
  "reasoning": "comprehensive LLM analysis"
}}"""
            
            # Use fine-tuned model for intent classification
            if model_preference.lower() == "fine-tuned" and self.openai_client:
                try:
                    response = self.openai_client.chat.completions.create(
                        model="ft:gpt-4o-2024-08-06:dcisionai:dcisionai-model:CV0blOhg",
                        max_tokens=1000,
                        messages=[{
                            "role": "user",
                            "content": prompt
                        }]
                    )
                    resp = response.choices[0].message.content
                    logger.info("✅ Used Fine-tuned GPT-4o for intent classification")
                except Exception as e:
                    logger.warning(f"Fine-tuned model failed: {e}, falling back to Anthropic")
                    if self.anthropic_client:
                        response = self.anthropic_client.messages.create(
                            model="claude-3-haiku-20240307",
                            max_tokens=1000,
                            messages=[{
                                "role": "user",
                                "content": prompt
                            }]
                        )
                        resp = response.content[0].text
                    else:
                        raise Exception("No LLM client available")
            else:
                # Use Anthropic as default
                if self.anthropic_client:
                    response = self.anthropic_client.messages.create(
                        model="claude-3-haiku-20240307",
                        max_tokens=1000,
                        messages=[{
                            "role": "user",
                            "content": prompt
                        }]
                    )
                    resp = response.content[0].text
                else:
                    raise Exception("No LLM client available")
            result = parse_json(resp)
            
            # Set defaults
            result.setdefault('intent', 'unknown')
            result.setdefault('industry', 'unknown')
            result.setdefault('optimization_type', 'linear_programming')
            result.setdefault('complexity', 'medium')
            result.setdefault('confidence', 0.6)  # Lower confidence for LLM fallback
            result.setdefault('matched_use_case', 'unknown')
            result.setdefault('reasoning', 'LLM fallback analysis')
            
            return result
            
        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            return {
                'intent': 'unknown',
                'industry': 'unknown',
                'optimization_type': 'linear_programming',
                'complexity': 'medium',
                'confidence': 0.3,
                'matched_use_case': 'unknown',
                'reasoning': 'LLM classification failed'
            }
    
    def _map_kb_use_case_to_expected(self, kb_use_case: str, intent: str, industry: str) -> str:
        """Map KB use case IDs to our expected format"""
        # Common mappings from KB responses to our expected format
        use_case_mappings = {
            # Portfolio optimization mappings
            '01_Asset_Allocation': '01_Portfolio_Optimization',
            '01_Portfolio_Optimization': '01_Portfolio_Optimization',
            'Portfolio_Optimization': '01_Portfolio_Optimization',
            'Asset_Allocation': '01_Portfolio_Optimization',
            
            # Inventory optimization mappings
            '02_Inventory_Allocation_Optimization': '01_Inventory_Optimization',
            '01_Inventory_Optimization': '01_Inventory_Optimization',
            'Inventory_Optimization': '01_Inventory_Optimization',
            'Inventory_Allocation': '01_Inventory_Optimization',
            
            # Production scheduling mappings
            '01_Production_Scheduling': '01_Production_Scheduling',
            'Production_Scheduling': '01_Production_Scheduling',
            
            # Pricing optimization mappings
            '03_Pricing_Optimization': '02_Pricing_Optimization',
            '02_Pricing_Optimization': '02_Pricing_Optimization',
            'Pricing_Optimization': '02_Pricing_Optimization',
            
            # Markdown optimization mappings
            '04_Markdown_Optimization': '01_Markdown_Optimization',
            '01_Markdown_Optimization': '01_Markdown_Optimization',
            'Markdown_Optimization': '01_Markdown_Optimization',
            
            # Vehicle routing mappings
            '01_Vehicle_Routing_Optimization': '01_Vehicle_Routing',
            '01_Vehicle_Routing_Problem': '01_Vehicle_Routing',
            'Vehicle_Routing': '01_Vehicle_Routing',
            
            # Grid optimization mappings
            '01_Grid_Optimization': '01_Grid_Optimization',
            'Grid_Optimization': '01_Grid_Optimization',
            
            # Risk management mappings
            '02_Risk_Management': '02_Risk_Management',
            'Risk_Management': '02_Risk_Management',
        }
        
        # Direct mapping if available
        if kb_use_case in use_case_mappings:
            return use_case_mappings[kb_use_case]
        
        # Fallback: try to construct expected format based on intent and industry
        if 'portfolio' in intent.lower() and 'finance' in industry.lower():
            return '01_Portfolio_Optimization'
        elif 'inventory' in intent.lower():
            if 'retail' in industry.lower():
                return '01_Inventory_Optimization'
            elif 'manufacturing' in industry.lower():
                return '02_Inventory_Optimization'
        elif 'production' in intent.lower() or 'scheduling' in intent.lower():
            return '01_Production_Scheduling'
        elif 'pricing' in intent.lower():
            return '02_Pricing_Optimization'
        elif 'markdown' in intent.lower():
            return '01_Markdown_Optimization'
        elif 'routing' in intent.lower() or 'delivery' in intent.lower():
            return '01_Vehicle_Routing'
        elif 'grid' in intent.lower() or 'energy' in intent.lower():
            return '01_Grid_Optimization'
        elif 'risk' in intent.lower():
            return '02_Risk_Management'
        
        # Default fallback
        return kb_use_case
    
    def _validate_supported_use_case(self, result: Dict[str, Any], kb_answer: str, problem_description: str) -> bool:
        """Validate if the KB response actually matches our supported optimization problems"""
        try:
            # Get the identified industry and intent
            industry = result.get('industry', '').lower()
            intent = result.get('intent', '').lower()
            confidence = result.get('confidence', 0)
            
            # Check if industry is in our supported wedge
            supported_industries = ['manufacturing', 'retail', 'finance']
            if industry not in supported_industries:
                logger.info(f"Industry '{industry}' not in supported wedge")
                return False
            
            # Check if the KB answer actually relates to our supported use cases
            # Look for indicators that this is a forced match vs genuine match
            # Note: "can be formulated as" is actually a legitimate phrase in optimization
            # so we should be more careful about flagging it
            forced_match_indicators = [
                'does not directly address',
                'however, some general principles',
                'based on the search results provided, this optimization problem does not seem to have a direct solution',
                'this optimization problem is not yet supported in our current platform'
            ]
            
            kb_answer_lower = kb_answer.lower()
            for indicator in forced_match_indicators:
                if indicator in kb_answer_lower:
                    logger.info(f"Forced match detected: '{indicator}'")
                    return False
            
            # Check confidence threshold
            if confidence < 0.7:
                logger.info(f"Low confidence: {confidence}")
                return False
            
            # REMOVED KEYWORD MATCHING - Trust the KB response completely
            # The KB has already analyzed the problem and determined the industry/intent
            # We should trust its classification rather than doing keyword matching
            
            logger.info(f"✅ KB validation passed: {industry} - {intent} (confidence: {confidence})")
            return True
            
        except Exception as e:
            logger.error(f"Use case validation failed: {e}")
            return False


    async def _llm_only_classification(self, problem_description: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Fallback LLM-only intent classification when Pinecone is not available"""
        try:
            logger.info("🤖 Using LLM-only intent classification (no KB)")
            
            # Use Claude for classification
            prompt = f"""Classify this optimization problem into the appropriate category.

Problem: {problem_description}

Analyze and return a JSON object with:
1. "intent": The optimization type (e.g., "vehicle_routing", "job_shop_scheduling", "store_layout_optimization", "portfolio_rebalancing")
2. "industry": The industry (LOGISTICS, MANUFACTURING, RETAIL, FINANCE)
3. "matched_use_case": Specific use case identifier (snake_case)
4. "confidence": Confidence score (0.0 to 1.0)
5. "reasoning": Brief explanation of classification
6. "optimization_type": Type of optimization (linear_programming, mixed_integer_programming, etc.)
7. "complexity": Problem complexity (low, medium, high)

Supported use cases:
- LOGISTICS: vehicle_routing, route_optimization, fleet_management
- MANUFACTURING: job_shop_scheduling, workforce_rostering, maintenance_scheduling
- RETAIL: store_layout_optimization, promotion_scheduling, inventory_management
- FINANCE: portfolio_rebalancing, portfolio_optimization, trading_schedule

Return ONLY the JSON object, no other text."""

            response = self.claude_client.messages.create(
                model="claude-3-haiku-20240307",  # Same model as main classifier
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse response
            response_text = response.content[0].text.strip()
            result = parse_json(response_text)
            
            if result and isinstance(result, dict):
                logger.info(f"✅ LLM classification: {result.get('intent')} ({result.get('confidence', 0):.0%} confidence)")
                return result
            else:
                logger.error("❌ Failed to parse LLM classification response")
                return None
                
        except Exception as e:
            logger.error(f"❌ LLM-only classification failed: {e}")
            return None


async def classify_intent_tool(problem_description: str, context: Optional[str] = None) -> Dict[str, Any]:
    """Tool wrapper for intent classification"""
    # This would be called from the main tools orchestrator
    # For now, return a placeholder
    return {"status": "error", "error": "Tool not initialized"}
