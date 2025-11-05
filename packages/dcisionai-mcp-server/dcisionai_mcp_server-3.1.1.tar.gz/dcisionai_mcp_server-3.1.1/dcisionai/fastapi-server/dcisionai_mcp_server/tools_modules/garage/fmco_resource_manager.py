"""
FMCO Resource Management
Manage features based on available resources
"""

import logging
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ResourceLevel(Enum):
    """Resource availability levels"""
    MINIMAL = "minimal"          # CPU only, no GPU
    STANDARD = "standard"       # CPU + limited GPU
    PREMIUM = "premium"         # Full GPU resources
    ENTERPRISE = "enterprise"   # Multiple GPUs, cloud resources

@dataclass
class ResourceConfig:
    """Resource configuration"""
    level: ResourceLevel
    has_gpu: bool
    gpu_memory: Optional[int]  # GB
    cpu_cores: int
    available_features: Dict[str, bool]
    performance_settings: Dict[str, Any]

class FMCOResourceManager:
    """Manage FMCO features based on available resources"""
    
    def __init__(self):
        self.resource_config = self._detect_resources()
        self._configure_features()
    
    def _detect_resources(self) -> ResourceConfig:
        """Detect available system resources"""
        
        # Check for GPU
        has_gpu = False
        gpu_memory = None
        
        try:
            import torch
            if torch.cuda.is_available():
                has_gpu = True
                gpu_memory = torch.cuda.get_device_properties(0).total_memory // (1024**3)
                logger.info(f"✅ GPU detected: {torch.cuda.get_device_name(0)} ({gpu_memory}GB)")
            else:
                logger.info("⚠️ No GPU detected, using CPU-only mode")
        except ImportError:
            logger.info("⚠️ PyTorch not available, using CPU-only mode")
        
        # Check CPU cores
        import multiprocessing
        cpu_cores = multiprocessing.cpu_count()
        
        # Determine resource level
        if has_gpu and gpu_memory and gpu_memory >= 16:
            level = ResourceLevel.ENTERPRISE
        elif has_gpu and gpu_memory and gpu_memory >= 8:
            level = ResourceLevel.PREMIUM
        elif has_gpu:
            level = ResourceLevel.STANDARD
        else:
            level = ResourceLevel.MINIMAL
        
        logger.info(f"🔧 Resource level detected: {level.value}")
        
        return ResourceConfig(
            level=level,
            has_gpu=has_gpu,
            gpu_memory=gpu_memory,
            cpu_cores=cpu_cores,
            available_features={},
            performance_settings={}
        )
    
    def _configure_features(self):
        """Configure available features based on resources - Phase 1 Only"""
        
        # Phase 1: CPU-only features (no GPU dependencies)
        features = {
            "paperIntegration": True,      # ✅ Pinecone + arXiv integration
            "hyperparameterTuning": True,  # ✅ CPU-based optimization
            "modelFineTuning": False,     # ❌ Phase 2 (requires GPU)
            "multiTaskLearning": False,    # ❌ Phase 2 (requires GPU)
            "llmSolvers": True,           # ✅ LLM-based solving
            "benchmarking": True,         # ✅ Standard datasets
            "realTimeStreaming": True,    # ✅ CoT streaming
            "advancedPrompting": True,    # ✅ Prompt engineering
            "domainAdaptation": True,     # ✅ Domain-specific templates
            "architectureSelection": True, # ✅ Auto-select best architecture
        }
        
        # Phase 1: No GPU-dependent features enabled
        logger.info("🚀 Phase 1 Mode: CPU-only features enabled")
        
        # Configure performance settings
        performance_settings = {
            "batch_size": 4 if self.resource_config.has_gpu else 1,
            "max_tokens": 4000 if self.resource_config.has_gpu else 2000,
            "num_workers": min(4, self.resource_config.cpu_cores),
            "gradient_accumulation_steps": 8 if not self.resource_config.has_gpu else 4,
            "mixed_precision": self.resource_config.has_gpu,
            "cpu_offload": not self.resource_config.has_gpu
        }
        
        self.resource_config.available_features = features
        self.resource_config.performance_settings = performance_settings
        
        logger.info(f"✅ Features configured for {self.resource_config.level.value} resources")
        logger.info(f"📊 Available features: {[k for k, v in features.items() if v]}")
    
    def get_available_features(self) -> Dict[str, bool]:
        """Get list of available features"""
        return self.resource_config.available_features
    
    def is_feature_available(self, feature: str) -> bool:
        """Check if a specific feature is available"""
        return self.resource_config.available_features.get(feature, False)
    
    def get_performance_settings(self) -> Dict[str, Any]:
        """Get performance settings for current resources"""
        return self.resource_config.performance_settings
    
    def get_resource_info(self) -> Dict[str, Any]:
        """Get resource information"""
        return {
            "level": self.resource_config.level.value,
            "has_gpu": self.resource_config.has_gpu,
            "gpu_memory": self.resource_config.gpu_memory,
            "cpu_cores": self.resource_config.cpu_cores,
            "available_features": self.resource_config.available_features,
            "performance_settings": self.resource_config.performance_settings
        }
    
    def get_upgrade_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for upgrading resources"""
        
        recommendations = {
            "current_level": self.resource_config.level.value,
            "upgrade_options": [],
            "feature_unlocks": []
        }
        
        if self.resource_config.level == ResourceLevel.MINIMAL:
            recommendations["upgrade_options"].extend([
                {
                    "level": "standard",
                    "description": "Add any GPU (even 4GB)",
                    "cost": "~$200-500",
                    "benefits": ["Enable model fine-tuning", "Faster inference"]
                },
                {
                    "level": "premium", 
                    "description": "Add 8GB+ GPU (RTX 3070/4060)",
                    "cost": "~$400-800",
                    "benefits": ["Full fine-tuning", "Multi-task learning", "Large models"]
                }
            ])
            recommendations["feature_unlocks"] = ["modelFineTuning", "multiTaskLearning"]
        
        elif self.resource_config.level == ResourceLevel.STANDARD:
            recommendations["upgrade_options"].extend([
                {
                    "level": "premium",
                    "description": "Upgrade to 8GB+ GPU",
                    "cost": "~$200-400",
                    "benefits": ["Better fine-tuning performance", "Larger models"]
                }
            ])
            recommendations["feature_unlocks"] = ["multiTaskLearning"]
        
        return recommendations
    
    def create_phased_deployment_plan(self) -> Dict[str, Any]:
        """Create a phased deployment plan"""
        
        phases = {
            "phase_1": {
                "name": "Core FMCO Features",
                "features": ["paperIntegration", "hyperparameterTuning", "llmSolvers", "benchmarking"],
                "requirements": "CPU only",
                "timeline": "Immediate",
                "status": "ready"
            },
            "phase_2": {
                "name": "Advanced Optimization",
                "features": ["advancedPrompting", "realTimeStreaming"],
                "requirements": "CPU + basic GPU",
                "timeline": "1-2 weeks",
                "status": "ready" if self.resource_config.has_gpu else "pending_gpu"
            },
            "phase_3": {
                "name": "Model Customization",
                "features": ["modelFineTuning", "multiTaskLearning"],
                "requirements": "8GB+ GPU",
                "timeline": "1 month",
                "status": "ready" if self.resource_config.level in [ResourceLevel.PREMIUM, ResourceLevel.ENTERPRISE] else "pending_gpu_upgrade"
            }
        }
        
        return {
            "current_phase": "phase_1" if self.resource_config.level == ResourceLevel.MINIMAL else "phase_2",
            "phases": phases,
            "recommendations": self.get_upgrade_recommendations()
        }
