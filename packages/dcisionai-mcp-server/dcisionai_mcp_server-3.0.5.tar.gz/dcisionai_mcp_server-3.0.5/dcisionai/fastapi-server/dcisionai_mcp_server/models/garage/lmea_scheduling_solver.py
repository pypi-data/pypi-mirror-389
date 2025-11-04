#!/usr/bin/env python3
"""
LMEA Scheduling Solver
Handles job shop scheduling, workforce rostering, and maintenance scheduling
using LLM-driven Evolutionary Algorithm
"""

import logging
import random
import copy
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .lmea_solver import LMEASolver, Solution
from .universal_proof_engine import UniversalProofEngine

logger = logging.getLogger(__name__)


class SchedulingType(Enum):
    """Types of scheduling problems"""
    JOB_SHOP = "job_shop_scheduling"
    WORKFORCE_ROSTERING = "workforce_rostering"
    MAINTENANCE = "maintenance_scheduling"


@dataclass
class Job:
    """Job to be scheduled"""
    id: int
    name: str
    operations: List[Tuple[int, float]]  # [(machine_id, duration), ...]
    due_date: Optional[float] = None
    priority: int = 1
    release_time: float = 0.0


@dataclass
class Machine:
    """Machine/Resource for job processing"""
    id: int
    name: str
    capabilities: List[str]
    availability_start: float = 0.0
    availability_end: float = float('inf')


@dataclass
class Operation:
    """Single operation in a job"""
    job_id: int
    operation_id: int
    machine_id: int
    duration: float
    start_time: float = 0.0
    end_time: float = 0.0


@dataclass
class Schedule:
    """Complete schedule solution"""
    operations: List[Operation]
    makespan: float
    total_tardiness: float
    machine_utilization: Dict[int, float]
    is_feasible: bool
    violations: List[str]


class LMEASchedulingSolver(LMEASolver):
    """
    LMEA-based solver for scheduling problems
    
    Supports:
    - Job Shop Scheduling (JSS)
    - Workforce Rostering
    - Maintenance Scheduling
    """
    
    def __init__(self):
        super().__init__()
        
        
        # Mathematical proof engine (NO LIES!)
        self.proof_engine = UniversalProofEngine()
        # Scheduling-specific parameters
        self.population_size = 30
        self.max_generations = 100
    
    async def solve_job_shop(
        self,
        jobs: List[Job],
        machines: List[Machine],
        problem_description: str = "",
        max_generations: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Solve Job Shop Scheduling Problem (JSS)
        
        Args:
            jobs: List of Job objects with operations
            machines: List of Machine objects
            problem_description: Natural language description
            max_generations: Override default max generations
        
        Returns:
            Dict with best schedule, makespan, and metrics
        """
        try:
            logger.info(f"🏭 Starting LMEA for Job Shop Scheduling")
            logger.info(f"   Jobs: {len(jobs)}")
            logger.info(f"   Machines: {len(machines)}")
            
            if max_generations:
                self.max_generations = max_generations
            
            # Initialize population
            population = self._initialize_jss_population(jobs, machines)
            logger.info(f"📊 Initial population: {len(population)} schedules")
            
            # Track best solution
            best_solution = min(population, key=lambda s: s.fitness)
            fitness_history = [best_solution.fitness]
            
            logger.info(f"🎯 Initial best makespan: {best_solution.fitness:.2f}")
            
            # Evolutionary loop
            temperature = self.initial_temperature
            
            for generation in range(self.max_generations):
                # Selection
                parents = self._select_parents(population, temperature)
                
                # Crossover (JSS-specific)
                offspring = self._jss_crossover(parents, jobs, machines)
                
                # Mutation (JSS-specific)
                offspring = self._jss_mutation(offspring, jobs, machines, temperature)
                
                # Evaluate
                for sol in offspring:
                    sol.fitness = self._evaluate_jss_solution(sol, jobs, machines)
                
                # Update population
                population = self._update_population(population + offspring, self.population_size)
                
                # Track best
                current_best = min(population, key=lambda s: s.fitness)
                if current_best.fitness < best_solution.fitness:
                    best_solution = current_best
                    logger.info(f"   Gen {generation}: New best! Makespan: {current_best.fitness:.2f}")
                
                fitness_history.append(current_best.fitness)
                
                # Temperature decay
                temperature = max(self.min_temperature, temperature * self.temperature_decay)
            
            # Decode best solution
            schedule = self._decode_jss_solution(best_solution, jobs, machines)
            
            logger.info(f"✅ LMEA JSS complete!")
            logger.info(f"   Makespan: {schedule.makespan:.2f}")
            logger.info(f"   Feasible: {schedule.is_feasible}")
            
            # Calculate improvement
            initial_fitness = fitness_history[0]
            final_fitness = fitness_history[-1]
            improvement = initial_fitness - final_fitness
            
            return {
                "status": "success",
                "solver_choice": "lmea_scheduling",
                "scheduling_type": "job_shop",
                "makespan": schedule.makespan,
                "total_tardiness": schedule.total_tardiness,
                "machine_utilization": schedule.machine_utilization,
                "is_feasible": schedule.is_feasible,
                "violations": schedule.violations,
                "operations": [
                    {
                        "job_id": op.job_id,
                        "operation_id": op.operation_id,
                        "machine_id": op.machine_id,
                        "start_time": op.start_time,
                        "end_time": op.end_time,
                        "duration": op.duration
                    }
                    for op in schedule.operations
                ],
                "generations": self.max_generations,
                "improvement": improvement,
                "fitness_history": fitness_history,
                "solve_time": 0.0
            }
            
        except Exception as e:
            logger.error(f"❌ LMEA JSS solver failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "solver_choice": "lmea_scheduling",
                "scheduling_type": "job_shop"
            }
    
    def _initialize_jss_population(
        self,
        jobs: List[Job],
        machines: List[Machine]
    ) -> List[Solution]:
        """Initialize population for Job Shop Scheduling"""
        population = []
        
        for _ in range(self.population_size):
            # Create a random job sequence
            # Each gene is a priority-ordered list of job IDs
            job_sequence = []
            for job in jobs:
                for op_idx in range(len(job.operations)):
                    job_sequence.append((job.id, op_idx))
            
            # Shuffle for randomness
            random.shuffle(job_sequence)
            
            sol = Solution(
                genes=job_sequence,
                fitness=float('inf'),
                metadata={"type": "job_shop"}
            )
            
            # Evaluate
            sol.fitness = self._evaluate_jss_solution(sol, jobs, machines)
            
            population.append(sol)
        
        return population
    
    def _evaluate_jss_solution(
        self,
        solution: Solution,
        jobs: List[Job],
        machines: List[Machine]
    ) -> float:
        """
        Evaluate Job Shop Schedule fitness
        
        Fitness = makespan + tardiness_penalty
        """
        job_dict = {j.id: j for j in jobs}
        machine_dict = {m.id: m for m in machines}
        
        # Track machine availability and job progress
        machine_available = {m.id: 0.0 for m in machines}
        job_progress = {j.id: 0 for j in jobs}  # Next operation index
        job_completion = {j.id: 0.0 for j in jobs}
        
        # Schedule operations in sequence
        for (job_id, op_idx) in solution.genes:
            job = job_dict[job_id]
            
            # Skip if operation already scheduled
            if op_idx != job_progress[job_id]:
                continue
            
            # Get operation details
            if op_idx >= len(job.operations):
                continue
            
            machine_id, duration = job.operations[op_idx]
            
            # Check if machine exists
            if machine_id not in machine_dict:
                continue
            
            # Calculate start time (max of machine available and job completion)
            start_time = max(
                machine_available[machine_id],
                job_completion[job_id],
                job.release_time
            )
            
            end_time = start_time + duration
            
            # Update tracking
            machine_available[machine_id] = end_time
            job_completion[job_id] = end_time
            job_progress[job_id] = op_idx + 1
        
        # Calculate makespan (max completion time)
        makespan = max(job_completion.values()) if job_completion else 0.0
        
        # Calculate tardiness penalty
        tardiness_penalty = 0.0
        for job in jobs:
            if job.due_date and job_completion[job.id] > job.due_date:
                tardiness = job_completion[job.id] - job.due_date
                tardiness_penalty += tardiness * job.priority * 10.0  # Heavy penalty
        
        # Fitness = makespan + penalties
        fitness = makespan + tardiness_penalty
        
        return fitness
    
    def _jss_crossover(
        self,
        parents: List[Solution],
        jobs: List[Job],
        machines: List[Machine]
    ) -> List[Solution]:
        """Job Shop Scheduling crossover (Precedence Preserving Crossover)"""
        offspring = []
        
        for i in range(0, len(parents) - 1, 2):
            parent1 = parents[i]
            parent2 = parents[i + 1]
            
            # Precedence Preserving Crossover (PPX)
            child_genes = []
            p1_genes = list(parent1.genes)
            p2_genes = list(parent2.genes)
            
            while p1_genes or p2_genes:
                if random.random() < 0.5 and p1_genes:
                    child_genes.append(p1_genes.pop(0))
                elif p2_genes:
                    child_genes.append(p2_genes.pop(0))
                elif p1_genes:
                    child_genes.append(p1_genes.pop(0))
            
            child = Solution(
                genes=child_genes,
                fitness=float('inf'),
                metadata={"type": "job_shop"}
            )
            
            offspring.append(child)
        
        return offspring
    
    def _jss_mutation(
        self,
        population: List[Solution],
        jobs: List[Job],
        machines: List[Machine],
        temperature: float
    ) -> List[Solution]:
        """Job Shop Scheduling mutation operators"""
        mutated = []
        
        for sol in population:
            if random.random() < temperature:
                # Choose mutation type
                mutation_type = random.randint(0, 2)
                
                new_genes = list(sol.genes)
                
                if mutation_type == 0:
                    # Swap two random operations
                    if len(new_genes) >= 2:
                        i, j = random.sample(range(len(new_genes)), 2)
                        new_genes[i], new_genes[j] = new_genes[j], new_genes[i]
                
                elif mutation_type == 1:
                    # Move operation to different position
                    if len(new_genes) >= 2:
                        i = random.randint(0, len(new_genes) - 1)
                        j = random.randint(0, len(new_genes) - 1)
                        op = new_genes.pop(i)
                        new_genes.insert(j, op)
                
                else:
                    # Reverse subsequence
                    if len(new_genes) >= 2:
                        i = random.randint(0, len(new_genes) - 2)
                        j = random.randint(i + 1, len(new_genes))
                        new_genes[i:j] = reversed(new_genes[i:j])
                
                mutated_sol = Solution(
                    genes=new_genes,
                    fitness=float('inf'),
                    metadata={"type": "job_shop"}
                )
                
                mutated.append(mutated_sol)
            else:
                mutated.append(sol)
        
        return mutated
    
    def _decode_jss_solution(
        self,
        solution: Solution,
        jobs: List[Job],
        machines: List[Machine]
    ) -> Schedule:
        """Convert Solution to Schedule with full details"""
        job_dict = {j.id: j for j in jobs}
        machine_dict = {m.id: m for m in machines}
        
        # Track machine availability and job progress
        machine_available = {m.id: 0.0 for m in machines}
        machine_total_time = {m.id: 0.0 for m in machines}
        job_progress = {j.id: 0 for j in jobs}
        job_completion = {j.id: 0.0 for j in jobs}
        
        operations = []
        violations = []
        
        # Schedule operations in sequence
        for (job_id, op_idx) in solution.genes:
            job = job_dict.get(job_id)
            if not job:
                continue
            
            # Skip if operation already scheduled
            if op_idx != job_progress[job_id]:
                continue
            
            # Get operation details
            if op_idx >= len(job.operations):
                continue
            
            machine_id, duration = job.operations[op_idx]
            
            # Check if machine exists
            if machine_id not in machine_dict:
                violations.append(f"Job {job_id} op {op_idx}: Machine {machine_id} not found")
                continue
            
            # Calculate start time
            start_time = max(
                machine_available[machine_id],
                job_completion[job_id],
                job.release_time
            )
            
            end_time = start_time + duration
            
            # Create operation
            op = Operation(
                job_id=job_id,
                operation_id=op_idx,
                machine_id=machine_id,
                duration=duration,
                start_time=start_time,
                end_time=end_time
            )
            
            operations.append(op)
            
            # Update tracking
            machine_available[machine_id] = end_time
            machine_total_time[machine_id] += duration
            job_completion[job_id] = end_time
            job_progress[job_id] = op_idx + 1
        
        # Calculate metrics
        makespan = max(job_completion.values()) if job_completion else 0.0
        
        # Calculate tardiness
        total_tardiness = 0.0
        for job in jobs:
            if job.due_date and job_completion[job.id] > job.due_date:
                tardiness = job_completion[job.id] - job.due_date
                total_tardiness += tardiness
                violations.append(f"Job {job.id} late by {tardiness:.1f} time units")
        
        # Calculate machine utilization
        machine_utilization = {}
        for machine in machines:
            if makespan > 0:
                util = (machine_total_time[machine.id] / makespan) * 100.0
                machine_utilization[machine.id] = util
            else:
                machine_utilization[machine.id] = 0.0
        
        is_feasible = len(violations) == 0
        
        return Schedule(
            operations=operations,
            makespan=makespan,
            total_tardiness=total_tardiness,
            machine_utilization=machine_utilization,
            is_feasible=is_feasible,
            violations=violations
        )
    
    def _select_parents(self, population: List[Solution], temperature: float) -> List[Solution]:
        """Select parents for reproduction using tournament selection"""
        tournament_size = 3
        parents = []
        
        for _ in range(len(population)):
            tournament = random.sample(population, min(tournament_size, len(population)))
            winner = min(tournament, key=lambda s: s.fitness)
            parents.append(winner)
        
        return parents
    
    def _update_population(self, combined: List[Solution], target_size: int) -> List[Solution]:
        """Update population keeping best solutions"""
        combined.sort(key=lambda s: s.fitness)
        return combined[:target_size]

