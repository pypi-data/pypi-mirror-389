"""
Intelligent data simulator for optimization problems

Adapted from model-builder for DcisionAI platform integration
"""

import asyncio
import json
import logging
import numpy as np
import pandas as pd
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

from .llm_adapter import LLMManager, LLMRequest
from .interfaces import (
    ParsedProblem, OptimizationProblemType, DecisionVariable, 
    Constraint, ObjectiveFunction, DatasetRegistry, Dataset, ProblemType
)
from .exceptions import DataIntegrationError
from .external_connectors import (
    ExternalDataManager, ExternalDataResult, merge_external_with_synthetic,
    calculate_portfolio_metrics
)


class DataQuality(Enum):
    """Data quality levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SIMULATED = "simulated"


@dataclass
class DataRequirements:
    """Specification of required data for optimization problem"""
    required_parameters: List[str] = field(default_factory=list)
    optional_parameters: List[str] = field(default_factory=list)
    data_types: Dict[str, str] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    domain_context: str = ""
    problem_scale: str = "medium"  # small, medium, large
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "required_parameters": self.required_parameters,
            "optional_parameters": self.optional_parameters,
            "data_types": self.data_types,
            "constraints": self.constraints,
            "domain_context": self.domain_context,
            "problem_scale": self.problem_scale
        }


@dataclass
class ExtractedData:
    """Data extracted from user queries or existing datasets"""
    parameters: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 1.0
    source: str = "user_query"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "parameters": self.parameters,
            "constraints": self.constraints,
            "metadata": self.metadata,
            "confidence_score": self.confidence_score,
            "source": self.source
        }


@dataclass
class DataSufficiencyReport:
    """Report on data sufficiency for optimization problem"""
    is_sufficient: bool
    missing_parameters: List[str] = field(default_factory=list)
    available_parameters: List[str] = field(default_factory=list)
    quality_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    simulation_needed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "is_sufficient": self.is_sufficient,
            "missing_parameters": self.missing_parameters,
            "available_parameters": self.available_parameters,
            "quality_score": self.quality_score,
            "recommendations": self.recommendations,
            "simulation_needed": self.simulation_needed
        }


@dataclass
class SimulatedDataset:
    """Generated synthetic dataset for optimization"""
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    quality_score: float = 0.8
    simulation_notes: List[str] = field(default_factory=list)
    realistic_ranges: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    data_quality: DataQuality = DataQuality.SIMULATED
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "data": self.data,
            "metadata": self.metadata,
            "quality_score": self.quality_score,
            "simulation_notes": self.simulation_notes,
            "realistic_ranges": self.realistic_ranges,
            "data_quality": self.data_quality.value
        }


class DomainDataGenerator:
    """Domain-specific data generation strategies"""
    
    def __init__(self, llm_manager: LLMManager):
        self.llm_manager = llm_manager
        self.logger = logging.getLogger(__name__)
        
        # Initialize domain-specific templates
        self._domain_templates = self._initialize_domain_templates()
        self._realistic_ranges = self._initialize_realistic_ranges()
    
    def _initialize_domain_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize domain-specific data generation templates"""
        return {
            "supply_chain": {
                "parameters": ["demand", "supply_capacity", "transportation_cost", "holding_cost", "shortage_cost"],
                "constraints": {"demand": (10, 1000), "capacity": (50, 2000), "cost": (0.1, 50.0)},
                "relationships": ["demand_seasonality", "capacity_utilization", "cost_distance_correlation"],
                "time_patterns": ["seasonal", "trend", "cyclical"]
            },
            "scheduling": {
                "parameters": ["processing_time", "setup_time", "due_date", "priority", "resource_requirement"],
                "constraints": {"time": (0.5, 24.0), "priority": (1, 10), "resources": (1, 5)},
                "relationships": ["time_complexity", "resource_conflicts", "precedence_constraints"],
                "time_patterns": ["working_hours", "shift_patterns", "deadline_pressure"]
            },
            "finance": {
                "parameters": ["expected_return", "risk", "correlation", "liquidity", "transaction_cost"],
                "constraints": {"return": (-0.2, 0.3), "risk": (0.01, 0.5), "correlation": (-1.0, 1.0)},
                "relationships": ["risk_return_tradeoff", "correlation_structure", "market_conditions"],
                "time_patterns": ["market_cycles", "volatility_clustering", "mean_reversion"]
            },
            "manufacturing": {
                "parameters": ["production_rate", "quality_rate", "machine_capacity", "labor_hours", "material_cost"],
                "constraints": {"rate": (1, 100), "quality": (0.8, 0.99), "capacity": (10, 500)},
                "relationships": ["quality_speed_tradeoff", "capacity_utilization", "learning_curves"],
                "time_patterns": ["production_cycles", "maintenance_schedules", "demand_fluctuation"]
            },
            "logistics": {
                "parameters": ["distance", "travel_time", "vehicle_capacity", "fuel_cost", "delivery_window"],
                "constraints": {"distance": (1, 500), "time": (0.1, 8.0), "capacity": (100, 5000)},
                "relationships": ["distance_time_correlation", "capacity_efficiency", "route_optimization"],
                "time_patterns": ["traffic_patterns", "delivery_schedules", "seasonal_demand"]
            },
            "energy": {
                "parameters": ["generation_capacity", "demand_load", "transmission_loss", "fuel_cost", "emission_factor"],
                "constraints": {"capacity": (10, 1000), "demand": (50, 800), "loss": (0.02, 0.15)},
                "relationships": ["load_following", "renewable_variability", "grid_stability"],
                "time_patterns": ["daily_load_curve", "seasonal_patterns", "renewable_intermittency"]
            }
        }
    
    def _initialize_realistic_ranges(self) -> Dict[str, Dict[str, Tuple[float, float]]]:
        """Initialize realistic value ranges for different domains"""
        return {
            "supply_chain": {
                "demand_units": (10, 10000),
                "cost_per_unit": (0.1, 100.0),
                "capacity_units": (50, 20000),
                "lead_time_days": (1, 30),
                "service_level": (0.85, 0.99)
            },
            "scheduling": {
                "processing_hours": (0.1, 24.0),
                "setup_minutes": (5, 120),
                "priority_score": (1, 10),
                "resource_count": (1, 20),
                "efficiency_rate": (0.7, 0.95)
            },
            "finance": {
                "annual_return": (-0.3, 0.4),
                "volatility": (0.05, 0.8),
                "correlation": (-0.9, 0.9),
                "liquidity_ratio": (0.1, 1.0),
                "expense_ratio": (0.001, 0.02)
            },
            "manufacturing": {
                "production_rate": (1, 1000),
                "defect_rate": (0.001, 0.1),
                "machine_hours": (8, 24),
                "material_cost": (0.5, 500.0),
                "labor_rate": (15, 100)
            },
            "logistics": {
                "distance_km": (1, 2000),
                "speed_kmh": (30, 120),
                "vehicle_capacity": (100, 40000),
                "fuel_cost": (1.0, 3.0),
                "delivery_hours": (1, 48)
            },
            "energy": {
                "capacity_mw": (1, 2000),
                "demand_mw": (10, 1500),
                "efficiency": (0.3, 0.95),
                "fuel_cost": (20, 200),
                "emission_rate": (0.1, 1.2)
            }
        }
    
    async def generate_supply_chain_data(self, requirements: DataRequirements) -> Dict[str, Any]:
        """Generate realistic supply chain optimization data"""
        
        try:
            template = self._domain_templates["supply_chain"]
            ranges = self._realistic_ranges["supply_chain"]
            
            # Determine problem scale
            scale_multipliers = {"small": 0.3, "medium": 1.0, "large": 3.0}
            scale = scale_multipliers.get(requirements.problem_scale, 1.0)
            
            # Generate base parameters
            num_products = max(2, int(5 * scale))
            num_suppliers = max(2, int(3 * scale))
            num_warehouses = max(1, int(2 * scale))
            num_customers = max(3, int(10 * scale))
            
            data = {
                "products": [f"Product_{i+1}" for i in range(num_products)],
                "suppliers": [f"Supplier_{i+1}" for i in range(num_suppliers)],
                "warehouses": [f"Warehouse_{i+1}" for i in range(num_warehouses)],
                "customers": [f"Customer_{i+1}" for i in range(num_customers)]
            }
            
            # Generate demand data with seasonality
            demand_data = []
            for product in data["products"]:
                for customer in data["customers"]:
                    base_demand = np.random.uniform(*ranges["demand_units"])
                    seasonal_factor = 1 + 0.3 * np.sin(np.random.uniform(0, 2*np.pi))
                    demand = base_demand * seasonal_factor * scale
                    
                    demand_data.append({
                        "product": product,
                        "customer": customer,
                        "demand": round(demand, 2),
                        "demand_variance": round(demand * 0.2, 2)
                    })
            
            data["demand"] = demand_data
            
            # Generate supply capacity
            supply_data = []
            for product in data["products"]:
                for supplier in data["suppliers"]:
                    capacity = np.random.uniform(*ranges["capacity_units"]) * scale
                    cost = np.random.uniform(*ranges["cost_per_unit"])
                    
                    supply_data.append({
                        "product": product,
                        "supplier": supplier,
                        "capacity": round(capacity, 2),
                        "unit_cost": round(cost, 2),
                        "lead_time": np.random.randint(1, 15)
                    })
            
            data["supply"] = supply_data
            
            # Generate transportation costs (distance-based)
            transport_data = []
            locations = data["suppliers"] + data["warehouses"] + data["customers"]
            
            for i, origin in enumerate(locations):
                for j, destination in enumerate(locations):
                    if i != j:
                        # Simulate realistic distance-based costs
                        distance = np.random.uniform(10, 500)
                        cost_per_km = np.random.uniform(0.5, 2.0)
                        transport_cost = distance * cost_per_km
                        
                        transport_data.append({
                            "origin": origin,
                            "destination": destination,
                            "distance_km": round(distance, 1),
                            "transport_cost": round(transport_cost, 2),
                            "transit_time": round(distance / 60, 1)  # Assume 60 km/h average
                        })
            
            data["transportation"] = transport_data
            
            # Generate inventory costs
            inventory_data = []
            for product in data["products"]:
                for warehouse in data["warehouses"]:
                    holding_cost = np.random.uniform(0.1, 5.0)
                    shortage_cost = holding_cost * np.random.uniform(5, 20)  # Shortage more expensive
                    
                    inventory_data.append({
                        "product": product,
                        "warehouse": warehouse,
                        "holding_cost_per_unit": round(holding_cost, 2),
                        "shortage_cost_per_unit": round(shortage_cost, 2),
                        "max_capacity": round(np.random.uniform(100, 2000) * scale, 2)
                    })
            
            data["inventory"] = inventory_data
            
            return data
            
        except Exception as e:
            self.logger.error(f"Supply chain data generation failed: {e}")
            raise DataIntegrationError(f"Failed to generate supply chain data: {e}")
    
    async def generate_scheduling_data(self, requirements: DataRequirements) -> Dict[str, Any]:
        """Generate realistic scheduling optimization data"""
        
        try:
            template = self._domain_templates["scheduling"]
            ranges = self._realistic_ranges["scheduling"]
            
            scale_multipliers = {"small": 0.5, "medium": 1.0, "large": 2.0}
            scale = scale_multipliers.get(requirements.problem_scale, 1.0)
            
            # Generate jobs and resources
            num_jobs = max(5, int(20 * scale))
            num_machines = max(2, int(5 * scale))
            num_workers = max(3, int(8 * scale))
            
            data = {
                "jobs": [f"Job_{i+1}" for i in range(num_jobs)],
                "machines": [f"Machine_{i+1}" for i in range(num_machines)],
                "workers": [f"Worker_{i+1}" for i in range(num_workers)]
            }
            
            # Generate job processing times
            job_data = []
            for job in data["jobs"]:
                # Base processing time with complexity factor
                complexity = np.random.uniform(0.5, 2.0)
                base_time = np.random.uniform(*ranges["processing_hours"]) * complexity
                
                # Due date (processing time + buffer)
                buffer_factor = np.random.uniform(1.5, 3.0)
                due_date = base_time * buffer_factor
                
                # Priority (higher number = higher priority)
                priority = np.random.randint(*ranges["priority_score"])
                
                job_data.append({
                    "job": job,
                    "processing_time": round(base_time, 2),
                    "setup_time": round(np.random.uniform(0.1, 2.0), 2),
                    "due_date": round(due_date, 2),
                    "priority": priority,
                    "complexity_factor": round(complexity, 2)
                })
            
            data["jobs_info"] = job_data
            
            # Generate machine capabilities
            machine_data = []
            for machine in data["machines"]:
                # Each machine can handle different job types with different efficiencies
                for job in data["jobs"]:
                    can_process = np.random.choice([True, False], p=[0.7, 0.3])  # 70% compatibility
                    if can_process:
                        efficiency = np.random.uniform(0.7, 1.0)
                        machine_data.append({
                            "machine": machine,
                            "job": job,
                            "efficiency": round(efficiency, 3),
                            "processing_cost": round(np.random.uniform(10, 50), 2)
                        })
            
            data["machine_capabilities"] = machine_data
            
            # Generate worker skills
            worker_data = []
            skill_types = ["basic", "intermediate", "advanced", "specialist"]
            
            for worker in data["workers"]:
                # Each worker has different skill levels
                skill_level = np.random.choice(skill_types, p=[0.3, 0.4, 0.2, 0.1])
                hourly_rate = {"basic": 20, "intermediate": 30, "advanced": 45, "specialist": 60}[skill_level]
                
                # Worker availability (shift patterns)
                availability_hours = np.random.uniform(6, 10)  # Hours per day
                
                worker_data.append({
                    "worker": worker,
                    "skill_level": skill_level,
                    "hourly_rate": hourly_rate + np.random.uniform(-5, 5),
                    "availability_hours": round(availability_hours, 1),
                    "efficiency": round(np.random.uniform(0.8, 1.0), 3)
                })
            
            data["workers_info"] = worker_data
            
            # Generate precedence constraints (some jobs must be done before others)
            precedence_data = []
            for i, job1 in enumerate(data["jobs"]):
                # 30% chance of having a precedence constraint
                if np.random.random() < 0.3 and i < len(data["jobs"]) - 1:
                    job2 = data["jobs"][i + 1]
                    precedence_data.append({
                        "predecessor": job1,
                        "successor": job2,
                        "min_delay": round(np.random.uniform(0, 2), 2)
                    })
            
            data["precedence_constraints"] = precedence_data
            
            return data
            
        except Exception as e:
            self.logger.error(f"Scheduling data generation failed: {e}")
            raise DataIntegrationError(f"Failed to generate scheduling data: {e}")
    
    async def generate_financial_data(self, requirements: DataRequirements) -> Dict[str, Any]:
        """Generate realistic financial optimization data"""
        
        try:
            ranges = self._realistic_ranges["finance"]
            
            scale_multipliers = {"small": 0.5, "medium": 1.0, "large": 2.0}
            scale = scale_multipliers.get(requirements.problem_scale, 1.0)
            
            # Generate assets
            num_assets = max(5, int(15 * scale))
            asset_classes = ["stocks", "bonds", "commodities", "real_estate", "alternatives"]
            
            data = {
                "assets": [f"Asset_{i+1}" for i in range(num_assets)]
            }
            
            # Generate asset characteristics
            asset_data = []
            for asset in data["assets"]:
                asset_class = np.random.choice(asset_classes)
                
                # Expected returns vary by asset class
                return_ranges = {
                    "stocks": (0.05, 0.15),
                    "bonds": (0.02, 0.06),
                    "commodities": (-0.05, 0.12),
                    "real_estate": (0.04, 0.10),
                    "alternatives": (0.03, 0.20)
                }
                
                expected_return = np.random.uniform(*return_ranges[asset_class])
                
                # Risk (volatility) generally correlates with expected return
                base_volatility = expected_return * np.random.uniform(1.5, 4.0)
                volatility = max(0.01, min(0.8, base_volatility))
                
                asset_data.append({
                    "asset": asset,
                    "asset_class": asset_class,
                    "expected_return": round(expected_return, 4),
                    "volatility": round(volatility, 4),
                    "liquidity": round(np.random.uniform(*ranges["liquidity_ratio"]), 3),
                    "expense_ratio": round(np.random.uniform(*ranges["expense_ratio"]), 4),
                    "min_investment": round(np.random.uniform(100, 10000), 2)
                })
            
            data["assets_info"] = asset_data
            
            # Generate correlation matrix
            correlation_matrix = []
            for i, asset1 in enumerate(data["assets"]):
                for j, asset2 in enumerate(data["assets"]):
                    if i == j:
                        correlation = 1.0
                    elif i < j:
                        # Generate realistic correlations based on asset classes
                        class1 = asset_data[i]["asset_class"]
                        class2 = asset_data[j]["asset_class"]
                        
                        if class1 == class2:
                            correlation = np.random.uniform(0.3, 0.8)  # Same class, higher correlation
                        else:
                            correlation = np.random.uniform(-0.3, 0.5)  # Different class, lower correlation
                    else:
                        # Use symmetric correlation
                        correlation = next(
                            item["correlation"] for item in correlation_matrix 
                            if item["asset1"] == asset2 and item["asset2"] == asset1
                        )
                    
                    correlation_matrix.append({
                        "asset1": asset1,
                        "asset2": asset2,
                        "correlation": round(correlation, 4)
                    })
            
            data["correlations"] = correlation_matrix
            
            # Generate market scenarios
            scenarios = ["bull_market", "bear_market", "normal_market", "high_volatility", "recession"]
            scenario_data = []
            
            for scenario in scenarios:
                scenario_multipliers = {
                    "bull_market": {"return": 1.3, "volatility": 0.8},
                    "bear_market": {"return": 0.5, "volatility": 1.5},
                    "normal_market": {"return": 1.0, "volatility": 1.0},
                    "high_volatility": {"return": 0.9, "volatility": 2.0},
                    "recession": {"return": 0.3, "volatility": 1.8}
                }
                
                multiplier = scenario_multipliers[scenario]
                probability = np.random.uniform(0.1, 0.3)
                
                scenario_data.append({
                    "scenario": scenario,
                    "probability": round(probability, 3),
                    "return_multiplier": multiplier["return"],
                    "volatility_multiplier": multiplier["volatility"]
                })
            
            # Normalize probabilities
            total_prob = sum(s["probability"] for s in scenario_data)
            for scenario in scenario_data:
                scenario["probability"] = round(scenario["probability"] / total_prob, 3)
            
            data["market_scenarios"] = scenario_data
            
            return data
            
        except Exception as e:
            self.logger.error(f"Financial data generation failed: {e}")
            raise DataIntegrationError(f"Failed to generate financial data: {e}")
    
    async def generate_manufacturing_data(self, requirements: DataRequirements) -> Dict[str, Any]:
        """Generate realistic manufacturing optimization data"""
        
        try:
            ranges = self._realistic_ranges["manufacturing"]
            
            scale_multipliers = {"small": 0.4, "medium": 1.0, "large": 2.5}
            scale = scale_multipliers.get(requirements.problem_scale, 1.0)
            
            # Generate products and production lines
            num_products = max(3, int(8 * scale))
            num_lines = max(2, int(4 * scale))
            num_materials = max(5, int(12 * scale))
            
            data = {
                "products": [f"Product_{i+1}" for i in range(num_products)],
                "production_lines": [f"Line_{i+1}" for i in range(num_lines)],
                "materials": [f"Material_{i+1}" for i in range(num_materials)]
            }
            
            # Generate product specifications
            product_data = []
            for product in data["products"]:
                # Production characteristics
                production_rate = np.random.uniform(*ranges["production_rate"]) * scale
                quality_rate = np.random.uniform(*ranges["defect_rate"])
                
                # Profit margins
                selling_price = np.random.uniform(10, 500)
                production_cost = selling_price * np.random.uniform(0.4, 0.8)
                profit_margin = selling_price - production_cost
                
                product_data.append({
                    "product": product,
                    "max_production_rate": round(production_rate, 2),
                    "defect_rate": round(quality_rate, 4),
                    "selling_price": round(selling_price, 2),
                    "production_cost": round(production_cost, 2),
                    "profit_margin": round(profit_margin, 2),
                    "setup_time": round(np.random.uniform(0.5, 4.0), 2)
                })
            
            data["products_info"] = product_data
            
            # Generate production line capabilities
            line_data = []
            for line in data["production_lines"]:
                # Each line has different capabilities and costs
                capacity = np.random.uniform(50, 500) * scale
                efficiency = np.random.uniform(0.7, 0.95)
                operating_cost = np.random.uniform(50, 200)
                
                line_data.append({
                    "production_line": line,
                    "capacity_per_hour": round(capacity, 2),
                    "efficiency": round(efficiency, 3),
                    "operating_cost_per_hour": round(operating_cost, 2),
                    "maintenance_hours_per_week": round(np.random.uniform(2, 8), 1),
                    "available_hours_per_day": round(np.random.uniform(16, 24), 1)
                })
            
            data["production_lines_info"] = line_data
            
            # Generate material requirements (Bill of Materials)
            bom_data = []
            for product in data["products"]:
                # Each product requires 2-5 materials
                num_materials_needed = np.random.randint(2, min(6, len(data["materials"]) + 1))
                required_materials = np.random.choice(
                    data["materials"], 
                    size=num_materials_needed, 
                    replace=False
                )
                
                for material in required_materials:
                    quantity_needed = np.random.uniform(0.1, 5.0)
                    bom_data.append({
                        "product": product,
                        "material": material,
                        "quantity_per_unit": round(quantity_needed, 3)
                    })
            
            data["bill_of_materials"] = bom_data
            
            # Generate material costs and availability
            material_data = []
            for material in data["materials"]:
                unit_cost = np.random.uniform(*ranges["material_cost"])
                
                # Supplier information
                lead_time = np.random.randint(1, 14)
                min_order_qty = np.random.uniform(10, 100)
                max_available = np.random.uniform(1000, 10000) * scale
                
                material_data.append({
                    "material": material,
                    "unit_cost": round(unit_cost, 2),
                    "lead_time_days": lead_time,
                    "min_order_quantity": round(min_order_qty, 2),
                    "max_available_per_period": round(max_available, 2),
                    "storage_cost_per_unit": round(unit_cost * 0.02, 3)  # 2% of unit cost
                })
            
            data["materials_info"] = material_data
            
            # Generate demand forecast
            demand_data = []
            for product in data["products"]:
                # Generate demand for next 12 periods (months)
                base_demand = np.random.uniform(100, 2000) * scale
                
                for period in range(1, 13):
                    # Add seasonality and trend
                    seasonal_factor = 1 + 0.2 * np.sin(2 * np.pi * period / 12)
                    trend_factor = 1 + 0.01 * period  # 1% growth per period
                    noise_factor = 1 + np.random.uniform(-0.1, 0.1)
                    
                    demand = base_demand * seasonal_factor * trend_factor * noise_factor
                    
                    demand_data.append({
                        "product": product,
                        "period": period,
                        "forecasted_demand": round(demand, 2),
                        "demand_uncertainty": round(demand * 0.15, 2)  # 15% uncertainty
                    })
            
            data["demand_forecast"] = demand_data
            
            return data
            
        except Exception as e:
            self.logger.error(f"Manufacturing data generation failed: {e}")
            raise DataIntegrationError(f"Failed to generate manufacturing data: {e}")


class DataSimulator:
    """Generates realistic datasets for optimization problems when user data is insufficient"""
    
    def __init__(self, llm_manager: LLMManager, dataset_registry: Optional[DatasetRegistry] = None):
        """Initialize data simulator with LLM manager and optional dataset registry"""
        self.llm_manager = llm_manager
        self.dataset_registry = dataset_registry
        self.domain_generator = DomainDataGenerator(llm_manager)
        self.external_data_manager = ExternalDataManager()
        self.logger = logging.getLogger(__name__)
        
        # Initialize data extraction templates
        self._extraction_templates = self._initialize_extraction_templates()
    
    def _initialize_extraction_templates(self) -> Dict[str, str]:
        """Initialize LLM templates for data extraction from queries"""
        return {
            "parameter_extraction": """
You are an expert data analyst specializing in optimization problems. Extract numerical parameters and data from this problem description.

Problem Description:
{prompt}

Extract any numerical values, ranges, constraints, or data mentioned in the problem. Look for:
- Costs, prices, budgets
- Capacities, limits, maximums
- Demands, requirements, minimums  
- Times, durations, deadlines
- Quantities, volumes, amounts
- Rates, percentages, ratios

Format your response as JSON:
{{
    "parameters": {{
        "parameter_name": {{
            "value": number_or_range,
            "unit": "unit_if_specified",
            "description": "what this parameter represents",
            "confidence": 0.0_to_1.0
        }}
    }},
    "constraints": {{
        "constraint_name": {{
            "type": "upper_bound|lower_bound|equality|range",
            "value": number_or_range,
            "description": "constraint description"
        }}
    }},
    "context": {{
        "domain": "supply_chain|scheduling|finance|manufacturing|logistics|energy|other",
        "scale": "small|medium|large",
        "time_horizon": "short|medium|long"
    }}
}}

Be precise with numerical extraction and indicate confidence levels.
""",
            
            "data_gap_analysis": """
You are an optimization expert analyzing data requirements. Given this optimization problem and available data, identify what additional data is needed.

Problem Description:
{prompt}

Available Data:
{available_data}

Analyze what data is missing for a complete optimization model. Consider:
- Decision variables and their bounds
- Constraint parameters and right-hand sides
- Objective function coefficients
- Problem-specific parameters (demand, capacity, costs, etc.)

Format your response as JSON:
{{
    "missing_parameters": [
        {{
            "name": "parameter_name",
            "type": "cost|demand|capacity|time|resource|other",
            "importance": "critical|important|optional",
            "description": "why this parameter is needed",
            "typical_range": "typical values or range",
            "simulation_difficulty": "easy|medium|hard"
        }}
    ],
    "data_quality_assessment": {{
        "completeness": 0.0_to_1.0,
        "reliability": 0.0_to_1.0,
        "recommendations": ["list of recommendations"]
    }},
    "simulation_strategy": {{
        "approach": "domain_specific|statistical|ml_based|hybrid",
        "complexity": "simple|moderate|complex",
        "confidence": 0.0_to_1.0
    }}
}}

Focus on parameters essential for optimization model construction.
"""
        }
    
    async def analyze_data_requirements(self, parsed_problem: ParsedProblem, 
                                      user_data: Optional[Dict[str, Any]] = None) -> DataRequirements:
        """Analyze data requirements for optimization problem"""
        
        try:
            self.logger.info(f"Analyzing data requirements for problem {parsed_problem.problem_id}")
            
            # Extract parameters from problem description using LLM
            extracted_data = await self.extract_data_from_query(parsed_problem.original_prompt)
            
            # Determine domain context
            domain_context = self._determine_domain_context(parsed_problem, extracted_data)
            
            # Identify required parameters based on problem type and domain
            required_params = self._identify_required_parameters(parsed_problem, domain_context)
            optional_params = self._identify_optional_parameters(parsed_problem, domain_context)
            
            # Determine problem scale
            problem_scale = self._determine_problem_scale(parsed_problem, extracted_data)
            
            # Create data requirements
            requirements = DataRequirements(
                required_parameters=required_params,
                optional_parameters=optional_params,
                data_types=self._determine_data_types(required_params + optional_params),
                constraints=extracted_data.constraints,
                domain_context=domain_context,
                problem_scale=problem_scale
            )
            
            self.logger.info(f"Identified {len(required_params)} required and {len(optional_params)} optional parameters")
            return requirements
            
        except Exception as e:
            self.logger.error(f"Data requirements analysis failed: {e}")
            raise DataIntegrationError(f"Failed to analyze data requirements: {e}")
    
    async def generate_synthetic_data(self, requirements: DataRequirements, 
                                    domain: str, 
                                    use_external_data: bool = True) -> SimulatedDataset:
        """Generate synthetic dataset based on requirements and domain"""
        
        try:
            self.logger.info(f"Generating synthetic data for domain: {domain}")
            
            # Generate domain-specific data
            if domain == "supply_chain":
                data = await self.domain_generator.generate_supply_chain_data(requirements)
            elif domain == "scheduling":
                data = await self.domain_generator.generate_scheduling_data(requirements)
            elif domain == "finance":
                data = await self.domain_generator.generate_financial_data(requirements)
            elif domain == "manufacturing":
                data = await self.domain_generator.generate_manufacturing_data(requirements)
            else:
                # Generic data generation
                data = await self._generate_generic_data(requirements)
            
            # Enhance with external data if available and requested
            external_data_used = False
            if use_external_data and self.external_data_manager.is_available():
                try:
                    enhanced_data = await self._enhance_with_external_data(data, domain, requirements)
                    if enhanced_data:
                        data = enhanced_data
                        external_data_used = True
                        self.logger.info("Enhanced synthetic data with external sources")
                except Exception as e:
                    self.logger.warning(f"Failed to enhance with external data: {e}")
            
            # Calculate realistic ranges
            realistic_ranges = self._calculate_realistic_ranges(data)
            
            # Generate metadata
            metadata = {
                "domain": domain,
                "generation_method": "domain_specific_with_external" if external_data_used else "domain_specific",
                "external_data_used": external_data_used,
                "external_sources": list(self.external_data_manager.get_available_sources().keys()) if external_data_used else [],
                "requirements": requirements.to_dict(),
                "generated_at": datetime.now().isoformat(),
                "data_points": self._count_data_points(data),
                "parameters_covered": list(data.keys())
            }
            
            # Create simulation notes
            simulation_notes = [
                f"Generated {domain} optimization dataset",
                f"Problem scale: {requirements.problem_scale}",
                f"Data points generated: {self._count_data_points(data)}",
                "Data includes realistic relationships and constraints",
                "Values are within typical industry ranges"
            ]
            
            if external_data_used:
                simulation_notes.append("Enhanced with real-world external data sources")
                simulation_notes.append(f"External sources: {', '.join(metadata['external_sources'])}")
            
            # Calculate quality score based on completeness and realism
            quality_score = self._calculate_quality_score(data, requirements)
            if external_data_used:
                quality_score = min(1.0, quality_score + 0.1)  # Bonus for external data
            
            simulated_dataset = SimulatedDataset(
                data=data,
                metadata=metadata,
                quality_score=quality_score,
                simulation_notes=simulation_notes,
                realistic_ranges=realistic_ranges,
                data_quality=DataQuality.HIGH if external_data_used else DataQuality.SIMULATED
            )
            
            self.logger.info(f"Generated synthetic dataset with quality score: {quality_score:.2f}")
            return simulated_dataset
            
        except Exception as e:
            self.logger.error(f"Synthetic data generation failed: {e}")
            raise DataIntegrationError(f"Failed to generate synthetic data: {e}")
    
    async def extract_data_from_query(self, prompt: str) -> ExtractedData:
        """Extract data from user queries using LLM"""
        
        try:
            request = LLMRequest(
                prompt=self._extraction_templates["parameter_extraction"].format(prompt=prompt),
                max_tokens=1000,
                temperature=0.2,
                metadata={"task": "parameter_extraction"}
            )
            
            response = await self.llm_manager.generate(request)
            
            # Parse JSON response
            extracted_json = self._parse_json_response(response.content)
            
            if extracted_json:
                return ExtractedData(
                    parameters=extracted_json.get("parameters", {}),
                    constraints=extracted_json.get("constraints", {}),
                    metadata=extracted_json.get("context", {}),
                    confidence_score=self._calculate_extraction_confidence(extracted_json),
                    source="user_query"
                )
            else:
                # Fallback extraction using pattern matching
                return self._fallback_data_extraction(prompt)
                
        except Exception as e:
            self.logger.error(f"Data extraction from query failed: {e}")
            return self._fallback_data_extraction(prompt)
    
    def validate_data_sufficiency(self, data: Dict[str, Any], 
                                requirements: DataRequirements) -> DataSufficiencyReport:
        """Validate if available data is sufficient for optimization problem"""
        
        try:
            # Check parameter coverage
            available_params = list(data.keys()) if data else []
            missing_params = [
                param for param in requirements.required_parameters 
                if param not in available_params
            ]
            
            # Calculate quality score
            coverage_score = 1.0 - (len(missing_params) / max(1, len(requirements.required_parameters)))
            
            # Check data quality
            quality_issues = []
            if data:
                quality_issues = self._assess_data_quality(data)
            
            quality_penalty = len(quality_issues) * 0.1
            quality_score = max(0.0, coverage_score - quality_penalty)
            
            # Determine if sufficient
            is_sufficient = (
                len(missing_params) == 0 and 
                quality_score >= 0.7 and
                len(quality_issues) <= 2
            )
            
            # Generate recommendations
            recommendations = []
            if missing_params:
                recommendations.append(f"Missing critical parameters: {', '.join(missing_params)}")
            if quality_issues:
                recommendations.extend(quality_issues)
            if not is_sufficient:
                recommendations.append("Consider data simulation to fill gaps")
            
            return DataSufficiencyReport(
                is_sufficient=is_sufficient,
                missing_parameters=missing_params,
                available_parameters=available_params,
                quality_score=quality_score,
                recommendations=recommendations,
                simulation_needed=not is_sufficient
            )
            
        except Exception as e:
            self.logger.error(f"Data sufficiency validation failed: {e}")
            return DataSufficiencyReport(
                is_sufficient=False,
                missing_parameters=requirements.required_parameters,
                available_parameters=[],
                quality_score=0.0,
                recommendations=[f"Validation error: {e}"],
                simulation_needed=True
            )
    
    def _determine_domain_context(self, problem: ParsedProblem, extracted_data: ExtractedData) -> str:
        """Determine domain context from problem and extracted data"""
        
        # Check metadata first if extracted_data exists
        if extracted_data and extracted_data.metadata.get("domain"):
            return extracted_data.metadata["domain"]
        
        # Use problem type mapping
        domain_mapping = {
            OptimizationProblemType.FACILITY_LOCATION: "supply_chain",
            OptimizationProblemType.ROUTING: "logistics", 
            OptimizationProblemType.SCHEDULING: "scheduling",
            OptimizationProblemType.PORTFOLIO_OPTIMIZATION: "finance",
            OptimizationProblemType.KNAPSACK: "resource_allocation"
        }
        
        if problem.problem_type in domain_mapping:
            return domain_mapping[problem.problem_type]
        
        # Fallback to keyword analysis
        prompt_lower = problem.original_prompt.lower()
        domain_keywords = {
            "supply_chain": ["supply", "inventory", "warehouse", "distribution", "logistics"],
            "scheduling": ["schedule", "time", "shift", "appointment", "resource"],
            "finance": ["portfolio", "investment", "return", "risk", "asset"],
            "manufacturing": ["production", "manufacturing", "assembly", "quality"],
            "energy": ["energy", "power", "generation", "grid", "renewable"]
        }
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                return domain
        
        return "general"
    
    def _identify_required_parameters(self, problem: ParsedProblem, domain: str) -> List[str]:
        """Identify required parameters based on problem type and domain"""
        
        base_params = ["objective_coefficients", "constraint_coefficients", "constraint_bounds"]
        
        domain_params = {
            "supply_chain": ["demand", "supply_capacity", "transportation_cost", "inventory_cost"],
            "scheduling": ["processing_time", "resource_capacity", "due_dates", "setup_time"],
            "finance": ["expected_returns", "risk_measures", "correlations", "transaction_costs"],
            "manufacturing": ["production_rates", "material_costs", "capacity_limits", "demand_forecast"],
            "logistics": ["distances", "vehicle_capacity", "delivery_windows", "fuel_costs"],
            "energy": ["generation_capacity", "demand_load", "fuel_costs", "transmission_limits"]
        }
        
        return base_params + domain_params.get(domain, [])
    
    def _identify_optional_parameters(self, problem: ParsedProblem, domain: str) -> List[str]:
        """Identify optional parameters that enhance the model"""
        
        domain_optional = {
            "supply_chain": ["lead_times", "service_levels", "seasonal_factors", "supplier_reliability"],
            "scheduling": ["worker_skills", "machine_efficiency", "maintenance_windows", "overtime_costs"],
            "finance": ["market_scenarios", "liquidity_constraints", "regulatory_limits", "tax_implications"],
            "manufacturing": ["quality_rates", "learning_curves", "maintenance_costs", "environmental_limits"],
            "logistics": ["traffic_patterns", "weather_factors", "driver_availability", "route_preferences"],
            "energy": ["renewable_variability", "storage_capacity", "grid_stability", "emission_limits"]
        }
        
        return domain_optional.get(domain, ["uncertainty_parameters", "performance_metrics"])
    
    def _determine_data_types(self, parameters: List[str]) -> Dict[str, str]:
        """Determine data types for parameters"""
        
        type_mapping = {
            "cost": "float", "price": "float", "rate": "float",
            "time": "float", "duration": "float", "delay": "float",
            "capacity": "float", "demand": "float", "quantity": "float",
            "distance": "float", "weight": "float", "volume": "float",
            "probability": "float", "percentage": "float", "ratio": "float",
            "count": "integer", "number": "integer", "index": "integer",
            "binary": "boolean", "flag": "boolean", "indicator": "boolean",
            "name": "string", "id": "string", "type": "string"
        }
        
        data_types = {}
        for param in parameters:
            param_lower = param.lower()
            for keyword, dtype in type_mapping.items():
                if keyword in param_lower:
                    data_types[param] = dtype
                    break
            else:
                data_types[param] = "float"  # Default to float
        
        return data_types
    
    def _determine_problem_scale(self, problem: ParsedProblem, extracted_data: ExtractedData) -> str:
        """Determine problem scale from problem characteristics"""
        
        # Check metadata first
        if extracted_data.metadata.get("scale"):
            return extracted_data.metadata["scale"]
        
        # Estimate scale from problem complexity
        num_variables = len(problem.variables)
        num_constraints = len(problem.constraints)
        
        if num_variables <= 10 and num_constraints <= 10:
            return "small"
        elif num_variables <= 50 and num_constraints <= 50:
            return "medium"
        else:
            return "large"
    
    async def _generate_generic_data(self, requirements: DataRequirements) -> Dict[str, Any]:
        """Generate generic optimization data when domain-specific generation is not available"""
        
        data = {}
        
        # Generate data for required parameters
        for param in requirements.required_parameters:
            if param in requirements.data_types:
                dtype = requirements.data_types[param]
                if dtype == "float":
                    data[param] = np.random.uniform(1, 100, size=10).tolist()
                elif dtype == "integer":
                    data[param] = np.random.randint(1, 100, size=10).tolist()
                elif dtype == "boolean":
                    data[param] = np.random.choice([True, False], size=10).tolist()
                else:
                    data[param] = [f"{param}_{i}" for i in range(10)]
        
        return data
    
    def _calculate_realistic_ranges(self, data: Dict[str, Any]) -> Dict[str, Tuple[float, float]]:
        """Calculate realistic ranges from generated data"""
        
        ranges = {}
        
        for key, values in data.items():
            if isinstance(values, list) and values:
                # Handle nested data structures
                if isinstance(values[0], dict):
                    # Extract numeric values from dictionaries
                    for subkey in values[0].keys():
                        subvalues = [item.get(subkey) for item in values if isinstance(item.get(subkey), (int, float))]
                        if subvalues:
                            ranges[f"{key}_{subkey}"] = (min(subvalues), max(subvalues))
                elif isinstance(values[0], (int, float)):
                    ranges[key] = (min(values), max(values))
        
        return ranges
    
    def _count_data_points(self, data: Dict[str, Any]) -> int:
        """Count total data points in generated dataset"""
        
        total_points = 0
        
        for values in data.values():
            if isinstance(values, list):
                total_points += len(values)
            elif isinstance(values, dict):
                total_points += len(values)
            else:
                total_points += 1
        
        return total_points
    
    def _calculate_quality_score(self, data: Dict[str, Any], requirements: DataRequirements) -> float:
        """Calculate quality score for generated data"""
        
        # Base score for having data
        base_score = 0.7
        
        # Bonus for parameter coverage
        covered_params = len([p for p in requirements.required_parameters if p in str(data)])
        total_params = len(requirements.required_parameters)
        coverage_bonus = 0.2 * (covered_params / max(1, total_params))
        
        # Bonus for data volume
        data_points = self._count_data_points(data)
        volume_bonus = min(0.1, data_points / 1000)  # Up to 0.1 bonus for 1000+ data points
        
        return min(1.0, base_score + coverage_bonus + volume_bonus)
    
    def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from LLM response with error handling"""
        
        try:
            # Try to find JSON in response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
        except json.JSONDecodeError as e:
            self.logger.warning(f"JSON parsing failed: {e}")
        
        return None
    
    def _calculate_extraction_confidence(self, extracted_json: Dict[str, Any]) -> float:
        """Calculate confidence score for extracted data"""
        
        # Base confidence
        confidence = 0.5
        
        # Bonus for having parameters
        if extracted_json.get("parameters"):
            confidence += 0.2
        
        # Bonus for having constraints
        if extracted_json.get("constraints"):
            confidence += 0.2
        
        # Bonus for having context
        if extracted_json.get("context"):
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _fallback_data_extraction(self, prompt: str) -> ExtractedData:
        """Fallback data extraction using pattern matching"""
        
        import re
        
        parameters = {}
        constraints = {}
        
        # Extract numbers with units
        number_patterns = [
            r'(\d+(?:\.\d+)?)\s*(dollars?|usd|\$)',
            r'(\d+(?:\.\d+)?)\s*(hours?|minutes?|days?)',
            r'(\d+(?:\.\d+)?)\s*(units?|items?|pieces?)',
            r'(\d+(?:\.\d+)?)\s*(percent|%)',
            r'(\d+(?:\.\d+)?)\s*(kg|pounds?|tons?)'
        ]
        
        for pattern in number_patterns:
            matches = re.findall(pattern, prompt.lower())
            for value, unit in matches:
                param_name = f"extracted_{unit}"
                parameters[param_name] = {
                    "value": float(value),
                    "unit": unit,
                    "description": f"Extracted {unit} value",
                    "confidence": 0.6
                }
        
        return ExtractedData(
            parameters=parameters,
            constraints=constraints,
            metadata={"extraction_method": "pattern_matching"},
            confidence_score=0.4,
            source="fallback_extraction"
        )
    
    def _assess_data_quality(self, data: Dict[str, Any]) -> List[str]:
        """Assess quality issues in provided data"""
        
        issues = []
        
        # Check for empty data
        if not data:
            issues.append("No data provided")
            return issues
        
        # Check for missing values
        for key, values in data.items():
            if isinstance(values, list):
                if not values:
                    issues.append(f"Empty list for parameter: {key}")
                elif None in values:
                    issues.append(f"Missing values in parameter: {key}")
        
        # Check for unrealistic values
        for key, values in data.items():
            if isinstance(values, list) and values:
                if isinstance(values[0], (int, float)):
                    if any(v < 0 for v in values if isinstance(v, (int, float))):
                        if "cost" in key.lower() or "price" in key.lower():
                            issues.append(f"Negative values in cost/price parameter: {key}")
        
        return issues
    
    async def _enhance_with_external_data(self, synthetic_data: Dict[str, Any], 
                                        domain: str, 
                                        requirements: DataRequirements) -> Optional[Dict[str, Any]]:
        """Enhance synthetic data with external data sources"""
        
        try:
            if domain == "finance":
                return await self._enhance_financial_data(synthetic_data, requirements)
            elif domain == "supply_chain":
                return await self._enhance_supply_chain_data(synthetic_data, requirements)
            elif domain == "manufacturing":
                return await self._enhance_manufacturing_data(synthetic_data, requirements)
            else:
                # For other domains, try to get economic context
                economic_data = await self.external_data_manager.get_economic_context_data()
                if economic_data:
                    synthetic_data["economic_context"] = economic_data
                    return synthetic_data
        
        except Exception as e:
            self.logger.warning(f"External data enhancement failed: {e}")
        
        return None
    
    async def _enhance_financial_data(self, synthetic_data: Dict[str, Any], 
                                    requirements: DataRequirements) -> Dict[str, Any]:
        """Enhance financial data with real market data"""
        
        try:
            # Extract asset symbols from synthetic data
            assets = synthetic_data.get("assets", [])
            
            # Use major market ETFs if no specific assets
            if not assets or len(assets) < 5:
                assets = ["SPY", "QQQ", "IWM", "VTI", "EFA", "EEM", "AGG", "TLT", "GLD", "VNQ"]
            
            # Get real market data
            market_data = await self.external_data_manager.get_market_data_for_optimization(
                symbols=assets[:10],  # Limit to 10 assets to avoid rate limits
                lookback_days=252,
                include_indices=True,
                include_sectors=True
            )
            
            # Get economic context
            economic_data = await self.external_data_manager.get_economic_context_data()
            
            # Merge with synthetic data
            enhanced_data = merge_external_with_synthetic(
                market_data.get("stocks", ExternalDataResult(data=pd.DataFrame())), 
                synthetic_data
            )
            
            # Add real correlation matrix if available
            correlation_matrix = await self.external_data_manager.get_correlation_matrix(assets[:10])
            if correlation_matrix is not None:
                # Convert correlation matrix to the format expected by optimization
                correlation_data = []
                for i, asset1 in enumerate(correlation_matrix.index):
                    for j, asset2 in enumerate(correlation_matrix.columns):
                        correlation_data.append({
                            "asset1": asset1,
                            "asset2": asset2,
                            "correlation": correlation_matrix.iloc[i, j]
                        })
                enhanced_data["real_correlations"] = correlation_data
            
            # Add real risk metrics
            risk_metrics = await self.external_data_manager.get_risk_metrics(assets[:10])
            if risk_metrics is not None:
                enhanced_data["real_risk_metrics"] = risk_metrics.to_dict("records")
            
            # Add economic indicators
            if economic_data:
                enhanced_data["economic_indicators"] = economic_data
            
            # Add market indices data
            if "indices" in market_data:
                enhanced_data["market_indices"] = market_data["indices"].to_dict()
            
            # Add sector data
            if "sectors" in market_data:
                enhanced_data["sector_data"] = market_data["sectors"].to_dict()
            
            return enhanced_data
            
        except Exception as e:
            self.logger.error(f"Financial data enhancement failed: {e}")
            raise
    
    async def _enhance_supply_chain_data(self, synthetic_data: Dict[str, Any], 
                                       requirements: DataRequirements) -> Dict[str, Any]:
        """Enhance supply chain data with economic indicators"""
        
        try:
            # Get economic context that affects supply chains
            economic_data = await self.external_data_manager.get_economic_context_data()
            
            if economic_data:
                enhanced_data = synthetic_data.copy()
                
                # Add economic indicators that affect supply chains
                if "economic_indicators" in economic_data:
                    enhanced_data["economic_factors"] = economic_data["economic_indicators"].to_dict()
                
                # Add commodity prices that affect costs
                if "commodities" in economic_data:
                    commodity_data = economic_data["commodities"].data
                    if not commodity_data.empty:
                        # Map commodities to supply chain costs
                        cost_adjustments = []
                        for _, row in commodity_data.iterrows():
                            cost_adjustments.append({
                                "commodity": row["commodity"],
                                "price": row["price"],
                                "impact_factor": self._calculate_commodity_impact(row["commodity"])
                            })
                        enhanced_data["commodity_cost_factors"] = cost_adjustments
                
                # Add forex data for international supply chains
                if "forex" in economic_data:
                    forex_data = economic_data["forex"].data
                    if not forex_data.empty:
                        # Calculate currency risk factors
                        currency_factors = []
                        for pair in forex_data["currency_pair"].unique():
                            pair_data = forex_data[forex_data["currency_pair"] == pair]
                            if not pair_data.empty:
                                volatility = pair_data["volatility"].mean()
                                currency_factors.append({
                                    "currency_pair": pair,
                                    "volatility": volatility,
                                    "risk_factor": min(1.5, 1.0 + volatility * 2)  # Convert to cost multiplier
                                })
                        enhanced_data["currency_risk_factors"] = currency_factors
                
                return enhanced_data
            
        except Exception as e:
            self.logger.error(f"Supply chain data enhancement failed: {e}")
        
        return synthetic_data
    
    async def _enhance_manufacturing_data(self, synthetic_data: Dict[str, Any], 
                                        requirements: DataRequirements) -> Dict[str, Any]:
        """Enhance manufacturing data with commodity and economic data"""
        
        try:
            # Get economic and commodity data
            economic_data = await self.external_data_manager.get_economic_context_data()
            
            if economic_data:
                enhanced_data = synthetic_data.copy()
                
                # Add commodity prices for raw materials
                if "commodities" in economic_data:
                    commodity_data = economic_data["commodities"].data
                    if not commodity_data.empty:
                        # Map commodities to material costs
                        material_cost_updates = []
                        
                        # Common manufacturing materials and their commodity mappings
                        material_mappings = {
                            "steel": "copper",  # Proxy for metal prices
                            "aluminum": "copper",
                            "plastic": "crude_oil",  # Oil-based materials
                            "rubber": "crude_oil",
                            "energy": "crude_oil"
                        }
                        
                        for material, commodity in material_mappings.items():
                            commodity_rows = commodity_data[commodity_data["commodity"] == commodity]
                            if not commodity_rows.empty:
                                latest_price = commodity_rows["price"].iloc[-1]
                                price_change = commodity_rows["monthly_return"].iloc[-1] if "monthly_return" in commodity_rows.columns else 0
                                
                                material_cost_updates.append({
                                    "material": material,
                                    "commodity_price": latest_price,
                                    "price_change": price_change,
                                    "cost_multiplier": 1.0 + price_change
                                })
                        
                        enhanced_data["material_cost_updates"] = material_cost_updates
                
                # Add economic indicators affecting manufacturing
                if "economic_indicators" in economic_data:
                    econ_data = economic_data["economic_indicators"].data
                    if not econ_data.empty:
                        # Extract relevant indicators
                        manufacturing_indicators = []
                        
                        for indicator in ["Unemployment Rate", "Inflation Rate", "Federal Funds Rate"]:
                            indicator_data = econ_data[econ_data["indicator"] == indicator]
                            if not indicator_data.empty:
                                latest_value = indicator_data["value"].iloc[-1]
                                manufacturing_indicators.append({
                                    "indicator": indicator,
                                    "value": latest_value,
                                    "impact": self._calculate_economic_impact(indicator, latest_value)
                                })
                        
                        enhanced_data["economic_indicators"] = manufacturing_indicators
                
                return enhanced_data
            
        except Exception as e:
            self.logger.error(f"Manufacturing data enhancement failed: {e}")
        
        return synthetic_data
    
    def _calculate_commodity_impact(self, commodity: str) -> float:
        """Calculate impact factor of commodity on supply chain costs"""
        
        impact_factors = {
            "crude_oil": 0.3,  # High impact on transportation
            "gold": 0.1,       # Low impact on most supply chains
            "silver": 0.1,
            "copper": 0.2,     # Medium impact on electronics/manufacturing
            "wheat": 0.15,     # Impact on food supply chains
            "corn": 0.15
        }
        
        return impact_factors.get(commodity.lower(), 0.1)
    
    def _calculate_economic_impact(self, indicator: str, value: float) -> Dict[str, float]:
        """Calculate economic indicator impact on manufacturing"""
        
        if indicator == "Unemployment Rate":
            # Higher unemployment = lower labor costs but potentially lower demand
            return {
                "labor_cost_factor": max(0.8, 1.0 - (value - 5.0) * 0.02),  # Baseline 5% unemployment
                "demand_factor": max(0.7, 1.0 - (value - 5.0) * 0.03)
            }
        elif indicator == "Inflation Rate":
            # Higher inflation = higher costs
            return {
                "cost_inflation_factor": 1.0 + max(0, (value - 2.0) * 0.5),  # Baseline 2% inflation
                "material_cost_factor": 1.0 + max(0, (value - 2.0) * 0.3)
            }
        elif indicator == "Federal Funds Rate":
            # Higher rates = higher financing costs
            return {
                "financing_cost_factor": 1.0 + max(0, (value - 2.0) * 0.1),  # Baseline 2% rate
                "investment_factor": max(0.8, 1.0 - (value - 2.0) * 0.05)
            }
        else:
            return {"general_factor": 1.0}
    
    async def get_external_data_status(self) -> Dict[str, Any]:
        """Get status of external data connections"""
        
        return {
            "available": self.external_data_manager.is_available(),
            "connectors": self.external_data_manager.get_connector_status(),
            "capabilities": self.external_data_manager.get_available_sources()
        }
    
    async def generate_enhanced_financial_dataset(self, symbols: List[str], 
                                                lookback_days: int = 252,
                                                requirements: Optional[DataRequirements] = None) -> SimulatedDataset:
        """Generate a financial dataset enhanced with real market data"""
        
        try:
            # Create requirements if not provided
            if requirements is None:
                requirements = DataRequirements(
                    required_parameters=["expected_returns", "risk_measures", "correlations"],
                    domain_context="finance",
                    problem_scale="medium"
                )
            
            # Generate base synthetic data
            synthetic_data = await self.domain_generator.generate_financial_data(requirements)
            
            # Replace synthetic assets with real symbols
            synthetic_data["assets"] = symbols
            
            # Enhance with real market data
            enhanced_data = await self._enhance_financial_data(synthetic_data, requirements)
            
            # Calculate quality score (higher for real data)
            quality_score = 0.95  # High quality for real market data
            
            # Create metadata
            metadata = {
                "domain": "finance",
                "generation_method": "real_market_data_enhanced",
                "symbols": symbols,
                "lookback_days": lookback_days,
                "external_data_used": True,
                "generated_at": datetime.now().isoformat()
            }
            
            simulation_notes = [
                f"Generated financial dataset for {len(symbols)} assets",
                f"Using {lookback_days} days of historical data",
                "Enhanced with real market data from external sources",
                "Includes real correlations, risk metrics, and economic indicators"
            ]
            
            return SimulatedDataset(
                data=enhanced_data,
                metadata=metadata,
                quality_score=quality_score,
                simulation_notes=simulation_notes,
                realistic_ranges=self._calculate_realistic_ranges(enhanced_data),
                data_quality=DataQuality.HIGH
            )
            
        except Exception as e:
            self.logger.error(f"Enhanced financial dataset generation failed: {e}")
            raise DataIntegrationError(f"Failed to generate enhanced financial dataset: {e}")