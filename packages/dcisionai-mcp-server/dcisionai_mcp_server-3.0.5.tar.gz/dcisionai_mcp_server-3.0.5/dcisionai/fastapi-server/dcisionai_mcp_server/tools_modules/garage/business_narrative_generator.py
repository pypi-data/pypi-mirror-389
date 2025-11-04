import logging
from datetime import datetime
from typing import Dict, Any, Optional
import json
import re

logger = logging.getLogger(__name__)

class BusinessNarrativeGenerator:
    """Generate business narratives from solver logs and optimization results"""
    
    def __init__(self):
        # Initialize OpenAI client for narrative generation
        try:
            from openai import OpenAI
            self.openai_client = OpenAI()
            logger.info("✅ OpenAI client initialized for narrative generation")
        except Exception as e:
            logger.error(f"❌ Failed to initialize OpenAI client: {e}")
            self.openai_client = None
        
        # Initialize Anthropic client as fallback
        try:
            import anthropic
            self.anthropic_client = anthropic.Anthropic()
            logger.info("✅ Anthropic client initialized for narrative generation")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Anthropic client: {e}")
            self.anthropic_client = None
    
    async def generate_business_narrative(
        self,
        problem_description: str,
        optimization_results: Dict[str, Any],
        transparency_data: Optional[Dict[str, Any]] = None,
        model_preference: str = "fine-tuned"
    ) -> Dict[str, Any]:
        """Generate a comprehensive business narrative from optimization results"""
        
        try:
            logger.info("📝 Generating business narrative from optimization results")
            
            # Extract key information
            objective_value = optimization_results.get('objective_value', 0)
            optimal_values = optimization_results.get('optimal_values', {})
            solve_time = optimization_results.get('solve_time', 0)
            status = optimization_results.get('status', 'unknown')
            
            # Extract solver insights
            solver_insights = self._extract_solver_insights(transparency_data)
            
            # Create narrative prompt
            prompt = self._create_narrative_prompt(
                problem_description,
                objective_value,
                optimal_values,
                solve_time,
                status,
                solver_insights
            )
            
            # Generate narrative using LLM
            narrative = await self._generate_narrative_with_llm(prompt, model_preference)
            
            # Parse and structure the response
            structured_narrative = self._structure_narrative_response(narrative)
            
            logger.info("✅ Business narrative generated successfully")
            
            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "narrative": structured_narrative,
                "raw_narrative": narrative
            }
            
        except Exception as e:
            logger.error(f"❌ Business narrative generation failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _extract_solver_insights(self, transparency_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract insights from solver transparency data"""
        if not transparency_data:
            return {}
        
        insights = {
            "solver_type": transparency_data.get('solver_type', 'unknown'),
            "solve_time": transparency_data.get('wall_time', 0),
            "model_complexity": {},
            "solution_quality": {},
            "solver_logs": transparency_data.get('solver_logs', []),
            "raw_output": transparency_data.get('raw_highs_output', '')
        }
        
        # Extract model complexity
        model_info = transparency_data.get('model_info', {})
        insights["model_complexity"] = {
            "variables": model_info.get('num_variables', 0),
            "constraints": model_info.get('num_constraints', 0),
            "nonzeros": model_info.get('num_nonzeros', 0)
        }
        
        # Extract solution quality
        solution_info = transparency_data.get('solution_info', {})
        insights["solution_quality"] = {
            "status": solution_info.get('status', 'unknown'),
            "objective_value": solution_info.get('objective_value', 0),
            "solve_time": solution_info.get('solve_time', 0)
        }
        
        return insights
    
    def _create_narrative_prompt(
        self,
        problem_description: str,
        objective_value: float,
        optimal_values: Dict[str, float],
        solve_time: float,
        status: str,
        solver_insights: Dict[str, Any]
    ) -> str:
        """Create a comprehensive prompt for narrative generation"""
        
        return f"""You are a senior business analyst and optimization expert. Generate a comprehensive business narrative that explains the optimization results in business terms.

PROBLEM CONTEXT:
{problem_description}

OPTIMIZATION RESULTS:
- Status: {status}
- Objective Value: {objective_value}
- Solve Time: {solve_time:.3f} seconds
- Optimal Values: {json.dumps(optimal_values, indent=2)}

SOLVER INSIGHTS:
- Solver Type: {solver_insights.get('solver_type', 'unknown')}
- Model Complexity: {solver_insights.get('model_complexity', {})}
- Solution Quality: {solver_insights.get('solution_quality', {})}
- Solver Logs: {len(solver_insights.get('solver_logs', []))} iterations

Generate a comprehensive business narrative with the following structure:

{{
  "executive_summary": "Brief 2-3 sentence summary of the optimization results and business impact",
  "key_findings": [
    "Finding 1: What the optimization discovered",
    "Finding 2: Key insights about the solution",
    "Finding 3: Performance metrics and efficiency gains"
  ],
  "business_implications": {{
    "financial_impact": "Specific financial implications and cost savings/benefits",
    "operational_impact": "How this affects day-to-day operations",
    "strategic_impact": "Long-term strategic implications",
    "risk_assessment": "Risks and considerations"
  }},
  "recommendations": [
    "Actionable recommendation 1",
    "Actionable recommendation 2",
    "Actionable recommendation 3"
  ],
  "next_steps": [
    "Immediate next step",
    "Short-term action",
    "Long-term consideration"
  ],
  "technical_notes": "Brief technical explanation of the solver performance and model complexity"
}}

Make sure to:
1. Use business language, not technical jargon
2. Focus on actionable insights and recommendations
3. Quantify benefits where possible
4. Address both opportunities and risks
5. Provide clear next steps for implementation
"""

    async def _generate_narrative_with_llm(self, prompt: str, model_preference: str) -> str:
        """Generate narrative using LLM"""
        
        try:
            if model_preference == "fine-tuned" and self.openai_client:
                logger.info("🧠 Using Fine-tuned GPT-4o for narrative generation")
                response = self.openai_client.chat.completions.create(
                    model="ft:gpt-4o-2024-08-06:dcisionai:dcisionai-model:CV0blOhg",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=2000
                )
                narrative = response.choices[0].message.content
                logger.info("✅ Used Fine-tuned GPT-4o for narrative generation")
            else:
                # Fallback to Anthropic
                logger.info("🧠 Using Anthropic Claude-3-5-sonnet for narrative generation")
                response = self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=2000,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}]
                )
                narrative = response.content[0].text
                logger.info("✅ Used Anthropic Claude-3-5-sonnet for narrative generation")
            
            return narrative
            
        except Exception as e:
            logger.error(f"❌ LLM narrative generation failed: {e}")
            raise e
    
    def _structure_narrative_response(self, raw_narrative: str) -> Dict[str, Any]:
        """Parse and structure the LLM response"""
        
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', raw_narrative, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON without markdown
                json_match = re.search(r'(\{.*\})', raw_narrative, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = raw_narrative
            
            structured = json.loads(json_str)
            
            # Ensure all required fields exist
            structured.setdefault("executive_summary", "Optimization completed successfully with significant business value.")
            structured.setdefault("key_findings", ["Key findings will be analyzed based on the optimization results."])
            structured.setdefault("business_implications", {
                "financial_impact": "Financial impact analysis pending",
                "operational_impact": "Operational impact analysis pending",
                "strategic_impact": "Strategic impact analysis pending",
                "risk_assessment": "Risk assessment pending"
            })
            structured.setdefault("recommendations", ["Recommendations will be provided based on the optimization results."])
            structured.setdefault("next_steps", ["Next steps will be outlined based on the optimization results."])
            structured.setdefault("technical_notes", "Technical analysis completed successfully.")
            
            return structured
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to parse structured narrative: {e}")
            # Return fallback structure
            return {
                "executive_summary": "Optimization completed successfully with significant business value.",
                "key_findings": ["Key findings will be analyzed based on the optimization results."],
                "business_implications": {
                    "financial_impact": "Financial impact analysis pending",
                    "operational_impact": "Operational impact analysis pending", 
                    "strategic_impact": "Strategic impact analysis pending",
                    "risk_assessment": "Risk assessment pending"
                },
                "recommendations": ["Recommendations will be provided based on the optimization results."],
                "next_steps": ["Next steps will be outlined based on the optimization results."],
                "technical_notes": "Technical analysis completed successfully.",
                "raw_narrative": raw_narrative
            }
