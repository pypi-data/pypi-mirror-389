"""
Business Interpretation for DcisionAI Optimization Results

Simplified, practical implementation adapted from model-builder
"""

import json
import logging
import re
import uuid
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)


@dataclass
class BusinessInterpretation:
    """Business-friendly solution interpretation"""
    interpretation_id: str
    summary: str
    key_decisions: Dict[str, str]
    performance_metrics: Dict[str, Any]
    implementation_steps: List[str]
    risks_and_assumptions: List[str]
    sensitivity_insights: List[str] = field(default_factory=list)
    what_if_scenarios: List[Dict[str, str]] = field(default_factory=list)
    confidence_score: float = 0.85
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "interpretation_id": self.interpretation_id,
            "summary": self.summary,
            "key_decisions": self.key_decisions,
            "performance_metrics": self.performance_metrics,
            "implementation_steps": self.implementation_steps,
            "risks_and_assumptions": self.risks_and_assumptions,
            "sensitivity_insights": self.sensitivity_insights,
            "what_if_scenarios": self.what_if_scenarios,
            "confidence_score": self.confidence_score,
            "created_at": self.created_at.isoformat()
        }


class BusinessInterpreter:
    """Interprets optimization solutions for business users"""
    
    def __init__(self, llm_caller: Callable[[str, str, int], str]):
        """
        Initialize interpreter
        
        Args:
            llm_caller: Function that takes (system_prompt, user_message, max_tokens) -> str
        """
        self.llm_caller = llm_caller
        self.logger = logging.getLogger(__name__)
    
    async def interpret_solution(
        self,
        solution: Dict[str, Any],
        problem_description: str,
        domain_id: str,
        config: Dict[str, Any]
    ) -> BusinessInterpretation:
        """
        Generate business-friendly interpretation of optimization solution
        
        Args:
            solution: Solution dict with 'solution', 'fitness', 'generations_run', etc.
            problem_description: Original natural language problem
            domain_id: Domain identifier (portfolio, retail_layout, etc.)
            config: Domain configuration
        
        Returns:
            BusinessInterpretation with actionable insights
        """
        try:
            self.logger.info(f"Interpreting solution for {domain_id}")
            
            # Generate interpretation using LLM
            prompt = self._build_interpretation_prompt(
                solution=solution,
                problem_description=problem_description,
                domain_id=domain_id,
                config=config
            )
            
            system_prompt = "You are a business optimization consultant. Interpret optimization results for business stakeholders in clear, actionable language."
            
            response = self.llm_caller(system_prompt, prompt, 2000)
            
            # Parse LLM response
            interpretation_data = self._parse_json_response(response)
            
            if interpretation_data:
                return BusinessInterpretation(
                    interpretation_id=str(uuid.uuid4()),
                    summary=interpretation_data.get("summary", "Optimization complete"),
                    key_decisions=interpretation_data.get("key_decisions", {}),
                    performance_metrics=interpretation_data.get("performance_metrics", {}),
                    implementation_steps=interpretation_data.get("implementation_steps", []),
                    risks_and_assumptions=interpretation_data.get("risks_and_assumptions", []),
                    sensitivity_insights=interpretation_data.get("sensitivity_insights", []),
                    what_if_scenarios=interpretation_data.get("what_if_scenarios", []),
                    confidence_score=0.85
                )
            else:
                # Fallback interpretation
                return self._create_fallback_interpretation(solution, domain_id)
                
        except Exception as e:
            self.logger.error(f"Interpretation failed: {e}")
            return self._create_fallback_interpretation(solution, domain_id)
    
    def _build_interpretation_prompt(
        self,
        solution: Dict[str, Any],
        problem_description: str,
        domain_id: str,
        config: Dict[str, Any]
    ) -> str:
        """Build LLM prompt for solution interpretation"""
        
        domain_name = config.get('name', domain_id)
        objective_value = solution.get('fitness', solution.get('objective_value', 'N/A'))
        solve_time = solution.get('solve_time', solution.get('duration_seconds', 'N/A'))
        
        # Format solution values
        solution_values = solution.get('solution', {})
        solution_str = self._format_solution_values(solution_values, domain_id)
        
        # Build domain-specific context
        domain_context = self._get_domain_context(domain_id, config)
        
        prompt = f"""
Interpret this {domain_name} optimization result for business stakeholders.

PROBLEM DESCRIPTION:
{problem_description}

SOLUTION RESULTS:
- Objective Value: {objective_value}
- Solve Time: {solve_time} seconds
- Solution:
{solution_str}

DOMAIN CONTEXT:
{domain_context}

Provide a comprehensive business interpretation in JSON format:

{{
  "summary": "2-3 sentence executive summary of what was optimized and achieved",
  "key_decisions": {{
    "decision_name": "Clear explanation in business terms (not technical)",
    ...
  }},
  "performance_metrics": {{
    "metric_name": "value with business interpretation",
    ...
  }},
  "implementation_steps": [
    "Step 1: Specific action (Target: timeframe)",
    "Step 2: Next action with dependencies",
    ...
  ],
  "risks_and_assumptions": [
    "Key assumption and how to validate it",
    "Potential risk and mitigation strategy",
    ...
  ],
  "sensitivity_insights": [
    "How solution changes if parameter X varies",
    "Robustness to uncertainty in input Y",
    ...
  ],
  "what_if_scenarios": [
    {{"scenario": "If X changes to Y", "impact": "Solution adjusts to Z"}},
    ...
  ]
}}

Important:
- Use business language, not mathematical jargon
- Make recommendations specific and actionable
- Include timeframes for implementation steps
- Focus on practical insights stakeholders can act on
- Explain WHY decisions matter, not just WHAT they are
"""
        return prompt
    
    def _format_solution_values(self, solution: Dict[str, Any], domain_id: str) -> str:
        """Format solution values for display"""
        if not solution:
            return "  (Solution details available in technical output)"
        
        lines = []
        # Limit to top 10 most important items
        for i, (key, value) in enumerate(list(solution.items())[:10]):
            if isinstance(value, float):
                lines.append(f"  {key}: {value:.4f}")
            elif isinstance(value, dict):
                lines.append(f"  {key}: {json.dumps(value, indent=4)}")
            elif isinstance(value, list):
                lines.append(f"  {key}: {value[:5]}{'...' if len(value) > 5 else ''}")
            else:
                lines.append(f"  {key}: {value}")
            
            if i >= 9:  # Limit to 10 items
                lines.append(f"  ... ({len(solution) - 10} more items)")
                break
        
        return "\n".join(lines)
    
    def _get_domain_context(self, domain_id: str, config: Dict[str, Any]) -> str:
        """Get domain-specific context for interpretation"""
        
        domain_contexts = {
            'portfolio': """
This is a portfolio optimization problem.
Key metrics: expected return, risk (volatility), Sharpe ratio, diversification.
Decisions: asset allocations (% of capital).
Business impact: Investment performance, risk management.
""",
            'retail_layout': """
This is a store layout optimization problem.
Key metrics: space efficiency, revenue per square foot, placement quality, accessibility.
Decisions: product-to-shelf assignments.
Business impact: Sales revenue, customer experience, operational efficiency.
""",
            'job_shop': """
This is a job shop scheduling problem.
Key metrics: makespan (total time), machine utilization, job completion times.
Decisions: job-to-machine assignments and sequencing.
Business impact: Production throughput, resource utilization, delivery times.
""",
            'vrp': """
This is a vehicle routing problem.
Key metrics: total distance/cost, number of vehicles, route efficiency.
Decisions: customer-to-vehicle assignments and route sequences.
Business impact: Delivery costs, fleet utilization, customer service.
""",
            'workforce': """
This is a workforce scheduling problem.
Key metrics: total cost, coverage, employee satisfaction, overtime hours.
Decisions: employee-to-shift assignments.
Business impact: Labor costs, service quality, employee satisfaction.
""",
            'supply_chain': """
This is a supply chain optimization problem.
Key metrics: total cost, inventory levels, fill rates, lead times.
Decisions: inventory policies, replenishment quantities, sourcing.
Business impact: Supply chain costs, service levels, working capital.
""",
            'maintenance': """
This is a maintenance scheduling problem.
Key metrics: downtime, maintenance costs, equipment reliability.
Decisions: maintenance task timing and resource allocation.
Business impact: Equipment uptime, maintenance costs, operational reliability.
""",
            'trading': """
This is a trading strategy optimization problem.
Key metrics: returns, risk, transaction costs, holding periods.
Decisions: buy/sell signals, position sizes, timing.
Business impact: Trading performance, risk exposure, capital efficiency.
"""
        }
        
        context = domain_contexts.get(domain_id, f"This is a {config.get('name', domain_id)} optimization problem.")
        
        # Add objectives from config
        objectives = config.get('objective_config', {}).get('objectives', [])
        if objectives:
            context += f"\nOptimization objectives: {', '.join(objectives[:3])}"
        
        return context.strip()
    
    def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from LLM response"""
        try:
            # Try direct JSON parse
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
            
            # Try to find any JSON object in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass
            
            self.logger.warning("Failed to parse JSON from LLM response")
            return None
    
    def _create_fallback_interpretation(self, solution: Dict[str, Any], domain_id: str) -> BusinessInterpretation:
        """Create fallback interpretation when LLM fails"""
        objective_value = solution.get('fitness', solution.get('objective_value', 'N/A'))
        
        return BusinessInterpretation(
            interpretation_id=str(uuid.uuid4()),
            summary=f"Optimization complete with objective value: {objective_value}",
            key_decisions={
                "Solution": "Optimal solution found (see technical details)"
            },
            performance_metrics={
                "objective_value": objective_value,
                "solve_time": solution.get('solve_time', solution.get('duration_seconds', 'N/A'))
            },
            implementation_steps=[
                "1. Review the detailed solution in the technical output",
                "2. Validate the solution meets business constraints",
                "3. Implement the recommended configuration",
                "4. Monitor performance metrics after deployment"
            ],
            risks_and_assumptions=[
                "Solution assumes input data is accurate",
                "Business conditions may change after optimization",
                "Implementation details may require adjustment"
            ],
            sensitivity_insights=[],
            what_if_scenarios=[],
            confidence_score=0.6  # Lower confidence for fallback
        )

