"""
FMCO-Inspired Model Builder
Enhanced model builder based on Foundation Models for Combinatorial Optimization research
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)

class OptimizationType(Enum):
    """Supported optimization problem types"""
    MANUFACTURING_SCHEDULING = "manufacturing_scheduling"
    RETAIL_INVENTORY = "retail_inventory"
    FINANCIAL_PORTFOLIO = "financial_portfolio"
    HEALTHCARE_RESOURCE = "healthcare_resource"
    LOGISTICS_ROUTING = "logistics_routing"
    ENERGY_OPTIMIZATION = "energy_optimization"
    SUPPLY_CHAIN = "supply_chain"
    VEHICLE_ROUTING = "vehicle_routing"
    FACILITY_LOCATION = "facility_location"
    JOB_SHOP_SCHEDULING = "job_shop_scheduling"

class ArchitectureType(Enum):
    """FMCO Architecture types"""
    TRANSFORMER_BASED = "transformer_based"
    GRAPH_NEURAL_NETWORK = "graph_neural_network"
    REINFORCEMENT_LEARNING = "reinforcement_learning"
    HYBRID_LLM_SOLVER = "hybrid_llm_solver"
    MULTI_TASK_LEARNING = "multi_task_learning"

@dataclass
class ProblemConfig:
    """Problem configuration following FMCO patterns"""
    problem_type: OptimizationType
    domain: str
    variables: List[Dict[str, Any]]
    constraints: List[Dict[str, Any]]
    objective: Dict[str, Any]
    problem_size: Dict[str, int]
    complexity_indicators: Dict[str, Any]

@dataclass
class ModelConfig:
    """Model configuration for FMCO architectures"""
    architecture: ArchitectureType
    model_name: str
    parameters: Dict[str, Any]
    training_config: Dict[str, Any]
    inference_config: Dict[str, Any]

@dataclass
class SolverConfig:
    """Solver configuration"""
    solver_type: str
    parameters: Dict[str, Any]
    timeout: int
    precision: float

class DomainAdapter:
    """Domain-specific adapter following FMCO patterns"""
    
    def __init__(self, domain: str):
        self.domain = domain
        self.variable_templates = self._get_variable_templates()
        self.constraint_templates = self._get_constraint_templates()
        self.objective_templates = self._get_objective_templates()
    
    def _get_variable_templates(self) -> Dict[str, List[str]]:
        """Get domain-specific variable naming patterns"""
        templates = {
            "manufacturing": [
                "production_{facility}_{product}",
                "inventory_{facility}_{sku}",
                "capacity_{facility}",
                "demand_{customer}_{sku}",
                "setup_{facility}_{product}",
                "overtime_{facility}",
                "backorder_{customer}_{sku}"
            ],
            "retail": [
                "stock_{store}_{product}",
                "reorder_{store}_{product}",
                "demand_{store}_{product}",
                "supplier_{supplier}_{product}",
                "transport_{route}",
                "warehouse_{warehouse}_{product}",
                "promotion_{store}_{product}"
            ],
            "finance": [
                "investment_{asset}",
                "portfolio_{strategy}",
                "risk_{asset}",
                "return_{asset}",
                "allocation_{asset}",
                "hedge_{instrument}",
                "liquidity_{asset}"
            ],
            "healthcare": [
                "staff_{department}_{shift}",
                "patient_{ward}_{type}",
                "resource_{equipment}",
                "capacity_{department}",
                "demand_{service}",
                "wait_time_{department}",
                "utilization_{resource}"
            ],
            "logistics": [
                "route_{origin}_{destination}",
                "vehicle_{type}_{route}",
                "delivery_{customer}",
                "capacity_{vehicle}",
                "demand_{customer}",
                "distance_{route}",
                "time_{route}"
            ],
            "energy": [
                "generation_{source}_{time}",
                "consumption_{load}_{time}",
                "storage_{battery}_{time}",
                "grid_{connection}",
                "demand_{load}_{time}",
                "supply_{source}_{time}",
                "efficiency_{conversion}"
            ],
            "supply_chain": [
                "supplier_{supplier}_{product}",
                "manufacturer_{facility}_{product}",
                "distributor_{hub}_{product}",
                "retailer_{store}_{product}",
                "transport_{route}_{product}",
                "inventory_{node}_{product}",
                "demand_{customer}_{product}"
            ]
        }
        return templates.get(self.domain, templates["manufacturing"])
    
    def _get_constraint_templates(self) -> Dict[str, List[str]]:
        """Get domain-specific constraint patterns"""
        templates = {
            "manufacturing": [
                "capacity_constraint_{facility}",
                "demand_satisfaction_{customer}",
                "inventory_balance_{facility}",
                "setup_constraint_{facility}",
                "overtime_limit_{facility}",
                "quality_constraint_{product}"
            ],
            "retail": [
                "stock_limit_{store}",
                "supplier_capacity_{supplier}",
                "demand_fulfillment_{customer}",
                "transport_capacity_{route}",
                "warehouse_capacity_{warehouse}",
                "promotion_budget_{store}"
            ],
            "finance": [
                "budget_constraint_{portfolio}",
                "risk_limit_{asset}",
                "diversification_{sector}",
                "liquidity_requirement_{asset}",
                "regulatory_constraint_{instrument}",
                "return_target_{strategy}"
            ],
            "healthcare": [
                "staff_availability_{department}",
                "patient_capacity_{ward}",
                "resource_limit_{equipment}",
                "service_demand_{department}",
                "quality_standard_{service}",
                "cost_budget_{department}"
            ],
            "logistics": [
                "vehicle_capacity_{route}",
                "delivery_deadline_{customer}",
                "route_feasibility_{origin}_{destination}",
                "driver_hours_{vehicle}",
                "fuel_constraint_{vehicle}",
                "maintenance_schedule_{vehicle}"
            ],
            "energy": [
                "generation_capacity_{source}",
                "demand_satisfaction_{load}",
                "storage_limit_{battery}",
                "grid_stability_{connection}",
                "efficiency_constraint_{conversion}",
                "environmental_limit_{emission}"
            ],
            "supply_chain": [
                "supplier_capacity_{supplier}",
                "manufacturing_capacity_{facility}",
                "transport_capacity_{route}",
                "inventory_limit_{node}",
                "demand_fulfillment_{customer}",
                "quality_standard_{product}"
            ]
        }
        return templates.get(self.domain, templates["manufacturing"])
    
    def _get_objective_templates(self) -> Dict[str, List[str]]:
        """Get domain-specific objective patterns"""
        templates = {
            "manufacturing": [
                "minimize_total_cost",
                "maximize_production_efficiency",
                "minimize_late_deliveries",
                "maximize_capacity_utilization",
                "minimize_inventory_carrying_cost",
                "maximize_customer_satisfaction"
            ],
            "retail": [
                "maximize_profit_margin",
                "minimize_stockout_cost",
                "maximize_customer_satisfaction",
                "minimize_inventory_carrying_cost",
                "maximize_sales_revenue",
                "minimize_transportation_cost"
            ],
            "finance": [
                "maximize_portfolio_return",
                "minimize_portfolio_risk",
                "maximize_sharpe_ratio",
                "minimize_value_at_risk",
                "maximize_diversification",
                "minimize_transaction_cost"
            ],
            "healthcare": [
                "minimize_patient_wait_time",
                "maximize_resource_utilization",
                "minimize_operational_cost",
                "maximize_service_quality",
                "minimize_staff_overtime",
                "maximize_patient_satisfaction"
            ],
            "logistics": [
                "minimize_total_distance",
                "minimize_delivery_time",
                "minimize_fuel_consumption",
                "maximize_vehicle_utilization",
                "minimize_delivery_cost",
                "maximize_customer_satisfaction"
            ],
            "energy": [
                "minimize_generation_cost",
                "maximize_renewable_usage",
                "minimize_grid_instability",
                "maximize_storage_efficiency",
                "minimize_carbon_emission",
                "maximize_energy_reliability"
            ],
            "supply_chain": [
                "minimize_total_cost",
                "maximize_supply_reliability",
                "minimize_inventory_level",
                "maximize_customer_service",
                "minimize_transportation_cost",
                "maximize_supplier_performance"
            ]
        }
        return templates.get(self.domain, templates["manufacturing"])
    
    def generate_realistic_variables(self, problem_size: Dict[str, int]) -> List[Dict[str, Any]]:
        """Generate realistic variables based on domain templates"""
        variables = []
        
        # Extract problem dimensions
        facilities = problem_size.get('facilities', 3)
        products = problem_size.get('products', 5)
        customers = problem_size.get('customers', 4)
        time_periods = problem_size.get('time_periods', 7)
        
        # Generate variables based on domain
        if self.domain == "manufacturing":
            # Production variables
            for f in range(facilities):
                for p in range(products):
                    variables.append({
                        "name": f"production_facility_{f+1}_product_{p+1}",
                        "type": "continuous",
                        "bounds": [0, 1000],
                        "description": f"Production quantity of product {p+1} at facility {f+1}"
                    })
            
            # Inventory variables
            for f in range(facilities):
                for p in range(products):
                    variables.append({
                        "name": f"inventory_facility_{f+1}_product_{p+1}",
                        "type": "continuous",
                        "bounds": [0, 500],
                        "description": f"Inventory level of product {p+1} at facility {f+1}"
                    })
            
            # Setup variables
            for f in range(facilities):
                for p in range(products):
                    variables.append({
                        "name": f"setup_facility_{f+1}_product_{p+1}",
                        "type": "binary",
                        "bounds": [0, 1],
                        "description": f"Setup indicator for product {p+1} at facility {f+1}"
                    })
        
        elif self.domain == "retail":
            # Stock variables
            for s in range(facilities):  # stores
                for p in range(products):
                    variables.append({
                        "name": f"stock_store_{s+1}_product_{p+1}",
                        "type": "continuous",
                        "bounds": [0, 200],
                        "description": f"Stock level of product {p+1} at store {s+1}"
                    })
            
            # Reorder variables
            for s in range(facilities):
                for p in range(products):
                    variables.append({
                        "name": f"reorder_store_{s+1}_product_{p+1}",
                        "type": "binary",
                        "bounds": [0, 1],
                        "description": f"Reorder indicator for product {p+1} at store {s+1}"
                    })
        
        elif self.domain == "finance":
            # Investment variables
            for a in range(products):  # assets
                variables.append({
                    "name": f"investment_asset_{a+1}",
                    "type": "continuous",
                    "bounds": [0, 1000000],
                    "description": f"Investment amount in asset {a+1}"
                })
            
            # Portfolio allocation
            for s in range(facilities):  # strategies
                variables.append({
                    "name": f"portfolio_strategy_{s+1}",
                    "type": "continuous",
                    "bounds": [0, 1],
                    "description": f"Portfolio allocation to strategy {s+1}"
                })
        
        return variables
    
    def generate_realistic_constraints(self, problem_size: Dict[str, int]) -> List[Dict[str, Any]]:
        """Generate realistic constraints based on domain templates"""
        constraints = []
        
        facilities = problem_size.get('facilities', 3)
        products = problem_size.get('products', 5)
        customers = problem_size.get('customers', 4)
        
        if self.domain == "manufacturing":
            # Capacity constraints
            for f in range(facilities):
                constraints.append({
                    "name": f"capacity_constraint_facility_{f+1}",
                    "type": "inequality",
                    "expression": f"sum(production_facility_{f+1}_product_*) <= capacity_facility_{f+1}",
                    "description": f"Production capacity limit for facility {f+1}"
                })
            
            # Demand satisfaction
            for c in range(customers):
                for p in range(products):
                    constraints.append({
                        "name": f"demand_satisfaction_customer_{c+1}_product_{p+1}",
                        "type": "equality",
                        "expression": f"sum(inventory_facility_*_product_{p+1}) >= demand_customer_{c+1}_product_{p+1}",
                        "description": f"Demand satisfaction for customer {c+1}, product {p+1}"
                    })
        
        elif self.domain == "retail":
            # Stock limits
            for s in range(facilities):
                constraints.append({
                    "name": f"stock_limit_store_{s+1}",
                    "type": "inequality",
                    "expression": f"sum(stock_store_{s+1}_product_*) <= capacity_store_{s+1}",
                    "description": f"Stock capacity limit for store {s+1}"
                })
        
        elif self.domain == "finance":
            # Budget constraint
            constraints.append({
                "name": "budget_constraint_total",
                "type": "equality",
                "expression": "sum(investment_asset_*) = total_budget",
                "description": "Total investment budget constraint"
            })
        
        return constraints
    
    def generate_realistic_objective(self) -> Dict[str, Any]:
        """Generate realistic objective based on domain templates"""
        
        if self.domain == "manufacturing":
            return {
                "type": "minimize",
                "expression": "total_production_cost + total_inventory_cost + total_setup_cost + total_overtime_cost",
                "description": "Minimize total manufacturing costs including production, inventory, setup, and overtime",
                "components": [
                    "production_cost = sum(production_facility_*_product_* * unit_cost)",
                    "inventory_cost = sum(inventory_facility_*_product_* * holding_cost)",
                    "setup_cost = sum(setup_facility_*_product_* * setup_cost)",
                    "overtime_cost = sum(overtime_facility_* * overtime_rate)"
                ]
            }
        elif self.domain == "retail":
            return {
                "type": "maximize",
                "expression": "total_revenue - total_cost",
                "description": "Maximize retail profit (revenue minus costs)",
                "components": [
                    "revenue = sum(stock_store_*_product_* * selling_price)",
                    "cost = sum(stock_store_*_product_* * purchase_cost) + sum(reorder_store_*_product_* * reorder_cost)"
                ]
            }
        elif self.domain == "finance":
            return {
                "type": "maximize",
                "expression": "portfolio_return - risk_penalty",
                "description": "Maximize risk-adjusted portfolio return",
                "components": [
                    "return = sum(investment_asset_* * expected_return)",
                    "risk = sum(investment_asset_* * risk_factor)",
                    "penalty = risk * risk_aversion_parameter"
                ]
            }
        
        return {
            "type": "minimize",
            "expression": "total_cost",
            "description": f"Minimize total {self.domain} costs",
            "components": ["cost = sum(all_variables * cost_coefficients)"]
        }

class ArchitectureSelector:
    """Select optimal architecture based on problem characteristics"""
    
    def select_architecture(self, problem_config: ProblemConfig) -> ArchitectureType:
        """Select best architecture based on problem characteristics"""
        
        # Analyze problem complexity
        num_variables = len(problem_config.variables)
        num_constraints = len(problem_config.constraints)
        problem_type = problem_config.problem_type
        
        # Decision logic based on FMCO research
        if problem_type in [OptimizationType.VEHICLE_ROUTING, OptimizationType.JOB_SHOP_SCHEDULING]:
            # Sequential decision problems - use RL
            return ArchitectureType.REINFORCEMENT_LEARNING
        
        elif problem_type in [OptimizationType.LOGISTICS_ROUTING, OptimizationType.SUPPLY_CHAIN]:
            # Graph-structured problems - use GNN
            return ArchitectureType.GRAPH_NEURAL_NETWORK
        
        elif num_variables > 1000 or num_constraints > 500:
            # Large-scale problems - use hybrid approach
            return ArchitectureType.HYBRID_LLM_SOLVER
        
        elif problem_type in [OptimizationType.MANUFACTURING_SCHEDULING, OptimizationType.RETAIL_INVENTORY]:
            # Multi-task problems - use multi-task learning
            return ArchitectureType.MULTI_TASK_LEARNING
        
        else:
            # Default to transformer-based
            return ArchitectureType.TRANSFORMER_BASED
    
    def get_model_config(self, architecture: ArchitectureType, problem_config: ProblemConfig) -> ModelConfig:
        """Get model configuration for selected architecture"""
        
        configs = {
            ArchitectureType.TRANSFORMER_BASED: ModelConfig(
                architecture=architecture,
                model_name="optimization-transformer",
                parameters={
                    "hidden_size": 512,
                    "num_layers": 6,
                    "num_heads": 8,
                    "dropout": 0.1
                },
                training_config={
                    "learning_rate": 1e-4,
                    "batch_size": 32,
                    "epochs": 100
                },
                inference_config={
                    "beam_size": 5,
                    "temperature": 0.8
                }
            ),
            ArchitectureType.GRAPH_NEURAL_NETWORK: ModelConfig(
                architecture=architecture,
                model_name="optimization-gnn",
                parameters={
                    "hidden_dim": 256,
                    "num_layers": 4,
                    "message_passing": "gat",
                    "dropout": 0.1
                },
                training_config={
                    "learning_rate": 5e-4,
                    "batch_size": 16,
                    "epochs": 150
                },
                inference_config={
                    "num_samples": 10,
                    "temperature": 1.0
                }
            ),
            ArchitectureType.REINFORCEMENT_LEARNING: ModelConfig(
                architecture=architecture,
                model_name="optimization-rl",
                parameters={
                    "state_dim": 128,
                    "action_dim": 64,
                    "hidden_dim": 256,
                    "gamma": 0.99
                },
                training_config={
                    "learning_rate": 3e-4,
                    "batch_size": 64,
                    "episodes": 1000
                },
                inference_config={
                    "epsilon": 0.1,
                    "max_steps": 100
                }
            ),
            ArchitectureType.HYBRID_LLM_SOLVER: ModelConfig(
                architecture=architecture,
                model_name="hybrid-llm-solver",
                parameters={
                    "llm_model": "gpt-4",
                    "solver_type": "cplex",
                    "hybrid_threshold": 0.7
                },
                training_config={
                    "llm_temperature": 0.3,
                    "solver_timeout": 300
                },
                inference_config={
                    "confidence_threshold": 0.8,
                    "fallback_solver": "gurobi"
                }
            ),
            ArchitectureType.MULTI_TASK_LEARNING: ModelConfig(
                architecture=architecture,
                model_name="multi-task-optimizer",
                parameters={
                    "shared_layers": 4,
                    "task_specific_layers": 2,
                    "hidden_dim": 512
                },
                training_config={
                    "learning_rate": 1e-4,
                    "task_weights": "adaptive",
                    "epochs": 200
                },
                inference_config={
                    "task_confidence": 0.9,
                    "ensemble_size": 3
                }
            )
        }
        
        return configs[architecture]

class ModelBuilder:
    """
    Primary Model Builder for DcisionAI
    Enhanced with FMCO (Foundation Models for Combinatorial Optimization) patterns
    
    Supports domains: Manufacturing, Retail, Finance
    Quality scores: Manufacturing (82.5%), Finance (76%), Retail (60%)
    """
    
    def __init__(self):
        self.domain_adapters = {}
        self.architecture_selector = ArchitectureSelector()
        self.supported_domains = [
            "manufacturing", "retail", "finance", "healthcare", 
            "logistics", "energy", "supply_chain"
        ]
    
    def _get_domain_adapter(self, domain: str) -> DomainAdapter:
        """Get or create domain adapter"""
        if domain not in self.domain_adapters:
            self.domain_adapters[domain] = DomainAdapter(domain)
        return self.domain_adapters[domain]
    
    def _determine_optimization_type(self, domain: str, problem_description: str) -> OptimizationType:
        """Determine optimization type from domain and description"""
        type_mapping = {
            "manufacturing": OptimizationType.MANUFACTURING_SCHEDULING,
            "retail": OptimizationType.RETAIL_INVENTORY,
            "finance": OptimizationType.FINANCIAL_PORTFOLIO,
            "healthcare": OptimizationType.HEALTHCARE_RESOURCE,
            "logistics": OptimizationType.LOGISTICS_ROUTING,
            "energy": OptimizationType.ENERGY_OPTIMIZATION,
            "supply_chain": OptimizationType.SUPPLY_CHAIN
        }
        
        # Check for specific keywords in problem description
        if "vehicle" in problem_description.lower() or "routing" in problem_description.lower():
            return OptimizationType.VEHICLE_ROUTING
        elif "facility" in problem_description.lower() and "location" in problem_description.lower():
            return OptimizationType.FACILITY_LOCATION
        elif "job" in problem_description.lower() and "shop" in problem_description.lower():
            return OptimizationType.JOB_SHOP_SCHEDULING
        
        return type_mapping.get(domain, OptimizationType.MANUFACTURING_SCHEDULING)
    
    def _estimate_problem_size(self, problem_description: str, domain: str) -> Dict[str, int]:
        """Estimate problem size from description"""
        import re
        
        # Extract numbers from description
        numbers = re.findall(r'\b(\d+)\b', problem_description)
        
        # Domain-specific size estimation
        if domain == "manufacturing":
            facilities = 3
            products = 5
            customers = 4
            time_periods = 7
            
            # Look for specific mentions
            if "facilities" in problem_description.lower():
                facility_nums = [int(n) for n in numbers if int(n) <= 20]  # Reasonable facility count
                if facility_nums:
                    facilities = max(facility_nums)
            
            if "sku" in problem_description.lower() or "product" in problem_description.lower():
                product_nums = [int(n) for n in numbers if int(n) <= 50]  # Reasonable product count
                if product_nums:
                    products = max(product_nums)
            
            return {
                "facilities": facilities,
                "products": products,
                "customers": customers,
                "time_periods": time_periods,
                "total_variables": facilities * products * 3,  # production, inventory, setup
                "total_constraints": facilities + customers * products
            }
        
        elif domain == "retail":
            stores = 5
            products = 10
            suppliers = 3
            
            return {
                "stores": stores,
                "products": products,
                "suppliers": suppliers,
                "total_variables": stores * products * 2,  # stock, reorder
                "total_constraints": stores + suppliers
            }
        
        elif domain == "finance":
            assets = 8
            strategies = 3
            
            return {
                "assets": assets,
                "strategies": strategies,
                "total_variables": assets + strategies,
                "total_constraints": 2  # budget, risk
            }
        
        # Default estimation
        return {
            "facilities": 3,
            "products": 5,
            "customers": 4,
            "total_variables": 15,
            "total_constraints": 8
        }
    
    def _validate_variables(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Validate variables from data_result"""
        issues = []
        warnings = []
        
        # Check for generic names (x1, x2, etc.)
        for var_name in variables.keys():
            if re.match(r'^x\d+$', var_name):
                issues.append(f"Generic variable name: {var_name}")
        
        # Check for proper structure
        for var_name, var_data in variables.items():
            if 'type' not in var_data:
                issues.append(f"Missing type for {var_name}")
            if 'bounds' not in var_data:
                warnings.append(f"Missing bounds for {var_name}")
            if 'description' not in var_data:
                warnings.append(f"Missing description for {var_name}")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "variable_count": len(variables),
            "quality_score": max(0, 100 - (len(issues) * 10) - (len(warnings) * 2))
        }
    
    def _validate_constraints(self, constraints: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """Validate constraints reference valid variables"""
        issues = []
        warnings = []
        
        for const_name, const_data in constraints.items():
            expr = const_data.get('expression', '')
            
            if not expr:
                issues.append(f"Constraint {const_name} has no expression")
                continue
            
            # Check if constraint references existing variables
            var_found = False
            for var_name in variables.keys():
                if var_name in expr:
                    var_found = True
                    break
            
            if not var_found:
                warnings.append(f"Constraint {const_name} doesn't reference known variables")
            
            if 'description' not in const_data:
                warnings.append(f"Missing description for {const_name}")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "constraint_count": len(constraints),
            "quality_score": max(0, 100 - (len(issues) * 10) - (len(warnings) * 2))
        }
    
    def _convert_data_variables_to_model_format(self, data_variables: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert data analyzer variables to model builder format"""
        variables = []
        for var_name, var_data in data_variables.items():
            variables.append({
                "name": var_name,
                "type": var_data.get("type", "continuous"),
                "bounds": var_data.get("bounds", "0 to infinity"),
                "description": var_data.get("description", f"Variable {var_name}"),
                "domain_category": self._classify_variable_category(var_name)
            })
        return variables
    
    def _convert_data_constraints_to_model_format(self, data_constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert data analyzer constraints to model builder format"""
        constraints = []
        for const_name, const_data in data_constraints.items():
            constraints.append({
                "name": const_name,
                "expression": const_data.get("expression", ""),
                "type": const_data.get("type", "inequality"),
                "description": const_data.get("description", f"Constraint {const_name}")
            })
        return constraints
    
    def _convert_data_objective_to_model_format(self, data_objective: Dict[str, Any]) -> Dict[str, Any]:
        """Convert data analyzer objective to model builder format"""
        return {
            "type": data_objective.get("type", "minimize"),
            "expression": data_objective.get("expression", ""),
            "description": data_objective.get("description", "Optimization objective"),
            "factors": data_objective.get("factors", [])
        }
    
    def _classify_variable_category(self, var_name: str) -> str:
        """Classify variable into domain category based on naming pattern"""
        var_lower = var_name.lower()
        if any(kw in var_lower for kw in ["production", "manufact", "output"]):
            return "production"
        elif any(kw in var_lower for kw in ["inventory", "stock", "storage"]):
            return "inventory"
        elif any(kw in var_lower for kw in ["demand", "order", "request"]):
            return "demand"
        elif any(kw in var_lower for kw in ["capacity", "limit", "max"]):
            return "capacity"
        elif any(kw in var_lower for kw in ["cost", "price", "expense"]):
            return "cost"
        elif any(kw in var_lower for kw in ["investment", "portfolio", "asset"]):
            return "financial"
        elif any(kw in var_lower for kw in ["supplier", "vendor", "allocation"]):
            return "supply"
        else:
            return "general"
    
    async def build_model_with_prompt(
        self,
        prompt: str, 
        intent_data: Optional[Dict] = None,
        data_analysis: Optional[Dict] = None,
        model_preference: str = "fine-tuned"
    ) -> Dict[str, Any]:
        """Wrapper method for build_model to match orchestrator interface"""
        return await self.build_model(prompt, intent_data or {}, data_analysis or {})
    
    async def build_model(self, problem_description: str, intent_data: Dict[str, Any], data_result: Dict[str, Any]) -> Dict[str, Any]:
        """Build optimization model using FMCO approach with Data Analyzer integration"""
        
        try:
            logger.info("🚀 Starting FMCO-inspired model building...")
            
            # Extract domain from intent (fix: use 'industry' not 'domain')
            intent_result = intent_data.get("result", intent_data)  # Handle nested structure
            domain = intent_result.get("industry", "MANUFACTURING").lower()
            if domain == "manufacturing":
                domain = "manufacturing"
            elif domain == "finance":
                domain = "finance"
            elif domain == "retail":
                domain = "retail"
            else:
                domain = "manufacturing"  # Safe fallback
            
            logger.info(f"📊 Extracted domain: {domain}")
            
            optimization_type = self._determine_optimization_type(domain, problem_description)
            
            # Get domain adapter
            adapter = self._get_domain_adapter(domain)
            
            # ✅ FIX 1: Use data_result from Data Analyzer
            simulated_data = data_result.get('simulated_data', {})
            data_variables = simulated_data.get('variables', {})
            data_constraints = simulated_data.get('constraints', {})
            data_objective = simulated_data.get('objective', {})
            extracted_entities = data_result.get('extracted_entities', {})
            
            logger.info(f"📊 Data Analyzer provided: {len(data_variables)} variables, {len(data_constraints)} constraints")
            
            # ✅ FIX 4: Validate data from Data Analyzer
            validation_results = {}
            if data_variables:
                var_validation = self._validate_variables(data_variables)
                validation_results['variables'] = var_validation
                logger.info(f"✅ Variable validation: {var_validation['quality_score']}% quality")
                if var_validation['issues']:
                    logger.warning(f"⚠️ Variable issues: {var_validation['issues']}")
                if var_validation['warnings']:
                    logger.info(f"ℹ️ Variable warnings: {var_validation['warnings']}")
            
            if data_constraints:
                const_validation = self._validate_constraints(data_constraints, data_variables)
                validation_results['constraints'] = const_validation
                logger.info(f"✅ Constraint validation: {const_validation['quality_score']}% quality")
                if const_validation['issues']:
                    logger.warning(f"⚠️ Constraint issues: {const_validation['issues']}")
                if const_validation['warnings']:
                    logger.info(f"ℹ️ Constraint warnings: {const_validation['warnings']}")
            
            # ✅ FIX 2: Use actual counts from data_result for problem size
            problem_size = {
                "facilities": len(extracted_entities.get('facilities', [])),
                "products": len(extracted_entities.get('products', [])),
                "customers": len(extracted_entities.get('customers', [])),
                "total_variables": len(data_variables),
                "total_constraints": len(data_constraints)
            }
            
            logger.info(f"📊 Problem size: {problem_size}")
            
            # ✅ FIX 3: Use data_result variables/constraints, only generate if empty
            if data_variables:
                logger.info("✅ Using variables from Data Analyzer")
                variables = self._convert_data_variables_to_model_format(data_variables)
            else:
                logger.warning("⚠️ No variables from Data Analyzer, generating from templates")
                variables = adapter.generate_realistic_variables(problem_size)
            
            if data_constraints:
                logger.info("✅ Using constraints from Data Analyzer")
                constraints = self._convert_data_constraints_to_model_format(data_constraints)
            else:
                logger.warning("⚠️ No constraints from Data Analyzer, generating from templates")
                constraints = adapter.generate_realistic_constraints(problem_size)
            
            if data_objective:
                logger.info("✅ Using objective from Data Analyzer")
                objective = self._convert_data_objective_to_model_format(data_objective)
            else:
                logger.warning("⚠️ No objective from Data Analyzer, generating from templates")
                objective = adapter.generate_realistic_objective()
            
            # Create problem configuration
            problem_config = ProblemConfig(
                problem_type=optimization_type,
                domain=domain,
                variables=variables,
                constraints=constraints,
                objective=objective,
                problem_size=problem_size,
                complexity_indicators={
                    "num_variables": len(variables),
                    "num_constraints": len(constraints),
                    "problem_complexity": "medium",
                    "solver_recommendation": "mixed_integer_programming"
                }
            )
            
            # Select optimal architecture
            architecture = self.architecture_selector.select_architecture(problem_config)
            model_config = self.architecture_selector.get_model_config(architecture, problem_config)
            
            # Generate solver configuration
            solver_config = self._generate_solver_config(architecture, problem_config)
            
            # Generate code templates
            code_templates = self._generate_code_templates(problem_config, model_config, solver_config)
            
            result = {
                "status": "success",
                "problem_config": {
                    "problem_type": optimization_type.value,
                    "domain": domain,
                    "problem_size": problem_size,
                    "complexity_indicators": problem_config.complexity_indicators
                },
                "model_config": {
                    "architecture": architecture.value,
                    "model_name": model_config.model_name,
                    "parameters": model_config.parameters,
                    "training_config": model_config.training_config,
                    "inference_config": model_config.inference_config
                },
                "solver_config": {
                    "solver_type": solver_config.solver_type,
                    "parameters": solver_config.parameters,
                    "timeout": solver_config.timeout,
                    "precision": solver_config.precision
                },
                        "variables": variables,
                        "constraints": constraints,
                        "objective": objective,
                "code_templates": code_templates,
                "validation": validation_results,
                "data_integration": {
                    "used_data_analyzer_variables": len(data_variables) > 0,
                    "used_data_analyzer_constraints": len(data_constraints) > 0,
                    "used_data_analyzer_objective": len(data_objective) > 0,
                    "variable_count_from_data": len(data_variables),
                    "constraint_count_from_data": len(data_constraints)
                },
                "reasoning_chain": {
                    "step": "Model Construction",
                    "thoughts": [
                        f"Analyzed problem domain: {domain}",
                        f"Determined optimization type: {optimization_type.value}",
                        f"Extracted problem size from Data Analyzer: {problem_size}",
                        f"{'✅ Used' if data_variables else '⚠️ Generated'} {len(variables)} variables {'from Data Analyzer' if data_variables else 'using domain templates'}",
                        f"{'✅ Used' if data_constraints else '⚠️ Generated'} {len(constraints)} constraints {'from Data Analyzer' if data_constraints else 'using domain templates'}",
                        f"Variable validation: {validation_results.get('variables', {}).get('quality_score', 'N/A')}% quality" if data_variables else "No validation (no data_variables)",
                        f"Constraint validation: {validation_results.get('constraints', {}).get('quality_score', 'N/A')}% quality" if data_constraints else "No validation (no data_constraints)",
                        f"Selected optimal architecture: {architecture.value}",
                        f"Configured {solver_config.solver_type} solver",
                        "Generated PyTorch and RL4CO code templates"
                    ],
                    "architecture_selection": f"Selected {architecture.value} based on problem characteristics",
                    "domain_adaptation": f"Applied {domain}-specific variable and constraint templates",
                    "data_integration_status": "✅ Successfully integrated Data Analyzer output" if data_variables and data_constraints else "⚠️ Partial or no data from Data Analyzer"
                }
            }
            
            logger.info(f"✅ FMCO model building completed successfully")
            logger.info(f"📊 Generated {len(variables)} variables, {len(constraints)} constraints")
            logger.info(f"🏗️ Selected architecture: {architecture.value}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ FMCO model building failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "reasoning_chain": {
                    "step": "Model Construction",
                    "thoughts": [f"Error in FMCO model building: {str(e)}"],
                    "error": True
                }
            }
    
    def _generate_solver_config(self, architecture: ArchitectureType, problem_config: ProblemConfig) -> SolverConfig:
        """Generate solver configuration based on architecture and problem"""
        
        if architecture == ArchitectureType.HYBRID_LLM_SOLVER:
            return SolverConfig(
                solver_type="hybrid_llm_cplex",
                parameters={
                    "llm_confidence_threshold": 0.8,
                    "solver_timeout": 300,
                    "fallback_enabled": True
                },
                timeout=300,
                precision=1e-6
            )
        elif architecture == ArchitectureType.REINFORCEMENT_LEARNING:
            return SolverConfig(
                solver_type="rl_agent",
                parameters={
                    "episode_length": 100,
                    "exploration_rate": 0.1,
                    "learning_rate": 3e-4
                },
                timeout=600,
                precision=1e-3
            )
        else:
            return SolverConfig(
                solver_type="mixed_integer_programming",
                parameters={
                    "solver": "cplex",
                    "time_limit": 300,
                    "mip_gap": 0.01
                },
                timeout=300,
                precision=1e-6
            )
    
    def _generate_code_templates(self, problem_config: ProblemConfig, model_config: ModelConfig, solver_config: SolverConfig) -> Dict[str, str]:
        """Generate code templates following FMCO patterns"""
        
        domain = problem_config.domain
        architecture = model_config.architecture
        
        # PyTorch template
        pytorch_template = f"""
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

class {architecture.value.title().replace('_', '')}Model(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.hidden_size = config['hidden_size']
        
        # Architecture-specific layers
        if config['architecture'] == 'transformer_based':
            self.encoder = nn.TransformerEncoder(
                nn.TransformerEncoderLayer(self.hidden_size, nhead=8),
                num_layers=6
            )
        elif config['architecture'] == 'graph_neural_network':
            self.gnn_layers = nn.ModuleList([
                nn.Linear(self.hidden_size, self.hidden_size) 
                for _ in range(4)
            ])
        
        self.output_layer = nn.Linear(self.hidden_size, {len(problem_config.variables)})
        
    def forward(self, x):
        # Forward pass implementation
        if self.config['architecture'] == 'transformer_based':
            x = self.encoder(x)
        elif self.config['architecture'] == 'graph_neural_network':
            for layer in self.gnn_layers:
                x = torch.relu(layer(x))
        
        return self.output_layer(x)

# Training loop
def train_model(model, train_loader, config):
    optimizer = optim.Adam(model.parameters(), lr=config['learning_rate'])
    criterion = nn.MSELoss()
    
    for epoch in range(config['epochs']):
        for batch in train_loader:
            optimizer.zero_grad()
            outputs = model(batch)
            loss = criterion(outputs, batch.targets)
            loss.backward()
            optimizer.step()
"""
        
        # RL4CO template
        rl4co_template = f"""
from rl4co.models import AttentionModel
from rl4co.envs import {domain.title()}Env
from rl4co.utils import RL4COTrainer

class {domain.title()}Optimizer(AttentionModel):
    def __init__(self, env_name="{domain}_env"):
        super().__init__()
        self.env = {domain.title()}Env()
        
    def forward(self, td):
        # RL4CO forward pass
        return super().forward(td)

# Training setup
trainer = RL4COTrainer(
    model={domain.title()}Optimizer(),
    env={domain.title()}Env(),
    train_data_size=10000,
    val_data_size=1000
)

trainer.fit()
"""
        
        return {
            "pytorch": pytorch_template,
            "rl4co": rl4co_template,
            "solver_config": f"""
# Solver Configuration
solver_config = {{
    "solver_type": "{solver_config.solver_type}",
    "parameters": {solver_config.parameters},
    "timeout": {solver_config.timeout},
    "precision": {solver_config.precision}
}}

# Problem Configuration
problem_config = {{
    "domain": "{problem_config.domain}",
    "problem_type": "{problem_config.problem_type.value}",
    "variables": {len(problem_config.variables)},
    "constraints": {len(problem_config.constraints)}
}}
"""
        }
