#!/usr/bin/env python3
"""
LLM-Guided Model Reformulator
Uses LLM reasoning to reformulate infeasible or problematic optimization models
"""

import logging
import json
from typing import Any, Dict, Optional
import os

logger = logging.getLogger(__name__)


class LLMReformulator:
    """Use LLM to automatically reformulate problematic models"""
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize LLM clients"""
        try:
            from openai import OpenAI
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
                logger.info("✅ OpenAI client initialized for reformulation")
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize OpenAI client: {e}")
        
        try:
            from anthropic import Anthropic
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if api_key:
                self.anthropic_client = Anthropic(api_key=api_key)
                logger.info("✅ Anthropic client initialized for reformulation")
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize Anthropic client: {e}")
    
    async def reformulate_infeasible_model(
        self,
        model_data: Dict[str, Any],
        diagnostics: Any,  # ValidationResult
        problem_description: str,
        solver_feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reformulate infeasible model using LLM reasoning
        
        Steps:
        1. Analyze constraint conflicts
        2. Identify root causes of infeasibility
        3. Suggest relaxations or modifications
        4. Generate reformulated model
        """
        try:
            logger.info("🔄 Starting LLM-guided model reformulation...")
            
            # Build reformulation prompt
            prompt = self._build_reformulation_prompt(
                model_data,
                diagnostics,
                problem_description,
                solver_feedback
            )
            
            # Get LLM suggestions
            llm_response = await self._call_llm(prompt)
            
            if not llm_response:
                logger.error("❌ LLM did not provide reformulation suggestions")
                return {
                    'status': 'error',
                    'message': 'LLM reformulation failed',
                    'original_model': model_data
                }
            
            # Parse LLM response
            reformulated_model = self._parse_reformulation_response(
                llm_response,
                model_data
            )
            
            logger.info("✅ Model reformulation completed")
            
            return {
                'status': 'success',
                'reformulated_model': reformulated_model,
                'original_model': model_data,
                'reasoning': llm_response.get('reasoning', ''),
                'changes_made': llm_response.get('changes', []),
                'confidence': llm_response.get('confidence', 0.7)
            }
            
        except Exception as e:
            logger.error(f"❌ Model reformulation failed: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'original_model': model_data
            }
    
    def _build_reformulation_prompt(
        self,
        model_data: Dict[str, Any],
        diagnostics: Any,
        problem_description: str,
        solver_feedback: Optional[str]
    ) -> str:
        """Build comprehensive reformulation prompt"""
        
        # Extract model components
        variables = model_data.get('variables', [])
        constraints = model_data.get('constraints', [])
        objective = model_data.get('objective', {})
        
        # Format variables
        vars_str = self._format_variables(variables)
        
        # Format constraints
        constraints_str = self._format_constraints(constraints)
        
        # Format objective
        obj_str = f"{objective.get('type', 'minimize')} {objective.get('expression', 'N/A')}"
        
        # Format diagnostics
        diag_str = ""
        if diagnostics:
            if hasattr(diagnostics, 'errors'):
                diag_str += f"\nErrors: {diagnostics.errors}"
            if hasattr(diagnostics, 'warnings'):
                diag_str += f"\nWarnings: {diagnostics.warnings}"
            if hasattr(diagnostics, 'suggestions'):
                diag_str += f"\nSuggestions: {diagnostics.suggestions}"
        
        prompt = f"""You are an expert optimization consultant. An optimization model has failed to solve and needs reformulation.

**Business Problem:**
{problem_description}

**Current Model:**

Variables:
{vars_str}

Constraints:
{constraints_str}

Objective:
{obj_str}

**Diagnostics:**
{diag_str}

**Solver Feedback:**
{solver_feedback or 'Model is infeasible - no feasible solution exists'}

**Your Task:**
Analyze this model and suggest how to reformulate it to make it solvable while maintaining business intent.

Consider:
1. Are there conflicting constraints that can be relaxed?
2. Should we add slack variables to make constraints "soft"?
3. Are bounds too restrictive?
4. Are there missing constraints that would help?
5. Can we reformulate constraints to be more flexible?

**Response Format (JSON):**
{{
  "reasoning": "Detailed explanation of the issues and your solution approach",
  "root_cause": "Primary reason for infeasibility",
  "suggested_changes": [
    {{
      "type": "relax_constraint|add_slack|adjust_bounds|add_constraint",
      "target": "constraint_name or variable_name",
      "modification": "Specific change to make",
      "business_justification": "Why this change is acceptable"
    }}
  ],
  "reformulated_model": {{
    "variables": [...],  // Updated variable definitions
    "constraints": [...],  // Updated constraints
    "objective": {{...}}  // Updated objective if needed
  }},
  "confidence": 0.8,  // Confidence in this reformulation (0-1)
  "potential_issues": ["Any potential issues with this reformulation"]
}}

Focus on practical, business-acceptable changes that resolve infeasibility while staying true to the original intent.
"""
        
        return prompt
    
    def _format_variables(self, variables) -> str:
        """Format variables for prompt"""
        if isinstance(variables, dict):
            lines = []
            for name, data in variables.items():
                vtype = data.get('type', 'continuous')
                bounds = data.get('bounds', 'unbounded')
                desc = data.get('description', '')
                lines.append(f"  - {name}: {vtype}, bounds={bounds}, {desc}")
            return "\n".join(lines)
        elif isinstance(variables, list):
            lines = []
            for var in variables:
                if isinstance(var, dict):
                    name = var.get('name', 'unnamed')
                    vtype = var.get('type', 'continuous')
                    bounds = var.get('bounds', 'unbounded')
                    desc = var.get('description', '')
                    lines.append(f"  - {name}: {vtype}, bounds={bounds}, {desc}")
            return "\n".join(lines)
        return str(variables)
    
    def _format_constraints(self, constraints) -> str:
        """Format constraints for prompt"""
        if isinstance(constraints, dict):
            lines = []
            for name, data in constraints.items():
                expr = data.get('expression', '')
                desc = data.get('description', '')
                lines.append(f"  - {name}: {expr}  // {desc}")
            return "\n".join(lines)
        elif isinstance(constraints, list):
            lines = []
            for i, const in enumerate(constraints):
                if isinstance(const, dict):
                    name = const.get('name', f'c{i}')
                    expr = const.get('expression', '')
                    desc = const.get('description', '')
                    lines.append(f"  - {name}: {expr}  // {desc}")
            return "\n".join(lines)
        return str(constraints)
    
    async def _call_llm(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Call LLM with reformulation prompt"""
        try:
            # Try OpenAI first (GPT-4)
            if self.openai_client:
                logger.info("🤖 Calling GPT-4 for model reformulation...")
                response = self.openai_client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {"role": "system", "content": "You are an expert optimization consultant specializing in mathematical programming and model reformulation."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,  # Lower temperature for more reliable output
                    response_format={"type": "json_object"}
                )
                
                content = response.choices[0].message.content
                logger.info(f"✅ Received reformulation from GPT-4: {len(content)} chars")
                
                # Parse JSON response
                return json.loads(content)
            
            # Try Anthropic (Claude) as fallback
            elif self.anthropic_client:
                logger.info("🤖 Calling Claude for model reformulation...")
                response = self.anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=4096,
                    temperature=0.3,
                    messages=[
                        {"role": "user", "content": prompt + "\n\nProvide your response as valid JSON."}
                    ]
                )
                
                content = response.content[0].text
                logger.info(f"✅ Received reformulation from Claude: {len(content)} chars")
                
                # Extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    logger.error("Could not extract JSON from Claude response")
                    return None
            
            else:
                logger.error("❌ No LLM client available for reformulation")
                return None
                
        except Exception as e:
            logger.error(f"❌ LLM call failed: {e}")
            return None
    
    def _parse_reformulation_response(
        self,
        llm_response: Dict[str, Any],
        original_model: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse and validate LLM reformulation response"""
        try:
            # Extract reformulated model
            reformulated = llm_response.get('reformulated_model', {})
            
            if not reformulated:
                logger.warning("⚠️ LLM did not provide reformulated model, using original")
                return original_model
            
            # Validate reformulated model has required components
            if 'variables' not in reformulated:
                reformulated['variables'] = original_model.get('variables', [])
            
            if 'constraints' not in reformulated:
                reformulated['constraints'] = original_model.get('constraints', [])
            
            if 'objective' not in reformulated:
                reformulated['objective'] = original_model.get('objective', {})
            
            # Add metadata about reformulation
            reformulated['reformulation_metadata'] = {
                'reasoning': llm_response.get('reasoning', ''),
                'root_cause': llm_response.get('root_cause', 'Unknown'),
                'changes': llm_response.get('suggested_changes', []),
                'confidence': llm_response.get('confidence', 0.5),
                'potential_issues': llm_response.get('potential_issues', [])
            }
            
            logger.info(f"📋 Reformulation confidence: {reformulated['reformulation_metadata']['confidence']}")
            
            return reformulated
            
        except Exception as e:
            logger.error(f"❌ Failed to parse reformulation response: {e}")
            return original_model

