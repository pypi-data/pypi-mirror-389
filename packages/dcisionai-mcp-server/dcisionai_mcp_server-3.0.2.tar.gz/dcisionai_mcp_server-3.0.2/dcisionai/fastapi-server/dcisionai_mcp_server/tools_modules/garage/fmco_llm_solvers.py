"""
FMCO LLM-Based Solvers
Advanced prompting strategies for optimization problem solving
"""

import logging
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import openai
import anthropic
import os

logger = logging.getLogger(__name__)

class PromptingStrategy(Enum):
    """LLM prompting strategies for optimization"""
    ZERO_SHOT_COT = "zero_shot_cot"
    FEW_SHOT_COT = "few_shot_cot"
    SELF_CONSISTENCY = "self_consistency"
    TREE_OF_THOUGHTS = "tree_of_thoughts"
    REACT_REASONING = "react_reasoning"
    PROGRAM_SYNTHESIS = "program_synthesis"
    CONSTRAINT_SATISFACTION = "constraint_satisfaction"

class SolverType(Enum):
    """Types of LLM-based solvers"""
    DIRECT_OPTIMIZATION = "direct_optimization"
    CONSTRAINT_PROPAGATION = "constraint_propagation"
    HEURISTIC_GENERATION = "heuristic_generation"
    SOLUTION_REPAIR = "solution_repair"
    META_HEURISTIC = "meta_heuristic"

@dataclass
class LLMSolverConfig:
    """Configuration for LLM-based solver"""
    solver_type: SolverType
    prompting_strategy: PromptingStrategy
    model: str
    temperature: float
    max_tokens: int
    timeout: int
    parameters: Dict[str, Any]

@dataclass
class LLMSolution:
    """Solution from LLM-based solver"""
    objective_value: float
    solution: Dict[str, Any]
    reasoning: str
    confidence: float
    solve_time: float
    iterations: int
    status: str

class LLMSolver:
    """LLM-based optimization solver with advanced prompting"""
    
    def __init__(self):
        # Initialize LLM clients
        try:
            self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            logger.info("✅ OpenAI client initialized for LLM solver")
        except Exception as e:
            logger.error(f"❌ Failed to initialize OpenAI client: {e}")
            self.openai_client = None
        
        try:
            self.anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            logger.info("✅ Anthropic client initialized for LLM solver")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Anthropic client: {e}")
            self.anthropic_client = None
        
        # Initialize prompting strategies
        self.prompting_strategies = self._initialize_prompting_strategies()
    
    def _initialize_prompting_strategies(self) -> Dict[PromptingStrategy, Dict[str, Any]]:
        """Initialize prompting strategies"""
        return {
            PromptingStrategy.ZERO_SHOT_COT: {
                "description": "Zero-shot Chain-of-Thought reasoning",
                "template": self._get_zero_shot_cot_template(),
                "examples": []
            },
            PromptingStrategy.FEW_SHOT_COT: {
                "description": "Few-shot Chain-of-Thought with examples",
                "template": self._get_few_shot_cot_template(),
                "examples": self._get_optimization_examples()
            },
            PromptingStrategy.SELF_CONSISTENCY: {
                "description": "Self-consistency with multiple reasoning paths",
                "template": self._get_self_consistency_template(),
                "num_samples": 5
            },
            PromptingStrategy.TREE_OF_THOUGHTS: {
                "description": "Tree of thoughts exploration",
                "template": self._get_tree_of_thoughts_template(),
                "max_depth": 3,
                "branching_factor": 3
            },
            PromptingStrategy.REACT_REASONING: {
                "description": "ReAct (Reasoning + Acting) framework",
                "template": self._get_react_template(),
                "max_steps": 10
            },
            PromptingStrategy.PROGRAM_SYNTHESIS: {
                "description": "Generate optimization code",
                "template": self._get_program_synthesis_template(),
                "language": "python"
            },
            PromptingStrategy.CONSTRAINT_SATISFACTION: {
                "description": "Constraint satisfaction reasoning",
                "template": self._get_constraint_satisfaction_template(),
                "propagation_steps": 5
            }
        }
    
    def _get_zero_shot_cot_template(self) -> str:
        """Zero-shot Chain-of-Thought template"""
        return """
You are an expert optimization solver. Solve the following optimization problem step by step.

Problem: {problem_description}

Variables: {variables}
Constraints: {constraints}
Objective: {objective}

Please solve this step by step:

1. First, understand the problem structure and identify the key decision variables
2. Analyze the constraints and their relationships
3. Determine the objective function and what we're trying to optimize
4. Apply appropriate optimization techniques
5. Generate a feasible solution
6. Verify the solution satisfies all constraints
7. Calculate the objective value

Think through each step carefully and provide your reasoning.

Solution:
"""
    
    def _get_few_shot_cot_template(self) -> str:
        """Few-shot Chain-of-Thought template with examples"""
        return """
You are an expert optimization solver. Here are some examples of how to solve optimization problems:

{examples}

Now solve this problem:

Problem: {problem_description}
Variables: {variables}
Constraints: {constraints}
Objective: {objective}

Follow the same step-by-step approach as in the examples.

Solution:
"""
    
    def _get_self_consistency_template(self) -> str:
        """Self-consistency template"""
        return """
You are an expert optimization solver. Solve the following problem and provide multiple reasoning paths.

Problem: {problem_description}
Variables: {variables}
Constraints: {constraints}
Objective: {objective}

Please provide {num_samples} different approaches to solve this problem:

Approach 1:
[Detailed reasoning and solution]

Approach 2:
[Detailed reasoning and solution]

...

Approach {num_samples}:
[Detailed reasoning and solution]

Finally, synthesize the best solution from all approaches.
"""
    
    def _get_tree_of_thoughts_template(self) -> str:
        """Tree of thoughts template"""
        return """
You are an expert optimization solver. Explore multiple solution paths for this problem.

Problem: {problem_description}
Variables: {variables}
Constraints: {constraints}
Objective: {objective}

Think of this as exploring a tree of possible solutions:

Level 1 - Initial Approaches:
- Approach A: [reasoning]
- Approach B: [reasoning]
- Approach C: [reasoning]

Level 2 - Refined Approaches:
For each promising approach, explore refinements:
- A1: [detailed reasoning]
- A2: [detailed reasoning]
- B1: [detailed reasoning]
- etc.

Level 3 - Final Solutions:
Select the best refined approach and provide the complete solution.

Final Solution:
"""
    
    def _get_react_template(self) -> str:
        """ReAct template"""
        return """
You are an expert optimization solver using the ReAct (Reasoning + Acting) framework.

Problem: {problem_description}
Variables: {variables}
Constraints: {constraints}
Objective: {objective}

Use this format for each step:
Thought: [Your reasoning about what to do next]
Action: [The action you're taking]
Observation: [What you observe from the action]

Continue this process until you reach a solution.

Step 1:
Thought: [Initial analysis]
Action: [First action]
Observation: [Result]

Step 2:
Thought: [Next reasoning]
Action: [Next action]
Observation: [Result]

...

Final Solution:
"""
    
    def _get_program_synthesis_template(self) -> str:
        """Program synthesis template"""
        return """
You are an expert optimization programmer. Generate Python code to solve this optimization problem.

Problem: {problem_description}
Variables: {variables}
Constraints: {constraints}
Objective: {objective}

Generate a complete Python program that:
1. Defines the optimization problem
2. Sets up variables and constraints
3. Solves the problem using appropriate methods
4. Returns the optimal solution

Code:
```python
# Optimization Problem Solver
import numpy as np
from scipy.optimize import minimize
# ... your code here
```
"""
    
    def _get_constraint_satisfaction_template(self) -> str:
        """Constraint satisfaction template"""
        return """
You are an expert constraint satisfaction solver. Solve this optimization problem by propagating constraints.

Problem: {problem_description}
Variables: {variables}
Constraints: {constraints}
Objective: {objective}

Use constraint propagation to solve this step by step:

Step 1 - Initial Domain Analysis:
[Analyze variable domains and initial constraints]

Step 2 - Constraint Propagation:
[Apply constraint propagation rules]

Step 3 - Domain Reduction:
[Reduce variable domains based on constraints]

Step 4 - Backtracking Search:
[Use backtracking if needed]

Step 5 - Solution Verification:
[Verify the final solution]

Final Solution:
"""
    
    def _get_optimization_examples(self) -> List[Dict[str, Any]]:
        """Get optimization examples for few-shot learning"""
        return [
            {
                "problem": "Maximize 3x + 2y subject to x + y ≤ 4, x ≥ 0, y ≥ 0",
                "solution": "x = 4, y = 0, objective = 12",
                "reasoning": "This is a linear programming problem. The feasible region is bounded by the constraint x + y ≤ 4 and non-negativity constraints. The optimal solution occurs at the corner point (4,0) where the objective function 3x + 2y reaches its maximum value of 12."
            },
            {
                "problem": "Minimize x² + y² subject to x + y = 1",
                "solution": "x = 0.5, y = 0.5, objective = 0.5",
                "reasoning": "This is a constrained optimization problem. Using Lagrange multipliers, we set up L = x² + y² + λ(x + y - 1). Taking partial derivatives and solving gives x = y = 0.5, which minimizes the objective function."
            }
        ]
    
    async def solve_with_llm(
        self,
        problem_description: str,
        variables: List[Dict[str, Any]],
        constraints: List[Dict[str, Any]],
        objective: Dict[str, Any],
        config: LLMSolverConfig
    ) -> LLMSolution:
        """Solve optimization problem using LLM with specified strategy"""
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            logger.info(f"🧠 Solving with LLM using {config.prompting_strategy.value}")
            
            # Get prompting strategy
            strategy = self.prompting_strategies[config.prompting_strategy]
            
            # Generate prompt based on strategy
            prompt = self._generate_prompt(
                problem_description, variables, constraints, objective, strategy, config
            )
            
            # Call LLM
            response = await self._call_llm(prompt, config)
            
            # Parse response
            solution = self._parse_llm_response(response, config.prompting_strategy)
            
            solve_time = asyncio.get_event_loop().time() - start_time
            
            result = LLMSolution(
                objective_value=solution.get("objective_value", 0.0),
                solution=solution.get("solution", {}),
                reasoning=solution.get("reasoning", ""),
                confidence=solution.get("confidence", 0.5),
                solve_time=solve_time,
                iterations=solution.get("iterations", 1),
                status="optimal" if solution.get("confidence", 0) > 0.8 else "feasible"
            )
            
            logger.info(f"✅ LLM solver completed: {result.objective_value:.2f} (confidence: {result.confidence:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"❌ LLM solver failed: {e}")
            solve_time = asyncio.get_event_loop().time() - start_time
            
            return LLMSolution(
                objective_value=float('inf'),
                solution={},
                reasoning=f"Error: {str(e)}",
                confidence=0.0,
                solve_time=solve_time,
                iterations=0,
                status="failed"
            )
    
    def _generate_prompt(
        self,
        problem_description: str,
        variables: List[Dict[str, Any]],
        constraints: List[Dict[str, Any]],
        objective: Dict[str, Any],
        strategy: Dict[str, Any],
        config: LLMSolverConfig
    ) -> str:
        """Generate prompt based on strategy"""
        
        template = strategy["template"]
        
        # Format variables, constraints, and objective
        variables_str = "\n".join([f"- {var['name']}: {var['description']}" for var in variables])
        constraints_str = "\n".join([f"- {const['name']}: {const['expression']}" for const in constraints])
        objective_str = f"{objective['type']} {objective['expression']}"
        
        # Format examples if using few-shot
        examples_str = ""
        if config.prompting_strategy == PromptingStrategy.FEW_SHOT_COT:
            examples = strategy["examples"]
            examples_str = "\n\n".join([
                f"Example {i+1}:\nProblem: {ex['problem']}\nSolution: {ex['solution']}\nReasoning: {ex['reasoning']}"
                for i, ex in enumerate(examples)
            ])
        
        # Format prompt
        prompt = template.format(
            problem_description=problem_description,
            variables=variables_str,
            constraints=constraints_str,
            objective=objective_str,
            examples=examples_str,
            num_samples=strategy.get("num_samples", 3),
            num_steps=strategy.get("max_steps", 5)
        )
        
        return prompt
    
    async def _call_llm(self, prompt: str, config: LLMSolverConfig) -> str:
        """Call LLM with the generated prompt"""
        
        if config.model.startswith("gpt") and self.openai_client:
            response = self.openai_client.chat.completions.create(
                model=config.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=config.temperature,
                max_tokens=config.max_tokens
            )
            return response.choices[0].message.content
        
        elif config.model.startswith("claude") and self.anthropic_client:
            response = self.anthropic_client.messages.create(
                model=config.model,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        
        else:
            raise ValueError(f"Unsupported model: {config.model}")
    
    def _parse_llm_response(self, response: str, strategy: PromptingStrategy) -> Dict[str, Any]:
        """Parse LLM response based on strategy"""
        
        # Basic parsing - extract objective value and solution
        import re
        
        # Try to extract objective value
        objective_match = re.search(r'objective[:\s]*([0-9.-]+)', response.lower())
        objective_value = float(objective_match.group(1)) if objective_match else 0.0
        
        # Try to extract solution variables
        solution = {}
        var_pattern = r'(\w+)\s*[=:]\s*([0-9.-]+)'
        matches = re.findall(var_pattern, response)
        for var_name, var_value in matches:
            solution[var_name] = float(var_value)
        
        # Estimate confidence based on response quality
        confidence = self._estimate_confidence(response, strategy)
        
        return {
            "objective_value": objective_value,
            "solution": solution,
            "reasoning": response,
            "confidence": confidence,
            "iterations": 1
        }
    
    def _estimate_confidence(self, response: str, strategy: PromptingStrategy) -> float:
        """Estimate confidence in LLM response"""
        
        confidence = 0.5  # Base confidence
        
        # Check for mathematical expressions
        if re.search(r'[0-9]+\.[0-9]+', response):
            confidence += 0.1
        
        # Check for step-by-step reasoning
        if re.search(r'step\s*[0-9]+', response.lower()):
            confidence += 0.1
        
        # Check for constraint verification
        if 'constraint' in response.lower() and 'satisfied' in response.lower():
            confidence += 0.1
        
        # Check for objective calculation
        if 'objective' in response.lower() and '=' in response:
            confidence += 0.1
        
        # Strategy-specific confidence adjustments
        if strategy == PromptingStrategy.SELF_CONSISTENCY:
            if 'synthesize' in response.lower() or 'consensus' in response.lower():
                confidence += 0.1
        
        if strategy == PromptingStrategy.TREE_OF_THOUGHTS:
            if 'level' in response.lower() and 'final' in response.lower():
                confidence += 0.1
        
        return min(confidence, 1.0)
    
    def get_solver_configs(self) -> Dict[str, LLMSolverConfig]:
        """Get predefined solver configurations"""
        
        return {
            "gpt4_cot": LLMSolverConfig(
                solver_type=SolverType.DIRECT_OPTIMIZATION,
                prompting_strategy=PromptingStrategy.ZERO_SHOT_COT,
                model="gpt-4",
                temperature=0.3,
                max_tokens=2000,
                timeout=60,
                parameters={"reasoning_depth": "detailed"}
            ),
            "claude_self_consistency": LLMSolverConfig(
                solver_type=SolverType.DIRECT_OPTIMIZATION,
                prompting_strategy=PromptingStrategy.SELF_CONSISTENCY,
                model="claude-3-sonnet-20240229",
                temperature=0.7,
                max_tokens=3000,
                timeout=120,
                parameters={"num_samples": 5}
            ),
            "gpt4_tree_of_thoughts": LLMSolverConfig(
                solver_type=SolverType.META_HEURISTIC,
                prompting_strategy=PromptingStrategy.TREE_OF_THOUGHTS,
                model="gpt-4",
                temperature=0.5,
                max_tokens=4000,
                timeout=180,
                parameters={"max_depth": 3, "branching_factor": 3}
            ),
            "claude_react": LLMSolverConfig(
                solver_type=SolverType.HEURISTIC_GENERATION,
                prompting_strategy=PromptingStrategy.REACT_REASONING,
                model="claude-3-haiku-20240307",
                temperature=0.4,
                max_tokens=2500,
                timeout=90,
                parameters={"max_steps": 10}
            ),
            "gpt4_program_synthesis": LLMSolverConfig(
                solver_type=SolverType.HEURISTIC_GENERATION,
                prompting_strategy=PromptingStrategy.PROGRAM_SYNTHESIS,
                model="gpt-4",
                temperature=0.2,
                max_tokens=3000,
                timeout=120,
                parameters={"language": "python", "framework": "scipy"}
            )
        }
