#!/usr/bin/env python3
"""
Critique Tool - Truth Guardian for Optimization Responses
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from anthropic import Anthropic
from ..utils.json_parser import parse_json

logger = logging.getLogger(__name__)


class CritiqueTool:
    """Critique Tool - Validates and critiques optimization tool responses for truth and accuracy"""
    
    def __init__(self):
        try:
            self.openai_client = OpenAI()
            logger.info("✅ OpenAI client initialized for critique tool")
        except Exception as e:
            logger.warning(f"⚠️ OpenAI client not available for critique tool: {e}")
            self.openai_client = None
    
    async def critique_response(
        self,
        problem_description: str,
        tool_name: str,
        tool_response: Dict[str, Any],
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Critique and validate a tool's response for truth, accuracy, and business logic
        
        Args:
            problem_description: Original problem description
            tool_name: Name of the tool that generated the response
            tool_response: The tool's response to critique
            context: Additional context for critique
        """
        try:
            logger.info(f"🔍 Critiquing {tool_name} response for truth and accuracy")
            
            # Build critique prompt
            prompt = f"""You are a Truth Guardian - an expert optimization analyst who critiques responses for accuracy, truth, and business logic.

PROBLEM: {problem_description}
TOOL: {tool_name}
CONTEXT: {context or "No additional context"}

TOOL RESPONSE TO CRITIQUE:
{self._format_response_for_critique(tool_response)}

CRITIQUE REQUIREMENTS:
1. **Truth Validation**: Is the response factually correct and logically sound?
2. **Accuracy Check**: Are the classifications, recommendations, or analyses accurate?
3. **Business Logic**: Does the response make business sense for the given problem?
4. **Completeness**: Is the response complete and comprehensive?
5. **Consistency**: Is the response internally consistent?
6. **Relevance**: Is the response relevant to the original problem?

Provide a comprehensive critique with:
- Overall truth score (0.0-1.0)
- Specific accuracy issues found
- Business logic validation
- Completeness assessment
- Recommendations for improvement
- Final verdict (accept/reject/needs_revision)

JSON format:
{{
  "critique_summary": "Overall assessment of the response",
  "truth_score": 0.0-1.0,
  "accuracy_issues": ["list of specific accuracy problems"],
  "business_logic_valid": true/false,
  "completeness_score": 0.0-1.0,
  "consistency_check": "assessment of internal consistency",
  "relevance_score": 0.0-1.0,
  "improvement_recommendations": ["specific recommendations"],
  "final_verdict": "accept|reject|needs_revision",
  "confidence": 0.0-1.0,
  "detailed_analysis": "comprehensive critique explanation"
}}"""
            
            if self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model="ft:gpt-4o-2024-08-06:dcisionai:dcisionai-model:CV0blOhg",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=4000
                )
                resp = response.choices[0].message.content
            else:
                raise Exception("OpenAI client not available")
            result = parse_json(resp)
            
            # Set defaults
            result.setdefault('truth_score', 0.8)
            result.setdefault('accuracy_issues', [])
            result.setdefault('business_logic_valid', True)
            result.setdefault('completeness_score', 0.8)
            result.setdefault('consistency_check', 'consistent')
            result.setdefault('relevance_score', 0.8)
            result.setdefault('improvement_recommendations', [])
            result.setdefault('final_verdict', 'accept')
            result.setdefault('confidence', 0.8)
            result.setdefault('detailed_analysis', 'Response appears valid')
            
            # Add metadata
            result['critique_timestamp'] = datetime.now().isoformat()
            result['tool_critiqued'] = tool_name
            result['problem_context'] = problem_description[:200] + "..." if len(problem_description) > 200 else problem_description
            
            logger.info(f"✅ Critique completed: {result['final_verdict']} (truth: {result['truth_score']:.2f})")
            
            return {
                "status": "success",
                "step": "critique",
                "timestamp": datetime.now().isoformat(),
                "result": result,
                "message": f"Critique completed: {result['final_verdict']} with truth score {result['truth_score']:.2f}"
            }
            
        except Exception as e:
            logger.error(f"Critique failed: {e}")
            return {
                "status": "error",
                "step": "critique",
                "error": str(e),
                "message": f"Critique failed for {tool_name}"
            }
    
    async def critique_intent_classification(
        self,
        problem_description: str,
        intent_result: Dict[str, Any],
        kb_response: Optional[str] = None
    ) -> Dict[str, Any]:
        """Specialized critique for intent classification results"""
        try:
            logger.info("🔍 Critiquing intent classification for truth and accuracy")
            
            # Extract key information
            intent = intent_result.get('intent', 'unknown')
            industry = intent_result.get('industry', 'unknown')
            confidence = intent_result.get('confidence', 0.0)
            reasoning = intent_result.get('reasoning', '')
            
            prompt = f"""You are a Truth Guardian specializing in intent classification critique.

PROBLEM: {problem_description}
CLASSIFIED INTENT: {intent}
CLASSIFIED INDUSTRY: {industry}
CONFIDENCE: {confidence}
REASONING: {reasoning}
KB RESPONSE: {kb_response or "No KB response"}

CRITIQUE FOCUS:
1. **Intent Accuracy**: Is the classified intent actually correct for this problem?
2. **Industry Classification**: Is the industry classification accurate?
3. **Confidence Calibration**: Is the confidence score appropriate?
4. **Reasoning Quality**: Is the reasoning sound and logical?
5. **KB Alignment**: Does the classification align with KB response?
6. **Business Relevance**: Is this classification useful for optimization?

Provide detailed critique:
{{
  "intent_accuracy": 0.0-1.0,
  "industry_accuracy": 0.0-1.0,
  "confidence_calibration": "appropriate|overconfident|underconfident",
  "reasoning_quality": "excellent|good|fair|poor",
  "kb_alignment": 0.0-1.0,
  "business_relevance": 0.0-1.0,
  "overall_truth_score": 0.0-1.0,
  "specific_issues": ["list of specific problems"],
  "improvement_suggestions": ["specific recommendations"],
  "final_verdict": "accept|reject|needs_revision",
  "detailed_analysis": "comprehensive critique"
}}"""
            
            if self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model="ft:gpt-4o-2024-08-06:dcisionai:dcisionai-model:CV0blOhg",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=3000
                )
                resp = response.choices[0].message.content
            else:
                raise Exception("OpenAI client not available")
            result = parse_json(resp)
            
            # Set defaults
            result.setdefault('intent_accuracy', 0.8)
            result.setdefault('industry_accuracy', 0.8)
            result.setdefault('confidence_calibration', 'appropriate')
            result.setdefault('reasoning_quality', 'good')
            result.setdefault('kb_alignment', 0.8)
            result.setdefault('business_relevance', 0.8)
            result.setdefault('overall_truth_score', 0.8)
            result.setdefault('specific_issues', [])
            result.setdefault('improvement_suggestions', [])
            result.setdefault('final_verdict', 'accept')
            result.setdefault('detailed_analysis', 'Intent classification appears valid')
            
            result['critique_timestamp'] = datetime.now().isoformat()
            result['critique_type'] = 'intent_classification'
            
            logger.info(f"✅ Intent critique completed: {result['final_verdict']} (truth: {result['overall_truth_score']:.2f})")
            
            return {
                "status": "success",
                "step": "intent_critique",
                "timestamp": datetime.now().isoformat(),
                "result": result,
                "message": f"Intent critique: {result['final_verdict']} (accuracy: {result['intent_accuracy']:.2f})"
            }
            
        except Exception as e:
            logger.error(f"Intent critique failed: {e}")
            return {
                "status": "error",
                "step": "intent_critique",
                "error": str(e)
            }
    
    async def critique_data_analysis(
        self,
        problem_description: str,
        data_result: Dict[str, Any],
        intent_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Specialized critique for data analysis results"""
        try:
            logger.info("🔍 Critiquing data analysis for truth and accuracy")
            
            # Extract key information
            readiness_score = data_result.get('readiness_score', 0.0)
            data_quality = data_result.get('data_quality', 'unknown')
            simulated_data = data_result.get('simulated_data', {})
            kb_requirements = data_result.get('kb_requirements', {})
            
            prompt = f"""You are a Truth Guardian specializing in data analysis critique.

PROBLEM: {problem_description}
INTENT CONTEXT: {intent_data or "No intent context"}
READINESS SCORE: {readiness_score}
DATA QUALITY: {data_quality}
SIMULATED DATA: {len(simulated_data.get('variables', {}))} variables, {len(simulated_data.get('constraints', {}))} constraints
KB REQUIREMENTS: {len(kb_requirements.get('required_variables', []))} required variables

CRITIQUE FOCUS:
1. **Readiness Assessment**: Is the readiness score appropriate?
2. **Data Quality**: Is the data quality assessment accurate?
3. **Simulated Data**: Are the simulated variables and constraints realistic?
4. **KB Alignment**: Does the analysis align with KB requirements?
5. **Completeness**: Are all necessary data elements covered?
6. **Business Logic**: Does the data analysis make business sense?

Provide detailed critique:
{{
  "readiness_assessment": "appropriate|overestimated|underestimated",
  "data_quality_accuracy": 0.0-1.0,
  "simulated_data_realism": 0.0-1.0,
  "kb_alignment": 0.0-1.0,
  "completeness_score": 0.0-1.0,
  "business_logic_valid": true/false,
  "overall_truth_score": 0.0-1.0,
  "specific_issues": ["list of specific problems"],
  "improvement_suggestions": ["specific recommendations"],
  "final_verdict": "accept|reject|needs_revision",
  "detailed_analysis": "comprehensive critique"
}}"""
            
            if self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model="ft:gpt-4o-2024-08-06:dcisionai:dcisionai-model:CV0blOhg",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=3000
                )
                resp = response.choices[0].message.content
            else:
                raise Exception("OpenAI client not available")
            result = parse_json(resp)
            
            # Set defaults
            result.setdefault('readiness_assessment', 'appropriate')
            result.setdefault('data_quality_accuracy', 0.8)
            result.setdefault('simulated_data_realism', 0.8)
            result.setdefault('kb_alignment', 0.8)
            result.setdefault('completeness_score', 0.8)
            result.setdefault('business_logic_valid', True)
            result.setdefault('overall_truth_score', 0.8)
            result.setdefault('specific_issues', [])
            result.setdefault('improvement_suggestions', [])
            result.setdefault('final_verdict', 'accept')
            result.setdefault('detailed_analysis', 'Data analysis appears valid')
            
            result['critique_timestamp'] = datetime.now().isoformat()
            result['critique_type'] = 'data_analysis'
            
            logger.info(f"✅ Data critique completed: {result['final_verdict']} (truth: {result['overall_truth_score']:.2f})")
            
            return {
                "status": "success",
                "step": "data_critique",
                "timestamp": datetime.now().isoformat(),
                "result": result,
                "message": f"Data critique: {result['final_verdict']} (truth: {result['overall_truth_score']:.2f})"
            }
            
        except Exception as e:
            logger.error(f"Data critique failed: {e}")
            return {
                "status": "error",
                "step": "data_critique",
                "error": str(e)
            }
    
    def _format_response_for_critique(self, response: Dict[str, Any]) -> str:
        """Format tool response for critique analysis"""
        try:
            # Extract key information for critique
            formatted = []
            
            if 'status' in response:
                formatted.append(f"Status: {response['status']}")
            
            if 'result' in response:
                result = response['result']
                if isinstance(result, dict):
                    for key, value in result.items():
                        if key in ['intent', 'industry', 'confidence', 'readiness_score', 'data_quality', 'model_type']:
                            formatted.append(f"{key}: {value}")
                        elif key == 'variables' and isinstance(value, list):
                            formatted.append(f"Variables: {len(value)} variables")
                        elif key == 'constraints' and isinstance(value, list):
                            formatted.append(f"Constraints: {len(value)} constraints")
                        elif key == 'reasoning_steps' and isinstance(value, dict):
                            formatted.append(f"Reasoning Steps: {len(value)} steps")
            
            if 'message' in response:
                formatted.append(f"Message: {response['message']}")
            
            return "\n".join(formatted) if formatted else "No response data available"
            
        except Exception as e:
            logger.warning(f"Error formatting response for critique: {e}")
            return "Error formatting response"


async def critique_tool(problem_description: str, tool_name: str, tool_output: Dict[str, Any], context: Optional[str] = None) -> Dict[str, Any]:
    """Tool wrapper for critique functionality"""
    # This would be called from the main tools orchestrator
    return {"status": "error", "error": "Tool not initialized"}
