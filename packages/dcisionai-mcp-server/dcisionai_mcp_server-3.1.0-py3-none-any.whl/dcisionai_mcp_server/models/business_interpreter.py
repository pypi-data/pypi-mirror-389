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
        """Create fallback interpretation when LLM fails - with domain-specific technical details"""
        objective_value = solution.get('fitness', solution.get('objective_value', 'N/A'))
        
        # Extract domain-specific technical details
        key_decisions = self._extract_technical_details(solution, domain_id)
        
        return BusinessInterpretation(
            interpretation_id=str(uuid.uuid4()),
            summary=f"Optimization complete with objective value: {objective_value}",
            key_decisions=key_decisions,
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
    
    def _extract_technical_details(self, solution: Dict[str, Any], domain_id: str) -> Dict[str, str]:
        """Extract domain-specific technical details from solution"""
        key_decisions = {}
        best_sol = solution.get('best_solution', {}) or solution.get('solution', {})
        
        if domain_id in ['vrp', 'vrp_v1']:
            # VRP: Extract route assignments
            routes = best_sol.get('routes', [])
            if routes:
                key_decisions['fleet_deployment'] = f"Deploy {len(routes)} vehicles to serve all customers efficiently"
                
                # Show first 5 routes in detail, summarize rest
                for i, route in enumerate(routes[:5]):
                    if isinstance(route, dict):
                        vehicle_id = route.get('vehicle_id', i+1)
                        customers = route.get('customers', [])
                        distance = route.get('total_distance', 0)
                        
                        if customers:
                            if len(customers) <= 8:
                                customer_str = ' → '.join([f"C{c}" for c in customers])
                            else:
                                customer_str = f"{' → '.join([f'C{c}' for c in customers[:4]])} ... → {' → '.join([f'C{c}' for c in customers[-2:]])}"
                            
                            key_decisions[f"Route {i+1} (Vehicle {vehicle_id})"] = f"{len(customers)} stops: {customer_str} (Distance: {distance:.2f} km)"
                
                if len(routes) > 5:
                    key_decisions['additional_routes'] = f"Plus {len(routes) - 5} more routes covering remaining customers"
            else:
                key_decisions['Solution'] = "Optimal routing solution found (route details in optimization output)"
        
        elif domain_id in ['job_shop', 'job_shop_v1']:
            # Job Shop: Extract schedule
            schedule = best_sol.get('schedule', [])
            if schedule:
                key_decisions['production_schedule'] = f"Schedule {len(schedule)} operations across machines to minimize makespan"
                
                # Group by machine
                by_machine = {}
                for op in schedule:
                    if isinstance(op, dict):
                        machine = op.get('machine', 'Unknown')
                        if machine not in by_machine:
                            by_machine[machine] = []
                        by_machine[machine].append(op)
                
                for machine, ops in list(by_machine.items())[:5]:
                    job_sequence = ' → '.join([f"J{op.get('job', '?')}" for op in ops[:8]])
                    if len(ops) > 8:
                        job_sequence += f" ... ({len(ops)-8} more)"
                    key_decisions[f"Machine {machine}"] = f"Process {len(ops)} jobs: {job_sequence}"
            else:
                key_decisions['Solution'] = "Optimal production schedule found (details in optimization output)"
        
        elif domain_id in ['workforce', 'workforce_v1', 'workforce_rostering']:
            # Workforce: Extract shift assignments
            assignments = best_sol.get('assignments', [])
            if assignments:
                key_decisions['workforce_deployment'] = f"Assign {len(assignments)} shifts to workers efficiently"
                
                # Group by worker or shift
                by_worker = {}
                for assign in assignments:
                    if isinstance(assign, dict):
                        worker = assign.get('worker_id', assign.get('worker', 'Unknown'))
                        if worker not in by_worker:
                            by_worker[worker] = []
                        by_worker[worker].append(assign)
                
                for worker, shifts in list(by_worker.items())[:5]:
                    shift_list = ', '.join([f"Shift {s.get('shift_id', s.get('shift', '?'))}" for s in shifts[:5]])
                    if len(shifts) > 5:
                        shift_list += f" ... ({len(shifts)-5} more)"
                    key_decisions[f"Worker {worker}"] = f"{len(shifts)} shifts: {shift_list}"
            else:
                key_decisions['Solution'] = "Optimal workforce roster found (details in optimization output)"
        
        elif domain_id in ['retail_layout', 'retail_layout_v1']:
            # Retail Layout: Extract product placements
            assignments = best_sol.get('assignments', {})
            if assignments and isinstance(assignments, dict):
                key_decisions['store_layout'] = f"Optimize placement of {len(assignments)} products across shelves"
                
                # Group by shelf
                by_shelf = {}
                for product, shelf in assignments.items():
                    if shelf not in by_shelf:
                        by_shelf[shelf] = []
                    by_shelf[shelf].append(product)
                
                for shelf, products in list(by_shelf.items())[:5]:
                    product_list = ', '.join([str(p) for p in products[:6]])
                    if len(products) > 6:
                        product_list += f" ... ({len(products)-6} more)"
                    key_decisions[f"Shelf {shelf}"] = f"{len(products)} products: {product_list}"
            else:
                key_decisions['Solution'] = "Optimal store layout found (details in optimization output)"
        
        elif domain_id in ['promotion', 'promotion_v1', 'retail_promotion']:
            # Promotion: Extract schedule
            schedule = best_sol.get('schedule', [])
            if schedule:
                key_decisions['promotion_calendar'] = f"Schedule {len(schedule)} promotions over planning period"
                
                for i, promo in enumerate(schedule[:8]):
                    if isinstance(promo, dict):
                        product = promo.get('product', promo.get('product_id', f'Product {i+1}'))
                        week = promo.get('week', promo.get('start_week', '?'))
                        key_decisions[f"Promotion {i+1}"] = f"{product} in Week {week}"
            else:
                key_decisions['Solution'] = "Optimal promotion schedule found (details in optimization output)"
        
        elif domain_id in ['maintenance', 'maintenance_v1']:
            # Maintenance: Extract schedule
            schedule = best_sol.get('schedule', [])
            if schedule:
                key_decisions['maintenance_plan'] = f"Schedule {len(schedule)} maintenance tasks to minimize downtime"
                
                for i, task in enumerate(schedule[:8]):
                    if isinstance(task, dict):
                        asset = task.get('asset', task.get('asset_id', f'Asset {i+1}'))
                        week = task.get('week', task.get('scheduled_week', '?'))
                        key_decisions[f"Task {i+1}"] = f"Maintain {asset} in Week {week}"
            else:
                key_decisions['Solution'] = "Optimal maintenance schedule found (details in optimization output)"
        
        else:
            # Generic fallback
            key_decisions['Solution'] = "Optimal solution found (see technical details in structured results)"
        
        return key_decisions

