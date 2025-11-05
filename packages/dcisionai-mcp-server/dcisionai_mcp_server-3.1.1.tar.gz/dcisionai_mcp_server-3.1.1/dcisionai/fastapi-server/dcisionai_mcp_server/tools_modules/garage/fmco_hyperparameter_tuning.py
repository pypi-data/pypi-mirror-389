"""
FMCO Automated Hyperparameter Tuning
Advanced hyperparameter optimization for FMCO models
"""

import logging
import json
import asyncio
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import optuna
from optuna.samplers import TPESampler, RandomSampler, CmaEsSampler
from optuna.pruners import MedianPruner, SuccessiveHalvingPruner

logger = logging.getLogger(__name__)

class OptimizationObjective(Enum):
    """Optimization objectives for hyperparameter tuning"""
    ACCURACY = "accuracy"
    SPEED = "speed"
    MEMORY_EFFICIENCY = "memory_efficiency"
    CONVERGENCE_RATE = "convergence_rate"
    GENERALIZATION = "generalization"
    MULTI_OBJECTIVE = "multi_objective"

class TuningStrategy(Enum):
    """Hyperparameter tuning strategies"""
    BAYESIAN_OPTIMIZATION = "bayesian_optimization"
    RANDOM_SEARCH = "random_search"
    GRID_SEARCH = "grid_search"
    EVOLUTIONARY = "evolutionary"
    MULTI_OBJECTIVE_OPTIMIZATION = "multi_objective_optimization"

@dataclass
class HyperparameterSpace:
    """Hyperparameter search space definition"""
    name: str
    param_type: str  # 'int', 'float', 'categorical', 'log'
    bounds: Tuple[float, float]
    default_value: Any
    description: str

@dataclass
class TuningConfig:
    """Configuration for hyperparameter tuning"""
    strategy: TuningStrategy
    objective: OptimizationObjective
    max_trials: int
    timeout: int
    n_jobs: int
    hyperparameter_spaces: List[HyperparameterSpace]
    evaluation_metrics: List[str]
    early_stopping_patience: int
    pruning_enabled: bool

@dataclass
class TuningResult:
    """Result from hyperparameter tuning"""
    best_params: Dict[str, Any]
    best_score: float
    best_trial: int
    total_trials: int
    tuning_time: float
    convergence_history: List[float]
    param_importance: Dict[str, float]
    optimization_direction: str

class FMCOHyperparameterTuner:
    """Automated hyperparameter tuning for FMCO models"""
    
    def __init__(self):
        self.tuning_history = []
        self.best_configurations = {}
        
        # Initialize Optuna study storage
        self.study_storage = "sqlite:///fmco_tuning.db"
        
        # Define default hyperparameter spaces for different architectures
        self.architecture_spaces = self._initialize_architecture_spaces()
    
    def _initialize_architecture_spaces(self) -> Dict[str, List[HyperparameterSpace]]:
        """Initialize hyperparameter spaces for different architectures"""
        
        return {
            "transformer_based": [
                HyperparameterSpace("hidden_size", "int", (128, 1024), 512, "Hidden dimension size"),
                HyperparameterSpace("num_layers", "int", (2, 12), 6, "Number of transformer layers"),
                HyperparameterSpace("num_heads", "int", (4, 16), 8, "Number of attention heads"),
                HyperparameterSpace("dropout", "float", (0.0, 0.5), 0.1, "Dropout rate"),
                HyperparameterSpace("learning_rate", "log", (1e-5, 1e-2), 1e-4, "Learning rate"),
                HyperparameterSpace("batch_size", "categorical", (16, 32, 64, 128), 32, "Batch size"),
                HyperparameterSpace("weight_decay", "log", (1e-6, 1e-2), 1e-4, "Weight decay"),
                HyperparameterSpace("warmup_steps", "int", (100, 2000), 1000, "Warmup steps")
            ],
            "graph_neural_network": [
                HyperparameterSpace("hidden_dim", "int", (64, 512), 256, "Hidden dimension"),
                HyperparameterSpace("num_layers", "int", (2, 8), 4, "Number of GNN layers"),
                HyperparameterSpace("message_passing", "categorical", ("gat", "gcn", "graphsage", "gin"), "gat", "Message passing type"),
                HyperparameterSpace("dropout", "float", (0.0, 0.5), 0.1, "Dropout rate"),
                HyperparameterSpace("learning_rate", "log", (1e-5, 1e-2), 5e-4, "Learning rate"),
                HyperparameterSpace("batch_size", "categorical", (8, 16, 32, 64), 16, "Batch size"),
                HyperparameterSpace("num_samples", "int", (5, 20), 10, "Number of samples"),
                HyperparameterSpace("temperature", "float", (0.5, 2.0), 1.0, "Sampling temperature")
            ],
            "reinforcement_learning": [
                HyperparameterSpace("state_dim", "int", (64, 256), 128, "State dimension"),
                HyperparameterSpace("action_dim", "int", (32, 128), 64, "Action dimension"),
                HyperparameterSpace("hidden_dim", "int", (128, 512), 256, "Hidden dimension"),
                HyperparameterSpace("gamma", "float", (0.9, 0.999), 0.99, "Discount factor"),
                HyperparameterSpace("learning_rate", "log", (1e-5, 1e-2), 3e-4, "Learning rate"),
                HyperparameterSpace("batch_size", "categorical", (32, 64, 128, 256), 64, "Batch size"),
                HyperparameterSpace("epsilon", "float", (0.01, 0.3), 0.1, "Exploration rate"),
                HyperparameterSpace("max_steps", "int", (50, 200), 100, "Maximum steps per episode")
            ],
            "hybrid_llm_solver": [
                HyperparameterSpace("llm_model", "categorical", ("gpt-4", "claude-3-sonnet", "gpt-3.5-turbo"), "gpt-4", "LLM model"),
                HyperparameterSpace("solver_type", "categorical", ("cplex", "gurobi", "scip"), "cplex", "Solver type"),
                HyperparameterSpace("hybrid_threshold", "float", (0.5, 0.9), 0.7, "Hybrid threshold"),
                HyperparameterSpace("llm_temperature", "float", (0.1, 0.8), 0.3, "LLM temperature"),
                HyperparameterSpace("solver_timeout", "int", (60, 600), 300, "Solver timeout"),
                HyperparameterSpace("confidence_threshold", "float", (0.6, 0.95), 0.8, "Confidence threshold"),
                HyperparameterSpace("fallback_enabled", "categorical", (True, False), True, "Fallback enabled")
            ],
            "multi_task_learning": [
                HyperparameterSpace("shared_layers", "int", (2, 8), 4, "Shared layers"),
                HyperparameterSpace("task_specific_layers", "int", (1, 4), 2, "Task-specific layers"),
                HyperparameterSpace("hidden_dim", "int", (256, 1024), 512, "Hidden dimension"),
                HyperparameterSpace("learning_rate", "log", (1e-5, 1e-2), 1e-4, "Learning rate"),
                HyperparameterSpace("task_weights", "categorical", ("uniform", "adaptive", "priority"), "adaptive", "Task weighting"),
                HyperparameterSpace("regularization", "log", (1e-6, 1e-1), 0.01, "Regularization strength"),
                HyperparameterSpace("epochs", "int", (50, 500), 200, "Training epochs"),
                HyperparameterSpace("ensemble_size", "int", (1, 5), 3, "Ensemble size")
            ]
        }
    
    def create_tuning_config(
        self,
        architecture: str,
        objective: OptimizationObjective = OptimizationObjective.ACCURACY,
        strategy: TuningStrategy = TuningStrategy.BAYESIAN_OPTIMIZATION,
        max_trials: int = 100,
        timeout: int = 3600
    ) -> TuningConfig:
        """Create tuning configuration for specific architecture"""
        
        if architecture not in self.architecture_spaces:
            raise ValueError(f"Unknown architecture: {architecture}")
        
        hyperparameter_spaces = self.architecture_spaces[architecture]
        
        # Define evaluation metrics based on objective
        evaluation_metrics = {
            OptimizationObjective.ACCURACY: ["accuracy", "f1_score", "precision", "recall"],
            OptimizationObjective.SPEED: ["inference_time", "training_time", "throughput"],
            OptimizationObjective.MEMORY_EFFICIENCY: ["memory_usage", "model_size", "peak_memory"],
            OptimizationObjective.CONVERGENCE_RATE: ["convergence_time", "epochs_to_convergence", "loss_reduction"],
            OptimizationObjective.GENERALIZATION: ["validation_accuracy", "test_accuracy", "generalization_gap"],
            OptimizationObjective.MULTI_OBJECTIVE: ["accuracy", "speed", "memory_efficiency"]
        }
        
        return TuningConfig(
            strategy=strategy,
            objective=objective,
            max_trials=max_trials,
            timeout=timeout,
            n_jobs=4,
            hyperparameter_spaces=hyperparameter_spaces,
            evaluation_metrics=evaluation_metrics[objective],
            early_stopping_patience=10,
            pruning_enabled=True
        )
    
    async def tune_hyperparameters(
        self,
        config: TuningConfig,
        evaluation_function: Callable[[Dict[str, Any]], float],
        study_name: Optional[str] = None
    ) -> TuningResult:
        """Run hyperparameter tuning"""
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            logger.info(f"🔧 Starting hyperparameter tuning with {config.strategy.value}")
            logger.info(f"📊 Objective: {config.objective.value}")
            logger.info(f"🎯 Max trials: {config.max_trials}")
            
            # Create Optuna study
            study = self._create_optuna_study(config, study_name)
            
            # Define objective function
            def objective(trial):
                # Sample hyperparameters
                params = self._sample_hyperparameters(trial, config.hyperparameter_spaces)
                
                # Evaluate the configuration
                score = evaluation_function(params)
                
                return score
            
            # Run optimization
            study.optimize(
                objective,
                n_trials=config.max_trials,
                timeout=config.timeout,
                n_jobs=config.n_jobs,
                show_progress_bar=True
            )
            
            # Extract results
            best_trial = study.best_trial
            best_params = best_trial.params
            best_score = best_trial.value
            
            # Get convergence history
            convergence_history = [t.value for t in study.trials if t.value is not None]
            
            # Calculate parameter importance
            param_importance = self._calculate_parameter_importance(study)
            
            tuning_time = asyncio.get_event_loop().time() - start_time
            
            result = TuningResult(
                best_params=best_params,
                best_score=best_score,
                best_trial=best_trial.number,
                total_trials=len(study.trials),
                tuning_time=tuning_time,
                convergence_history=convergence_history,
                param_importance=param_importance,
                optimization_direction="maximize" if config.objective in [OptimizationObjective.ACCURACY, OptimizationObjective.GENERALIZATION] else "minimize"
            )
            
            # Store in history
            self.tuning_history.append({
                "timestamp": datetime.now().isoformat(),
                "architecture": study_name or "unknown",
                "strategy": config.strategy.value,
                "objective": config.objective.value,
                "best_score": best_score,
                "total_trials": len(study.trials),
                "tuning_time": tuning_time
            })
            
            logger.info(f"✅ Hyperparameter tuning completed: {best_score:.4f} in {tuning_time:.2f}s")
            logger.info(f"📈 Best trial: {best_trial.number}, Total trials: {len(study.trials)}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Hyperparameter tuning failed: {e}")
            tuning_time = asyncio.get_event_loop().time() - start_time
            
            return TuningResult(
                best_params={},
                best_score=0.0,
                best_trial=0,
                total_trials=0,
                tuning_time=tuning_time,
                convergence_history=[],
                param_importance={},
                optimization_direction="unknown"
            )
    
    def _create_optuna_study(self, config: TuningConfig, study_name: Optional[str]) -> optuna.Study:
        """Create Optuna study with appropriate configuration"""
        
        # Choose sampler based on strategy
        if config.strategy == TuningStrategy.BAYESIAN_OPTIMIZATION:
            sampler = TPESampler(seed=42)
        elif config.strategy == TuningStrategy.RANDOM_SEARCH:
            sampler = RandomSampler(seed=42)
        elif config.strategy == TuningStrategy.EVOLUTIONARY:
            sampler = CmaEsSampler(seed=42)
        else:
            sampler = TPESampler(seed=42)  # Default to TPE
        
        # Choose pruner
        if config.pruning_enabled:
            pruner = MedianPruner(n_startup_trials=5, n_warmup_steps=10)
        else:
            pruner = None
        
        # Create study
        study = optuna.create_study(
            study_name=study_name or f"fmco_tuning_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            direction="maximize" if config.objective in [OptimizationObjective.ACCURACY, OptimizationObjective.GENERALIZATION] else "minimize",
            sampler=sampler,
            pruner=pruner,
            storage=self.study_storage,
            load_if_exists=True
        )
        
        return study
    
    def _sample_hyperparameters(self, trial, spaces: List[HyperparameterSpace]) -> Dict[str, Any]:
        """Sample hyperparameters from search spaces"""
        
        params = {}
        
        for space in spaces:
            if space.param_type == "int":
                params[space.name] = trial.suggest_int(space.name, int(space.bounds[0]), int(space.bounds[1]))
            elif space.param_type == "float":
                params[space.name] = trial.suggest_float(space.name, space.bounds[0], space.bounds[1])
            elif space.param_type == "log":
                params[space.name] = trial.suggest_loguniform(space.name, space.bounds[0], space.bounds[1])
            elif space.param_type == "categorical":
                params[space.name] = trial.suggest_categorical(space.name, space.bounds)
        
        return params
    
    def _calculate_parameter_importance(self, study: optuna.Study) -> Dict[str, float]:
        """Calculate parameter importance from study"""
        
        try:
            importance = optuna.importance.get_param_importances(study)
            return importance
        except Exception as e:
            logger.warning(f"⚠️ Could not calculate parameter importance: {e}")
            return {}
    
    async def multi_objective_tuning(
        self,
        config: TuningConfig,
        evaluation_functions: Dict[str, Callable[[Dict[str, Any]], float]],
        objectives: List[str]
    ) -> Dict[str, TuningResult]:
        """Run multi-objective hyperparameter tuning"""
        
        logger.info(f"🎯 Starting multi-objective tuning for {len(objectives)} objectives")
        
        # Create multi-objective study
        study = optuna.create_study(
            study_name=f"multi_objective_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            directions=["maximize"] * len(objectives),  # Assume all objectives are to be maximized
            sampler=TPESampler(seed=42),
            storage=self.study_storage,
            load_if_exists=True
        )
        
        def multi_objective(trial):
            # Sample hyperparameters
            params = self._sample_hyperparameters(trial, config.hyperparameter_spaces)
            
            # Evaluate all objectives
            scores = []
            for obj_name in objectives:
                if obj_name in evaluation_functions:
                    score = evaluation_functions[obj_name](params)
                    scores.append(score)
                else:
                    logger.warning(f"⚠️ Evaluation function not found for objective: {obj_name}")
                    scores.append(0.0)
            
            return scores
        
        # Run optimization
        study.optimize(multi_objective, n_trials=config.max_trials, timeout=config.timeout)
        
        # Extract Pareto-optimal solutions
        pareto_front = study.best_trials
        
        results = {}
        for i, trial in enumerate(pareto_front[:5]):  # Top 5 Pareto-optimal solutions
            results[f"pareto_solution_{i+1}"] = TuningResult(
                best_params=trial.params,
                best_score=trial.values[0] if trial.values else 0.0,
                best_trial=trial.number,
                total_trials=len(study.trials),
                tuning_time=0.0,  # Would need to track this separately
                convergence_history=[],
                param_importance={},
                optimization_direction="multi_objective"
            )
        
        logger.info(f"✅ Multi-objective tuning completed: {len(pareto_front)} Pareto-optimal solutions")
        
        return results
    
    def get_tuning_history(self) -> List[Dict[str, Any]]:
        """Get tuning history"""
        return self.tuning_history
    
    def get_best_configurations(self) -> Dict[str, Dict[str, Any]]:
        """Get best configurations for each architecture"""
        return self.best_configurations
    
    def suggest_hyperparameters(
        self,
        architecture: str,
        objective: OptimizationObjective,
        previous_results: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Suggest hyperparameters based on architecture and objective"""
        
        if architecture not in self.architecture_spaces:
            raise ValueError(f"Unknown architecture: {architecture}")
        
        spaces = self.architecture_spaces[architecture]
        
        # Start with default values
        suggested_params = {}
        for space in spaces:
            suggested_params[space.name] = space.default_value
        
        # Adjust based on objective
        if objective == OptimizationObjective.SPEED:
            # Favor smaller models for speed
            if "hidden_size" in suggested_params:
                suggested_params["hidden_size"] = min(suggested_params["hidden_size"], 256)
            if "num_layers" in suggested_params:
                suggested_params["num_layers"] = min(suggested_params["num_layers"], 4)
            if "batch_size" in suggested_params:
                suggested_params["batch_size"] = max(suggested_params["batch_size"], 64)
        
        elif objective == OptimizationObjective.MEMORY_EFFICIENCY:
            # Favor memory-efficient configurations
            if "hidden_size" in suggested_params:
                suggested_params["hidden_size"] = min(suggested_params["hidden_size"], 256)
            if "batch_size" in suggested_params:
                suggested_params["batch_size"] = min(suggested_params["batch_size"], 16)
        
        elif objective == OptimizationObjective.ACCURACY:
            # Favor larger models for accuracy
            if "hidden_size" in suggested_params:
                suggested_params["hidden_size"] = max(suggested_params["hidden_size"], 512)
            if "num_layers" in suggested_params:
                suggested_params["num_layers"] = max(suggested_params["num_layers"], 6)
        
        return suggested_params
    
    def analyze_tuning_results(self, results: List[TuningResult]) -> Dict[str, Any]:
        """Analyze tuning results and provide insights"""
        
        if not results:
            return {"status": "no_results"}
        
        # Calculate statistics
        scores = [r.best_score for r in results]
        times = [r.tuning_time for r in results]
        
        analysis = {
            "total_experiments": len(results),
            "score_statistics": {
                "mean": np.mean(scores),
                "std": np.std(scores),
                "min": np.min(scores),
                "max": np.max(scores),
                "median": np.median(scores)
            },
            "time_statistics": {
                "mean": np.mean(times),
                "std": np.std(times),
                "min": np.min(times),
                "max": np.max(times),
                "total": np.sum(times)
            },
            "best_result": {
                "score": max(scores),
                "index": scores.index(max(scores)),
                "params": results[scores.index(max(scores))].best_params
            },
            "convergence_analysis": {
                "avg_trials": np.mean([r.total_trials for r in results]),
                "convergence_rate": len([r for r in results if r.total_trials < 50]) / len(results)
            }
        }
        
        return analysis
