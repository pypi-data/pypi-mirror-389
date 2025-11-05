#!/usr/bin/env python3
"""
LLM-driven Evolutionary Algorithm (LMEA) Solver
Based on "Large Language Models as Evolutionary Optimizers" (Liu et al., 2023)

Zero-shot evolutionary search guided by LLMs for combinatorial optimization
"""

import logging
import json
import random
import copy
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
import os

logger = logging.getLogger(__name__)


@dataclass
class Solution:
    """Represents a solution in the population"""
    genes: List[Any]  # Solution representation (e.g., permutation for TSP)
    fitness: float  # Fitness value (lower is better for minimization)
    metadata: Dict[str, Any]  # Additional info
    
    def __repr__(self):
        return f"Solution(fitness={self.fitness:.2f}, genes={self.genes[:5]}...)"


class LMEASolver:
    """
    LLM-driven Evolutionary Algorithm for combinatorial optimization
    
    Key features:
    - Zero-shot: No training needed
    - Self-adaptive: Temperature control for exploration/exploitation
    - Reasoning-based: LLM explains its decisions
    """
    
    def __init__(self, model: str = "gpt-4-turbo-preview"):
        self.model = model
        self.openai_client = None
        self.anthropic_client = None
        self._initialize_clients()
        
        # LMEA parameters
        self.population_size = 10
        self.max_generations = 50
        self.initial_temperature = 1.0
        self.min_temperature = 0.1
        self.temperature_decay = 0.95
        
    def _initialize_clients(self):
        """Initialize LLM clients"""
        try:
            from openai import OpenAI
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
                logger.info("✅ OpenAI client initialized for LMEA")
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize OpenAI client: {e}")
        
        try:
            from anthropic import Anthropic
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if api_key:
                self.anthropic_client = Anthropic(api_key=api_key)
                logger.info("✅ Anthropic client initialized for LMEA")
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize Anthropic client: {e}")
    
    async def solve_tsp(
        self,
        cities: List[Tuple[float, float]],
        problem_description: str = "",
        max_generations: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Solve Traveling Salesman Problem using LMEA
        
        Args:
            cities: List of (x, y) coordinates
            problem_description: Natural language description of problem
            max_generations: Override default max generations
        
        Returns:
            Dict with best solution, fitness, and reasoning
        """
        try:
            logger.info(f"🧬 Starting LMEA for TSP with {len(cities)} cities")
            
            if max_generations:
                self.max_generations = max_generations
            
            # Initialize population
            population = self._initialize_tsp_population(cities)
            logger.info(f"📊 Initial population: {len(population)} solutions")
            
            # Track best solution
            best_solution = min(population, key=lambda s: s.fitness)
            best_fitness_history = [best_solution.fitness]
            
            # Evolutionary search with self-adaptive temperature
            temperature = self.initial_temperature
            
            for generation in range(self.max_generations):
                logger.info(f"\n🔄 Generation {generation + 1}/{self.max_generations}")
                logger.info(f"   Temperature: {temperature:.3f}")
                logger.info(f"   Best fitness: {best_solution.fitness:.2f}")
                
                # Step 1: LLM selects parents
                parents = await self._llm_select_parents(
                    population,
                    temperature,
                    cities,
                    problem_description
                )
                
                # Step 2: LLM performs crossover
                offspring = await self._llm_crossover_tsp(
                    parents,
                    temperature,
                    cities,
                    problem_description
                )
                
                # Step 3: LLM performs mutation
                offspring = await self._llm_mutate_tsp(
                    offspring,
                    temperature,
                    cities,
                    problem_description
                )
                
                # Step 4: Evaluate offspring
                for child in offspring:
                    child.fitness = self._evaluate_tsp_fitness(child.genes, cities)
                
                # Step 5: Update population (generational replacement)
                population = self._update_population(population, offspring)
                
                # Track best solution
                current_best = min(population, key=lambda s: s.fitness)
                if current_best.fitness < best_solution.fitness:
                    best_solution = current_best
                    logger.info(f"   ✨ New best solution found: {best_solution.fitness:.2f}")
                
                best_fitness_history.append(best_solution.fitness)
                
                # Step 6: Adapt temperature (self-adaptation)
                temperature = self._adapt_temperature(
                    temperature,
                    generation,
                    best_fitness_history
                )
                
                # Early stopping if no improvement
                if len(best_fitness_history) > 10:
                    recent_improvement = best_fitness_history[-10] - best_fitness_history[-1]
                    if recent_improvement < 0.01:
                        logger.info(f"   🛑 Early stopping: No significant improvement")
                        break
            
            logger.info(f"\n✅ LMEA completed")
            logger.info(f"   Final best fitness: {best_solution.fitness:.2f}")
            logger.info(f"   Improvement: {best_fitness_history[0] - best_solution.fitness:.2f}")
            
            return {
                'status': 'success',
                'best_solution': best_solution.genes,
                'best_fitness': best_solution.fitness,
                'fitness_history': best_fitness_history,
                'generations': len(best_fitness_history) - 1,
                'improvement': best_fitness_history[0] - best_solution.fitness,
                'metadata': best_solution.metadata
            }
            
        except Exception as e:
            logger.error(f"❌ LMEA failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _initialize_tsp_population(self, cities: List[Tuple[float, float]]) -> List[Solution]:
        """Initialize diverse population of TSP solutions"""
        population = []
        n = len(cities)
        
        for i in range(self.population_size):
            # Create random permutation
            tour = list(range(n))
            random.shuffle(tour)
            
            # Evaluate fitness
            fitness = self._evaluate_tsp_fitness(tour, cities)
            
            population.append(Solution(
                genes=tour,
                fitness=fitness,
                metadata={'generation': 0, 'method': 'random'}
            ))
        
        return population
    
    def _evaluate_tsp_fitness(self, tour: List[int], cities: List[Tuple[float, float]]) -> float:
        """Calculate total tour distance (fitness)"""
        total_distance = 0.0
        n = len(tour)
        
        for i in range(n):
            city1 = cities[tour[i]]
            city2 = cities[tour[(i + 1) % n]]
            
            # Euclidean distance
            dx = city1[0] - city2[0]
            dy = city1[1] - city2[1]
            distance = (dx**2 + dy**2)**0.5
            
            total_distance += distance
        
        return total_distance
    
    async def _llm_select_parents(
        self,
        population: List[Solution],
        temperature: float,
        cities: List[Tuple[float, float]],
        problem_description: str
    ) -> List[Solution]:
        """Use LLM to select promising parent solutions"""
        try:
            # Format population for LLM
            pop_summary = []
            for i, sol in enumerate(population[:5]):  # Show top 5 for efficiency
                pop_summary.append({
                    'id': i,
                    'fitness': round(sol.fitness, 2),
                    'tour_sample': sol.genes[:10]  # Show first 10 cities
                })
            
            prompt = f"""You are guiding an evolutionary algorithm for the Traveling Salesman Problem.

**Problem:** {problem_description or f'Find shortest tour visiting {len(cities)} cities'}

**Current Population (top 5 solutions):**
{json.dumps(pop_summary, indent=2)}

**Your Task:** Select 2 parent solutions for crossover.

**Guidelines:**
- Balance fitness (select good solutions) and diversity (explore different regions)
- Temperature = {temperature:.2f} (higher = more exploration, lower = more exploitation)
- Consider both solution quality and potential for improvement

**Response Format (JSON):**
{{
  "parent1_id": 0,
  "parent2_id": 1,
  "reasoning": "Explain why you selected these parents"
}}

Select parents that will produce promising offspring.
"""
            
            response = await self._call_llm(prompt, temperature)
            
            if response:
                p1_id = response.get('parent1_id', 0)
                p2_id = response.get('parent2_id', 1)
                
                # Ensure valid indices
                p1_id = max(0, min(p1_id, len(population) - 1))
                p2_id = max(0, min(p2_id, len(population) - 1))
                
                parents = [population[p1_id], population[p2_id]]
                logger.info(f"   👨‍👩‍👦 Selected parents: {p1_id} (fitness={parents[0].fitness:.2f}), {p2_id} (fitness={parents[1].fitness:.2f})")
                logger.info(f"   💭 Reasoning: {response.get('reasoning', 'N/A')[:100]}...")
                
                return parents
            else:
                # Fallback: tournament selection
                return random.sample(population, 2)
                
        except Exception as e:
            logger.warning(f"⚠️ LLM parent selection failed, using random: {e}")
            return random.sample(population, 2)
    
    async def _llm_crossover_tsp(
        self,
        parents: List[Solution],
        temperature: float,
        cities: List[Tuple[float, float]],
        problem_description: str
    ) -> List[Solution]:
        """Use LLM to perform intelligent crossover"""
        try:
            p1_tour = parents[0].genes
            p2_tour = parents[1].genes
            
            prompt = f"""You are performing crossover for a Traveling Salesman Problem.

**Parent 1 Tour:** {p1_tour[:15]}... (fitness: {parents[0].fitness:.2f})
**Parent 2 Tour:** {p2_tour[:15]}... (fitness: {parents[1].fitness:.2f})

**Your Task:** Create a new tour by combining the best features of both parents.

**Guidelines:**
- Maintain feasibility (visit each city exactly once)
- Preserve good sub-tours from parents
- Temperature = {temperature:.2f} (higher = more creative combinations)
- Consider which segments from each parent to keep

**Response Format (JSON):**
{{
  "offspring_tour": [0, 1, 2, ...],  // Complete tour visiting all cities
  "reasoning": "Explain how you combined the parents"
}}

Create an offspring that inherits the best qualities from both parents.
"""
            
            response = await self._call_llm(prompt, temperature)
            
            if response and 'offspring_tour' in response:
                offspring_tour = response['offspring_tour']
                
                # Validate and repair if needed
                offspring_tour = self._repair_tsp_tour(offspring_tour, len(cities))
                
                offspring = Solution(
                    genes=offspring_tour,
                    fitness=self._evaluate_tsp_fitness(offspring_tour, cities),
                    metadata={'method': 'llm_crossover', 'reasoning': response.get('reasoning', '')}
                )
                
                logger.info(f"   🧬 LLM crossover produced offspring with fitness: {offspring.fitness:.2f}")
                
                return [offspring]
            else:
                # Fallback: order crossover
                return [self._order_crossover(parents[0], parents[1], cities)]
                
        except Exception as e:
            logger.warning(f"⚠️ LLM crossover failed, using order crossover: {e}")
            return [self._order_crossover(parents[0], parents[1], cities)]
    
    async def _llm_mutate_tsp(
        self,
        offspring: List[Solution],
        temperature: float,
        cities: List[Tuple[float, float]],
        problem_description: str
    ) -> List[Solution]:
        """Use LLM to perform intelligent mutation"""
        mutated = []
        
        for child in offspring:
            try:
                prompt = f"""You are applying mutation to improve a TSP solution.

**Current Tour:** {child.genes[:15]}... (fitness: {child.fitness:.2f})
**Temperature:** {temperature:.2f} (higher = more exploration)

**Your Task:** Suggest a small modification to explore nearby solutions.

**Mutation Options:**
1. Swap two cities
2. Reverse a segment
3. Insert a city in a different position

**Response Format (JSON):**
{{
  "mutation_type": "swap|reverse|insert",
  "parameters": {{"city1": 0, "city2": 5}},  // Depends on mutation type
  "reasoning": "Why this mutation might improve the solution"
}}

Suggest a mutation that balances exploration and exploitation.
"""
                
                response = await self._call_llm(prompt, temperature)
                
                if response:
                    mutated_tour = self._apply_mutation(
                        child.genes,
                        response.get('mutation_type', 'swap'),
                        response.get('parameters', {})
                    )
                    
                    mutated_child = Solution(
                        genes=mutated_tour,
                        fitness=self._evaluate_tsp_fitness(mutated_tour, cities),
                        metadata={'method': 'llm_mutation', 'reasoning': response.get('reasoning', '')}
                    )
                    
                    logger.info(f"   🔀 LLM mutation: {response.get('mutation_type', 'N/A')}, fitness: {mutated_child.fitness:.2f}")
                    
                    mutated.append(mutated_child)
                else:
                    # Fallback: random swap
                    mutated.append(self._random_swap_mutation(child, cities))
                    
            except Exception as e:
                logger.warning(f"⚠️ LLM mutation failed, using random swap: {e}")
                mutated.append(self._random_swap_mutation(child, cities))
        
        return mutated
    
    def _repair_tsp_tour(self, tour: List[int], n_cities: int) -> List[int]:
        """Repair invalid TSP tour to visit each city exactly once"""
        if len(tour) != n_cities:
            tour = list(range(n_cities))
            random.shuffle(tour)
            return tour
        
        # Check for duplicates/missing cities
        seen = set()
        missing = set(range(n_cities))
        
        for city in tour:
            if city in seen or city >= n_cities:
                # Invalid
                tour = list(range(n_cities))
                random.shuffle(tour)
                return tour
            seen.add(city)
            missing.discard(city)
        
        if missing:
            # Missing cities, repair
            tour = list(range(n_cities))
            random.shuffle(tour)
        
        return tour
    
    def _order_crossover(
        self,
        parent1: Solution,
        parent2: Solution,
        cities: List[Tuple[float, float]]
    ) -> Solution:
        """Traditional order crossover operator"""
        n = len(parent1.genes)
        
        # Select crossover points
        p1, p2 = sorted(random.sample(range(n), 2))
        
        # Create offspring
        offspring = [-1] * n
        offspring[p1:p2] = parent1.genes[p1:p2]
        
        # Fill remaining from parent2
        pos = p2
        for city in parent2.genes:
            if city not in offspring:
                if pos >= n:
                    pos = 0
                offspring[pos] = city
                pos += 1
        
        return Solution(
            genes=offspring,
            fitness=self._evaluate_tsp_fitness(offspring, cities),
            metadata={'method': 'order_crossover'}
        )
    
    def _random_swap_mutation(
        self,
        solution: Solution,
        cities: List[Tuple[float, float]]
    ) -> Solution:
        """Traditional swap mutation"""
        mutated = solution.genes.copy()
        i, j = random.sample(range(len(mutated)), 2)
        mutated[i], mutated[j] = mutated[j], mutated[i]
        
        return Solution(
            genes=mutated,
            fitness=self._evaluate_tsp_fitness(mutated, cities),
            metadata={'method': 'swap_mutation'}
        )
    
    def _apply_mutation(
        self,
        tour: List[int],
        mutation_type: str,
        parameters: Dict[str, Any]
    ) -> List[int]:
        """Apply specified mutation"""
        mutated = tour.copy()
        n = len(mutated)
        
        if mutation_type == 'swap':
            i = parameters.get('city1', random.randint(0, n-1))
            j = parameters.get('city2', random.randint(0, n-1))
            mutated[i], mutated[j] = mutated[j], mutated[i]
        
        elif mutation_type == 'reverse':
            i = parameters.get('start', random.randint(0, n-2))
            j = parameters.get('end', random.randint(i+1, n-1))
            mutated[i:j+1] = reversed(mutated[i:j+1])
        
        elif mutation_type == 'insert':
            i = parameters.get('from', random.randint(0, n-1))
            j = parameters.get('to', random.randint(0, n-1))
            city = mutated.pop(i)
            mutated.insert(j, city)
        
        return mutated
    
    def _update_population(
        self,
        population: List[Solution],
        offspring: List[Solution]
    ) -> List[Solution]:
        """Update population with offspring (generational replacement)"""
        # Combine population and offspring
        combined = population + offspring
        
        # Sort by fitness
        combined.sort(key=lambda s: s.fitness)
        
        # Keep best solutions
        return combined[:self.population_size]
    
    def _adapt_temperature(
        self,
        current_temp: float,
        generation: int,
        fitness_history: List[float]
    ) -> float:
        """Self-adaptive temperature control"""
        # Check recent improvement
        if len(fitness_history) > 5:
            recent_improvement = fitness_history[-5] - fitness_history[-1]
            
            if recent_improvement < 0.01:
                # Stuck in local optimum, increase exploration
                new_temp = min(current_temp * 1.1, 1.0)
                logger.info(f"   🌡️ Increasing temperature to {new_temp:.3f} (stuck in local optimum)")
                return new_temp
        
        # Default: exponential decay
        new_temp = max(current_temp * self.temperature_decay, self.min_temperature)
        
        return new_temp
    
    async def _call_llm(self, prompt: str, temperature: float) -> Optional[Dict[str, Any]]:
        """Call LLM with prompt"""
        try:
            if self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert in evolutionary algorithms and combinatorial optimization."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=min(temperature, 1.0),
                    response_format={"type": "json_object"}
                )
                
                content = response.choices[0].message.content
                return json.loads(content)
            
            elif self.anthropic_client:
                response = self.anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=2048,
                    temperature=min(temperature, 1.0),
                    messages=[
                        {"role": "user", "content": prompt + "\n\nProvide your response as valid JSON."}
                    ]
                )
                
                content = response.content[0].text
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ LLM call failed: {e}")
            return None

