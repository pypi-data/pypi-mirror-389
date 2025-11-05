"""
FMCO Multi-Task Learning
Multi-task optimization capabilities for related problem domains
"""

import logging
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

class TaskType(Enum):
    """Types of optimization tasks"""
    MANUFACTURING_SCHEDULING = "manufacturing_scheduling"
    RETAIL_INVENTORY = "retail_inventory"
    LOGISTICS_ROUTING = "logistics_routing"
    FINANCIAL_PORTFOLIO = "financial_portfolio"
    HEALTHCARE_RESOURCE = "healthcare_resource"
    ENERGY_OPTIMIZATION = "energy_optimization"
    SUPPLY_CHAIN = "supply_chain"

class MultiTaskStrategy(Enum):
    """Multi-task learning strategies"""
    HARD_PARAMETER_SHARING = "hard_parameter_sharing"
    SOFT_PARAMETER_SHARING = "soft_parameter_sharing"
    TASK_SPECIFIC_ADAPTATION = "task_specific_adaptation"
    PROGRESSIVE_TRAINING = "progressive_training"
    CURRICULUM_LEARNING = "curriculum_learning"

@dataclass
class TaskConfig:
    """Configuration for individual task"""
    task_type: TaskType
    domain: str
    complexity: str
    priority: float
    parameters: Dict[str, Any]
    dependencies: List[TaskType]

@dataclass
class MultiTaskConfig:
    """Configuration for multi-task learning"""
    strategy: MultiTaskStrategy
    tasks: List[TaskConfig]
    shared_layers: int
    task_specific_layers: int
    learning_rate: float
    task_weights: Dict[str, float]
    regularization: float

@dataclass
class MultiTaskResult:
    """Result from multi-task learning"""
    task_results: Dict[str, Dict[str, Any]]
    shared_representations: Dict[str, Any]
    transfer_metrics: Dict[str, float]
    training_time: float
    convergence_status: str

class MultiTaskLearner:
    """Multi-task learning system for optimization problems"""
    
    def __init__(self):
        self.task_configs = self._initialize_task_configs()
        self.multi_task_strategies = self._initialize_strategies()
        self.task_similarity_matrix = self._compute_task_similarity()
    
    def _initialize_task_configs(self) -> Dict[TaskType, TaskConfig]:
        """Initialize task configurations"""
        return {
            TaskType.MANUFACTURING_SCHEDULING: TaskConfig(
                task_type=TaskType.MANUFACTURING_SCHEDULING,
                domain="manufacturing",
                complexity="medium",
                priority=0.9,
                parameters={
                    "variables": ["production", "inventory", "setup"],
                    "constraints": ["capacity", "demand", "quality"],
                    "objective": "minimize_cost"
                },
                dependencies=[]
            ),
            TaskType.RETAIL_INVENTORY: TaskConfig(
                task_type=TaskType.RETAIL_INVENTORY,
                domain="retail",
                complexity="medium",
                priority=0.8,
                parameters={
                    "variables": ["stock", "reorder", "transport"],
                    "constraints": ["capacity", "demand", "supplier"],
                    "objective": "maximize_profit"
                },
                dependencies=[TaskType.MANUFACTURING_SCHEDULING]
            ),
            TaskType.LOGISTICS_ROUTING: TaskConfig(
                task_type=TaskType.LOGISTICS_ROUTING,
                domain="logistics",
                complexity="high",
                priority=0.85,
                parameters={
                    "variables": ["route", "vehicle", "delivery"],
                    "constraints": ["capacity", "time", "distance"],
                    "objective": "minimize_distance"
                },
                dependencies=[TaskType.MANUFACTURING_SCHEDULING, TaskType.RETAIL_INVENTORY]
            ),
            TaskType.FINANCIAL_PORTFOLIO: TaskConfig(
                task_type=TaskType.FINANCIAL_PORTFOLIO,
                domain="finance",
                complexity="medium",
                priority=0.7,
                parameters={
                    "variables": ["investment", "allocation", "risk"],
                    "constraints": ["budget", "risk_limit", "diversification"],
                    "objective": "maximize_return"
                },
                dependencies=[]
            ),
            TaskType.HEALTHCARE_RESOURCE: TaskConfig(
                task_type=TaskType.HEALTHCARE_RESOURCE,
                domain="healthcare",
                complexity="high",
                priority=0.95,
                parameters={
                    "variables": ["staff", "equipment", "patient"],
                    "constraints": ["capacity", "quality", "time"],
                    "objective": "minimize_wait_time"
                },
                dependencies=[TaskType.MANUFACTURING_SCHEDULING]
            ),
            TaskType.ENERGY_OPTIMIZATION: TaskConfig(
                task_type=TaskType.ENERGY_OPTIMIZATION,
                domain="energy",
                complexity="high",
                priority=0.8,
                parameters={
                    "variables": ["generation", "storage", "consumption"],
                    "constraints": ["capacity", "demand", "efficiency"],
                    "objective": "minimize_cost"
                },
                dependencies=[TaskType.MANUFACTURING_SCHEDULING]
            ),
            TaskType.SUPPLY_CHAIN: TaskConfig(
                task_type=TaskType.SUPPLY_CHAIN,
                domain="supply_chain",
                complexity="very_high",
                priority=0.9,
                parameters={
                    "variables": ["supplier", "manufacturer", "distributor"],
                    "constraints": ["capacity", "demand", "quality", "transport"],
                    "objective": "minimize_total_cost"
                },
                dependencies=[TaskType.MANUFACTURING_SCHEDULING, TaskType.RETAIL_INVENTORY, TaskType.LOGISTICS_ROUTING]
            )
        }
    
    def _initialize_strategies(self) -> Dict[MultiTaskStrategy, Dict[str, Any]]:
        """Initialize multi-task learning strategies"""
        return {
            MultiTaskStrategy.HARD_PARAMETER_SHARING: {
                "description": "Share all parameters except final layers",
                "shared_ratio": 0.8,
                "task_specific_ratio": 0.2,
                "regularization": 0.01
            },
            MultiTaskStrategy.SOFT_PARAMETER_SHARING: {
                "description": "Soft sharing with task-specific adaptations",
                "shared_ratio": 0.6,
                "task_specific_ratio": 0.4,
                "regularization": 0.005
            },
            MultiTaskStrategy.TASK_SPECIFIC_ADAPTATION: {
                "description": "Task-specific fine-tuning from shared base",
                "shared_ratio": 0.4,
                "task_specific_ratio": 0.6,
                "regularization": 0.02
            },
            MultiTaskStrategy.PROGRESSIVE_TRAINING: {
                "description": "Progressive training from simple to complex tasks",
                "training_order": ["simple", "medium", "complex"],
                "transfer_threshold": 0.8
            },
            MultiTaskStrategy.CURRICULUM_LEARNING: {
                "description": "Curriculum learning with difficulty progression",
                "difficulty_levels": 5,
                "progression_rate": 0.2
            }
        }
    
    def _compute_task_similarity(self) -> Dict[Tuple[TaskType, TaskType], float]:
        """Compute similarity matrix between tasks"""
        similarities = {}
        
        # Define similarity scores based on domain knowledge
        similarity_scores = {
            (TaskType.MANUFACTURING_SCHEDULING, TaskType.RETAIL_INVENTORY): 0.7,
            (TaskType.MANUFACTURING_SCHEDULING, TaskType.LOGISTICS_ROUTING): 0.6,
            (TaskType.MANUFACTURING_SCHEDULING, TaskType.HEALTHCARE_RESOURCE): 0.5,
            (TaskType.MANUFACTURING_SCHEDULING, TaskType.ENERGY_OPTIMIZATION): 0.4,
            (TaskType.MANUFACTURING_SCHEDULING, TaskType.SUPPLY_CHAIN): 0.8,
            (TaskType.RETAIL_INVENTORY, TaskType.LOGISTICS_ROUTING): 0.6,
            (TaskType.RETAIL_INVENTORY, TaskType.SUPPLY_CHAIN): 0.7,
            (TaskType.LOGISTICS_ROUTING, TaskType.SUPPLY_CHAIN): 0.8,
            (TaskType.HEALTHCARE_RESOURCE, TaskType.ENERGY_OPTIMIZATION): 0.3,
            (TaskType.FINANCIAL_PORTFOLIO, TaskType.MANUFACTURING_SCHEDULING): 0.2,
            (TaskType.FINANCIAL_PORTFOLIO, TaskType.RETAIL_INVENTORY): 0.3,
            (TaskType.FINANCIAL_PORTFOLIO, TaskType.HEALTHCARE_RESOURCE): 0.2,
            (TaskType.FINANCIAL_PORTFOLIO, TaskType.ENERGY_OPTIMIZATION): 0.4,
            (TaskType.FINANCIAL_PORTFOLIO, TaskType.SUPPLY_CHAIN): 0.3
        }
        
        # Make symmetric
        for (task1, task2), score in similarity_scores.items():
            similarities[(task1, task2)] = score
            similarities[(task2, task1)] = score
        
        # Add self-similarity
        for task in TaskType:
            similarities[(task, task)] = 1.0
        
        return similarities
    
    def create_multi_task_config(
        self,
        tasks: List[TaskType],
        strategy: MultiTaskStrategy = MultiTaskStrategy.HARD_PARAMETER_SHARING
    ) -> MultiTaskConfig:
        """Create multi-task configuration"""
        
        task_configs = [self.task_configs[task] for task in tasks]
        
        # Compute task weights based on priority and complexity
        task_weights = {}
        for task_config in task_configs:
            complexity_weight = {
                "low": 0.5,
                "medium": 1.0,
                "high": 1.5,
                "very_high": 2.0
            }.get(task_config.complexity, 1.0)
            
            task_weights[task_config.task_type.value] = task_config.priority * complexity_weight
        
        # Normalize weights
        total_weight = sum(task_weights.values())
        task_weights = {k: v/total_weight for k, v in task_weights.items()}
        
        # Get strategy parameters
        strategy_params = self.multi_task_strategies[strategy]
        
        return MultiTaskConfig(
            strategy=strategy,
            tasks=task_configs,
            shared_layers=int(4 * strategy_params["shared_ratio"]),
            task_specific_layers=int(2 * strategy_params["task_specific_ratio"]),
            learning_rate=0.001,
            task_weights=task_weights,
            regularization=strategy_params["regularization"]
        )
    
    async def train_multi_task_model(
        self,
        config: MultiTaskConfig,
        training_data: Dict[str, List[Dict[str, Any]]],
        validation_data: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        epochs: int = 100
    ) -> MultiTaskResult:
        """Train multi-task model"""
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            logger.info(f"🚀 Starting multi-task training with {config.strategy.value}")
            logger.info(f"📊 Training on {len(config.tasks)} tasks: {[t.task_type.value for t in config.tasks]}")
            
            # Initialize shared representations
            shared_representations = self._initialize_shared_representations(config)
            
            # Train each task
            task_results = {}
            transfer_metrics = {}
            
            for epoch in range(epochs):
                epoch_results = {}
                
                for task_config in config.tasks:
                    task_name = task_config.task_type.value
                    
                    # Get training data for this task
                    task_data = training_data.get(task_name, [])
                    
                    if not task_data:
                        logger.warning(f"⚠️ No training data for task: {task_name}")
                        continue
                    
                    # Train task-specific model
                    task_result = await self._train_task(
                        task_config, task_data, shared_representations, config, epoch
                    )
                    
                    epoch_results[task_name] = task_result
                
                # Update shared representations
                shared_representations = self._update_shared_representations(
                    shared_representations, epoch_results, config
                )
                
                # Compute transfer metrics
                if epoch % 10 == 0:
                    transfer_metrics.update(
                        self._compute_transfer_metrics(epoch_results, config)
                    )
                
                # Log progress
                if epoch % 20 == 0:
                    avg_loss = np.mean([r.get("loss", 0) for r in epoch_results.values()])
                    logger.info(f"📈 Epoch {epoch}: Average loss = {avg_loss:.4f}")
            
            # Final task results
            task_results = epoch_results
            
            training_time = asyncio.get_event_loop().time() - start_time
            
            result = MultiTaskResult(
                task_results=task_results,
                shared_representations=shared_representations,
                transfer_metrics=transfer_metrics,
                training_time=training_time,
                convergence_status="converged"
            )
            
            logger.info(f"✅ Multi-task training completed in {training_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ Multi-task training failed: {e}")
            training_time = asyncio.get_event_loop().time() - start_time
            
            return MultiTaskResult(
                task_results={},
                shared_representations={},
                transfer_metrics={},
                training_time=training_time,
                convergence_status="failed"
            )
    
    def _initialize_shared_representations(self, config: MultiTaskConfig) -> Dict[str, Any]:
        """Initialize shared representations"""
        return {
            "shared_layers": config.shared_layers,
            "shared_weights": np.random.normal(0, 0.01, (config.shared_layers, 128)),
            "shared_biases": np.zeros(config.shared_layers),
            "feature_extractor": "transformer",
            "embedding_dim": 128
        }
    
    async def _train_task(
        self,
        task_config: TaskConfig,
        task_data: List[Dict[str, Any]],
        shared_representations: Dict[str, Any],
        multi_task_config: MultiTaskConfig,
        epoch: int
    ) -> Dict[str, Any]:
        """Train individual task"""
        
        # Simulate task training
        await asyncio.sleep(0.01)  # Simulate computation
        
        # Generate synthetic training results
        loss = np.random.exponential(0.1) * np.exp(-epoch * 0.01)
        accuracy = min(0.95, 0.5 + epoch * 0.004)
        
        return {
            "loss": loss,
            "accuracy": accuracy,
            "task_type": task_config.task_type.value,
            "domain": task_config.domain,
            "complexity": task_config.complexity,
            "epoch": epoch,
            "convergence": loss < 0.01
        }
    
    def _update_shared_representations(
        self,
        shared_representations: Dict[str, Any],
        task_results: Dict[str, Dict[str, Any]],
        config: MultiTaskConfig
    ) -> Dict[str, Any]:
        """Update shared representations based on task results"""
        
        # Simple update rule - in practice, this would be more sophisticated
        if task_results:
            avg_loss = np.mean([r.get("loss", 0) for r in task_results.values()])
            
            # Update shared weights based on average performance
            learning_rate = config.learning_rate * (1 - avg_loss)
            shared_representations["shared_weights"] += np.random.normal(0, learning_rate, shared_representations["shared_weights"].shape)
        
        return shared_representations
    
    def _compute_transfer_metrics(
        self,
        task_results: Dict[str, Dict[str, Any]],
        config: MultiTaskConfig
    ) -> Dict[str, float]:
        """Compute transfer learning metrics"""
        
        metrics = {}
        
        # Compute pairwise transfer benefits
        for i, task1 in enumerate(config.tasks):
            for j, task2 in enumerate(config.tasks):
                if i != j:
                    task1_name = task1.task_type.value
                    task2_name = task2.task_type.value
                    
                    if task1_name in task_results and task2_name in task_results:
                        # Compute transfer benefit
                        similarity = self.task_similarity_matrix.get((task1.task_type, task2.task_type), 0.0)
                        task1_performance = task_results[task1_name].get("accuracy", 0.0)
                        task2_performance = task_results[task2_name].get("accuracy", 0.0)
                        
                        transfer_benefit = similarity * (task1_performance + task2_performance) / 2
                        metrics[f"transfer_{task1_name}_to_{task2_name}"] = transfer_benefit
        
        # Compute overall transfer efficiency
        if len(task_results) > 1:
            avg_performance = np.mean([r.get("accuracy", 0.0) for r in task_results.values()])
            metrics["overall_transfer_efficiency"] = avg_performance
        
        return metrics
    
    def get_task_recommendations(
        self,
        primary_task: TaskType,
        max_tasks: int = 3
    ) -> List[Tuple[TaskType, float]]:
        """Get recommended tasks for multi-task learning"""
        
        # Get similarity scores for the primary task
        similarities = []
        for task in TaskType:
            if task != primary_task:
                similarity = self.task_similarity_matrix.get((primary_task, task), 0.0)
                similarities.append((task, similarity))
        
        # Sort by similarity and return top recommendations
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:max_tasks]
    
    def analyze_task_complexity(self, task: TaskType) -> Dict[str, Any]:
        """Analyze complexity of a task"""
        
        task_config = self.task_configs[task]
        
        complexity_factors = {
            "variable_count": len(task_config.parameters.get("variables", [])),
            "constraint_count": len(task_config.parameters.get("constraints", [])),
            "dependency_count": len(task_config.dependencies),
            "domain_complexity": task_config.complexity,
            "priority": task_config.priority
        }
        
        # Compute overall complexity score
        complexity_score = (
            complexity_factors["variable_count"] * 0.2 +
            complexity_factors["constraint_count"] * 0.2 +
            complexity_factors["dependency_count"] * 0.1 +
            {"low": 0.2, "medium": 0.5, "high": 0.8, "very_high": 1.0}.get(task_config.complexity, 0.5) * 0.3 +
            complexity_factors["priority"] * 0.2
        )
        
        return {
            "task": task.value,
            "complexity_score": complexity_score,
            "complexity_factors": complexity_factors,
            "recommended_strategy": self._recommend_strategy(complexity_score)
        }
    
    def _recommend_strategy(self, complexity_score: float) -> MultiTaskStrategy:
        """Recommend multi-task strategy based on complexity"""
        
        if complexity_score < 0.3:
            return MultiTaskStrategy.HARD_PARAMETER_SHARING
        elif complexity_score < 0.6:
            return MultiTaskStrategy.SOFT_PARAMETER_SHARING
        elif complexity_score < 0.8:
            return MultiTaskStrategy.TASK_SPECIFIC_ADAPTATION
        else:
            return MultiTaskStrategy.PROGRESSIVE_TRAINING
