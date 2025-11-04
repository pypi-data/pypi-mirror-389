#!/usr/bin/env python3
"""
Universal LMEA (LLM-Enhanced Evolutionary Algorithm) Engine

A domain-agnostic evolutionary algorithm framework that can be configured
for any optimization problem via Supabase configurations.

Key Features:
- Domain-agnostic genetic operators (selection, crossover, mutation)
- Configurable multi-objective fitness functions
- Flexible constraint handling (hard/soft constraints)
- Integrated mathematical proof generation
- Evolution tracking for visualizations

Architecture:
1. **Fitness Evaluator**: Domain-specific fitness calculation (injected)
2. **Constraint Handler**: Validates and penalizes constraint violations
3. **Genetic Operators**: Selection, crossover, mutation (domain-agnostic)
4. **Proof Engine**: Universal mathematical validation

Design Pattern: Strategy Pattern + Dependency Injection
- Fitness evaluation strategy is injected per domain
- Core GA operations are universal
"""

import logging
import random
import copy
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class LMEAConfig:
    """Configuration for LMEA engine from Supabase"""
    population_size: int = 100
    max_generations: int = 150
    crossover_rate: float = 0.7
    mutation_rate: float = 0.2
    tournament_size: int = 5
    elite_size: int = 10
    convergence_threshold: int = 30  # Generations without improvement before stopping
    target_fitness: Optional[float] = None
    
    # Constraint penalties
    hard_constraint_penalty: float = 10000.0
    soft_constraint_penalty_base: float = 100.0


class UniversalLMEAEngine:
    """
    Universal Evolutionary Algorithm Engine
    
    This engine handles all domain-agnostic EA operations:
    - Population management
    - Selection (tournament selection)
    - Crossover (uniform, single-point, domain-specific)
    - Mutation (gaussian, swap, domain-specific)
    - Elitism
    - Convergence detection
    - Evolution tracking
    
    Domain-specific logic is injected via:
    - fitness_evaluator: Callable that computes fitness for a solution
    - constraint_checker: Callable that validates constraints
    - solution_initializer: Callable that creates random solutions
    - crossover_operator: Optional custom crossover logic
    - mutation_operator: Optional custom mutation logic
    """
    
    def __init__(self, config: LMEAConfig):
        self.config = config
        logger.info(f"🧬 Universal LMEA Engine initialized:")
        logger.info(f"   Population: {config.population_size}, Generations: {config.max_generations}")
        logger.info(f"   Crossover: {config.crossover_rate}, Mutation: {config.mutation_rate}")
        logger.info(f"   Tournament: {config.tournament_size}, Elite: {config.elite_size}")
    
    async def evolve(
        self,
        solution_initializer: Callable[[], Any],
        fitness_evaluator: Callable[[Any, Dict[str, Any]], float],
        constraint_checker: Optional[Callable[[Any, Dict[str, Any]], List[str]]] = None,
        crossover_operator: Optional[Callable[[Any, Any], Tuple[Any, Any]]] = None,
        mutation_operator: Optional[Callable[[Any], Any]] = None,
        problem_data: Optional[Dict[str, Any]] = None,
        early_stopping: bool = True
    ) -> Dict[str, Any]:
        """
        Run evolutionary algorithm to find optimal solution
        
        Args:
            solution_initializer: Function that generates random solution
            fitness_evaluator: Function(solution, problem_data) -> fitness_score
            constraint_checker: Function(solution, problem_data) -> List[violations]
            crossover_operator: Optional custom crossover logic
            mutation_operator: Optional custom mutation logic
            problem_data: Domain-specific problem data passed to evaluators
            early_stopping: Whether to stop early if no improvement
            
        Returns:
            {
                'best_solution': best_individual,
                'fitness': best_fitness,
                'generations_run': actual_generations,
                'evolution_history': [...],
                'convergence_reason': 'target_reached' | 'no_improvement' | 'max_generations'
            }
        """
        problem_data = problem_data or {}
        
        logger.info(f"🚀 Starting evolution...")
        start_time = datetime.now()
        
        # Initialize population
        logger.info(f"📦 Initializing population of {self.config.population_size}...")
        population = [solution_initializer() for _ in range(self.config.population_size)]
        
        # Evolution tracking
        evolution_history = []
        best_fitness = float('-inf')
        best_solution = None
        generations_without_improvement = 0
        convergence_reason = 'max_generations'
        
        # Main evolution loop
        for generation in range(self.config.max_generations):
            # Evaluate fitness for all individuals
            fitness_scores = []
            for individual in population:
                # Calculate base fitness
                base_fitness = fitness_evaluator(individual, problem_data)
                
                # Apply constraint penalties
                if constraint_checker:
                    violations = constraint_checker(individual, problem_data)
                    if violations:
                        # Penalize based on number and severity of violations
                        penalty = len(violations) * self.config.hard_constraint_penalty
                        fitness = base_fitness - penalty
                    else:
                        fitness = base_fitness
                else:
                    fitness = base_fitness
                
                fitness_scores.append(fitness)
            
            # Track current generation statistics
            current_best = max(fitness_scores)
            avg_fitness = sum(fitness_scores) / len(fitness_scores)
            worst_fitness = min(fitness_scores)
            
            # Calculate constraint satisfaction rate
            if constraint_checker:
                feasible_count = sum(
                    1 for ind in population 
                    if not constraint_checker(ind, problem_data)
                )
                constraint_satisfaction = feasible_count / len(population)
            else:
                constraint_satisfaction = 1.0
            
            # Record generation data
            evolution_history.append({
                'generation': generation + 1,
                'best_fitness': current_best,
                'avg_fitness': avg_fitness,
                'worst_fitness': worst_fitness,
                'constraint_satisfaction': constraint_satisfaction,
                'population_diversity': self._calculate_diversity(population)
            })
            
            # Update best solution
            if current_best > best_fitness:
                best_fitness = current_best
                best_solution = copy.deepcopy(population[fitness_scores.index(current_best)])
                generations_without_improvement = 0
                logger.info(f"✨ Gen {generation + 1:3d}: New best fitness = {best_fitness:.4f} (avg: {avg_fitness:.4f})")
            else:
                generations_without_improvement += 1
                if generation % 10 == 0:
                    logger.info(f"⏳ Gen {generation + 1:3d}: Best = {best_fitness:.4f}, Avg = {avg_fitness:.4f} (no improvement: {generations_without_improvement})")
            
            # Check stopping conditions
            if self.config.target_fitness and best_fitness >= self.config.target_fitness:
                logger.info(f"🎯 Target fitness {self.config.target_fitness} reached!")
                convergence_reason = 'target_reached'
                break
            
            if early_stopping and generations_without_improvement >= self.config.convergence_threshold:
                logger.info(f"⏸️  No improvement for {self.config.convergence_threshold} generations, stopping early")
                convergence_reason = 'no_improvement'
                break
            
            # Selection: Tournament selection with elitism
            elite = self._select_elite(population, fitness_scores)
            offspring = []
            
            # Generate offspring to fill population (minus elite)
            while len(offspring) < self.config.population_size - self.config.elite_size:
                # Select parents via tournament
                parent1 = self._tournament_selection(population, fitness_scores)
                parent2 = self._tournament_selection(population, fitness_scores)
                
                # Crossover
                if random.random() < self.config.crossover_rate:
                    if crossover_operator:
                        child1, child2 = crossover_operator(parent1, parent2)
                    else:
                        child1, child2 = self._default_crossover(parent1, parent2)
                else:
                    child1, child2 = copy.deepcopy(parent1), copy.deepcopy(parent2)
                
                # Mutation
                if random.random() < self.config.mutation_rate:
                    child1 = mutation_operator(child1) if mutation_operator else self._default_mutation(child1)
                if random.random() < self.config.mutation_rate:
                    child2 = mutation_operator(child2) if mutation_operator else self._default_mutation(child2)
                
                offspring.extend([child1, child2])
            
            # New population = elite + offspring
            population = elite + offspring[:self.config.population_size - self.config.elite_size]
        
        duration = (datetime.now() - start_time).total_seconds()
        actual_generations = len(evolution_history)
        
        logger.info(f"✅ Evolution complete: {actual_generations} generations in {duration:.2f}s")
        logger.info(f"   Best fitness: {best_fitness:.4f}")
        logger.info(f"   Convergence reason: {convergence_reason}")
        
        return {
            'best_solution': best_solution,
            'fitness': best_fitness,
            'generations_run': actual_generations,
            'evolution_history': evolution_history,
            'convergence_reason': convergence_reason,
            'duration_seconds': duration,
            'final_population': population,
            'final_fitness_scores': fitness_scores
        }
    
    def _select_elite(self, population: List[Any], fitness_scores: List[float]) -> List[Any]:
        """Select top N individuals as elite"""
        elite_indices = sorted(range(len(fitness_scores)), key=lambda i: fitness_scores[i], reverse=True)[:self.config.elite_size]
        return [copy.deepcopy(population[i]) for i in elite_indices]
    
    def _tournament_selection(self, population: List[Any], fitness_scores: List[float]) -> Any:
        """Tournament selection: pick best from random subset"""
        tournament_indices = random.sample(range(len(population)), self.config.tournament_size)
        best_idx = max(tournament_indices, key=lambda i: fitness_scores[i])
        return copy.deepcopy(population[best_idx])
    
    def _default_crossover(self, parent1: Any, parent2: Any) -> Tuple[Any, Any]:
        """
        Default uniform crossover for dict/list structures
        Override with custom crossover_operator if needed
        """
        child1 = copy.deepcopy(parent1)
        child2 = copy.deepcopy(parent2)
        
        # If solutions are dicts, swap random keys
        if isinstance(parent1, dict) and isinstance(parent2, dict):
            keys = list(parent1.keys())
            for key in keys:
                if random.random() < 0.5:
                    child1[key], child2[key] = parent2[key], parent1[key]
        
        # If solutions are lists, uniform crossover
        elif isinstance(parent1, list) and isinstance(parent2, list):
            for i in range(min(len(parent1), len(parent2))):
                if random.random() < 0.5:
                    child1[i], child2[i] = parent2[i], parent1[i]
        
        return child1, child2
    
    def _default_mutation(self, solution: Any) -> Any:
        """
        Default mutation for dict/list structures
        Override with custom mutation_operator if needed
        """
        mutated = copy.deepcopy(solution)
        
        # If solution is dict with numeric values, apply gaussian noise
        if isinstance(solution, dict):
            for key, value in mutated.items():
                if isinstance(value, (int, float)) and random.random() < 0.1:
                    mutated[key] = value * random.gauss(1.0, 0.1)
        
        # If solution is list, swap random elements
        elif isinstance(solution, list) and len(solution) > 1:
            if random.random() < 0.5:
                i, j = random.sample(range(len(solution)), 2)
                mutated[i], mutated[j] = mutated[j], mutated[i]
        
        return mutated
    
    def _calculate_diversity(self, population: List[Any]) -> float:
        """
        Calculate population diversity (0-1 scale)
        Higher diversity = more different solutions
        """
        if len(population) < 2:
            return 0.0
        
        # Simple diversity metric: compare random pairs
        sample_size = min(20, len(population))
        samples = random.sample(population, sample_size)
        
        differences = 0
        comparisons = 0
        
        for i in range(len(samples)):
            for j in range(i + 1, len(samples)):
                if samples[i] != samples[j]:
                    differences += 1
                comparisons += 1
        
        return differences / comparisons if comparisons > 0 else 0.0


# Helper function to create LMEA config from Supabase domain config
def create_lmea_config_from_domain(domain_config: Dict[str, Any]) -> LMEAConfig:
    """Convert Supabase domain_config to LMEAConfig"""
    ga_params = domain_config.get('ga_params', {})
    
    return LMEAConfig(
        population_size=ga_params.get('population_size', 100),
        max_generations=ga_params.get('max_generations', 150),
        crossover_rate=ga_params.get('crossover_rate', 0.7),
        mutation_rate=ga_params.get('mutation_rate', 0.2),
        tournament_size=ga_params.get('tournament_size', 5),
        elite_size=ga_params.get('elite_size', 10),
        convergence_threshold=ga_params.get('convergence_threshold', 30),
        target_fitness=ga_params.get('target_fitness', None),
        hard_constraint_penalty=ga_params.get('hard_constraint_penalty', 10000.0),
        soft_constraint_penalty_base=ga_params.get('soft_constraint_penalty_base', 100.0)
    )

