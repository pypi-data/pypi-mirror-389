#!/usr/bin/env python3
"""
Explainability Tool
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from anthropic import Anthropic
from ..utils.json_parser import parse_json

logger = logging.getLogger(__name__)


class ExplainabilityTool:
    """Explainability for optimization results"""
    
    def __init__(self):
        try:
            self.openai_client = OpenAI()
            logger.info("✅ OpenAI client initialized for explainability tool")
        except Exception as e:
            logger.warning(f"⚠️ OpenAI client not available for explainability tool: {e}")
            self.openai_client = None
    
    async def explain_optimization(
        self,
        problem_description: str,
        intent_data: Optional[Dict] = None,
        data_analysis: Optional[Dict] = None,
        model_building: Optional[Dict] = None,
        optimization_solution: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Explain optimization results to business stakeholders"""
        try:
            # Use optimization solution if available, otherwise fall back to model building
            if optimization_solution and optimization_solution.get('status') == 'success':
                result_data = optimization_solution.get('result', {})
                logger.info("Using optimization solution for business explanation")
            elif optimization_solution and optimization_solution.get('result', {}).get('status') == 'optimal':
                result_data = optimization_solution.get('result', {})
                logger.info("Using optimization solution for business explanation (optimal status)")
            elif model_building and model_building.get('status') == 'success':
                result_data = model_building.get('result', {})
                logger.info("Using model building result for business explanation")
            else:
                logger.error("No valid optimization results provided - explain_optimization requires real optimization results")
                return {
                    "status": "error",
                    "step": "explainability",
                    "error": "No valid optimization results provided - explain_optimization requires real optimization results",
                    "message": "Please run optimization solving tool first to get optimization results"
                }
            
            status = result_data.get('status', 'unknown')
            objective_value = result_data.get('objective_value', 0)
            optimal_values = result_data.get('optimal_values', {})
            
            prompt = f"""You are a senior business analyst explaining optimization results to C-level executives. Generate actionable business recommendations based on the actual optimization results.

PROBLEM CONTEXT:
{problem_description}

OPTIMIZATION RESULTS:
- Status: {status}
- Objective Value: {objective_value}
- Optimal Values: {optimal_values}

REQUIREMENTS:
1. Use business language, not technical jargon
2. Focus on actionable insights and specific recommendations
3. Quantify benefits and cost savings where possible
4. Address both opportunities and risks
5. Provide clear next steps for implementation
6. Base all recommendations on the actual optimization results above

Generate a comprehensive business explanation with this structure:

{{
  "executive_summary": {{
    "problem_statement": "Clear statement of the original business problem",
    "solution_approach": "How optimization solved the problem",
    "key_findings": [
      "Specific finding 1 based on actual results",
      "Specific finding 2 based on actual results",
      "Specific finding 3 based on actual results"
    ],
    "business_impact": "Quantified impact: cost savings, efficiency gains, or revenue improvement"
  }},
  "detailed_analysis": {{
    "optimal_strategy": "The recommended approach based on optimization results",
    "performance_metrics": "Key performance indicators and their values",
    "resource_allocation": "How resources should be allocated based on optimal values",
    "constraint_analysis": "Which constraints are binding and their implications"
  }},
  "business_recommendations": [
    "Specific actionable recommendation 1 with timeline",
    "Specific actionable recommendation 2 with timeline", 
    "Specific actionable recommendation 3 with timeline"
  ],
  "implementation_roadmap": {{
    "immediate_actions": ["Action to take within 30 days"],
    "short_term_goals": ["Goals for next 3 months"],
    "long_term_strategy": ["Strategic direction for next year"]
  }},
  "risk_assessment": {{
    "implementation_risks": ["Risk 1 with mitigation strategy"],
    "operational_risks": ["Risk 2 with mitigation strategy"],
    "market_risks": ["Risk 3 with mitigation strategy"]
  }},
  "success_metrics": [
    "Metric 1: How to measure success",
    "Metric 2: Target value and timeline",
    "Metric 3: Monitoring approach"
  ]
}}

IMPORTANT: Only provide explanations based on the actual optimization results above. Do not make up or estimate values."""
            
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
            
            return {
                "status": "success",
                "step": "explainability",
                "timestamp": datetime.now().isoformat(),
                "result": result,
                "message": "Explanation generated based on actual optimization results"
            }
        except Exception as e:
            return {"status": "error", "step": "explainability", "error": str(e)}


async def explain_optimization_tool(
    problem_description: str,
    intent_data: Optional[Dict] = None,
    data_analysis: Optional[Dict] = None,
    model_building: Optional[Dict] = None,
    optimization_solution: Optional[Dict] = None
) -> Dict[str, Any]:
    """Tool wrapper for explainability"""
    # This would be called from the main tools orchestrator
    # For now, return a placeholder
    return {"status": "error", "error": "Tool not initialized"}
