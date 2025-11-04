"""
FMCO Benchmarking Pipeline
Standard datasets and benchmarking capabilities for optimization models
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

class BenchmarkDataset(Enum):
    """Standard benchmark datasets for optimization"""
    TSP_LIB = "tsp_lib"
    CVRP_LIB = "cvrp_lib"
    OR_LIB = "or_lib"
    MIPLIB = "miplib"
    QAPLIB = "qaplib"
    MANUFACTURING_SCHEDULING = "manufacturing_scheduling"
    RETAIL_INVENTORY = "retail_inventory"
    FINANCIAL_PORTFOLIO = "financial_portfolio"

@dataclass
class BenchmarkInstance:
    """Individual benchmark instance"""
    name: str
    dataset: BenchmarkDataset
    problem_type: str
    size: Dict[str, int]
    optimal_value: Optional[float]
    instance_data: Dict[str, Any]
    metadata: Dict[str, Any]

@dataclass
class BenchmarkResult:
    """Benchmark evaluation result"""
    instance_name: str
    algorithm: str
    objective_value: float
    optimal_value: Optional[float]
    gap_percentage: Optional[float]
    solve_time: float
    status: str
    solution_quality: str
    metadata: Dict[str, Any]

class BenchmarkingPipeline:
    """FMCO benchmarking pipeline with standard datasets"""
    
    def __init__(self):
        self.datasets = self._initialize_datasets()
        self.benchmark_instances = self._load_benchmark_instances()
    
    def _initialize_datasets(self) -> Dict[str, Dict[str, Any]]:
        """Initialize standard benchmark datasets"""
        return {
            "tsp_lib": {
                "name": "TSPLIB",
                "description": "Traveling Salesman Problem Library",
                "url": "http://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/",
                "instances": ["eil51", "berlin52", "st70", "eil76", "pr76", "rat99", "kroA100", "kroB100"],
                "problem_type": "tsp",
                "optimal_known": True
            },
            "cvrp_lib": {
                "name": "CVRPLIB", 
                "description": "Capacitated Vehicle Routing Problem Library",
                "url": "http://vrp.atd-lab.inf.puc-rio.br/index.php/en/",
                "instances": ["A-n32-k5", "A-n33-k5", "A-n33-k6", "A-n34-k5", "A-n36-k5", "A-n37-k5", "A-n37-k6"],
                "problem_type": "cvrp",
                "optimal_known": True
            },
            "manufacturing_scheduling": {
                "name": "Manufacturing Scheduling Benchmarks",
                "description": "Real-world manufacturing scheduling problems",
                "instances": ["automotive_parts_3f", "electronics_5f", "textile_4f", "food_processing_6f"],
                "problem_type": "manufacturing_scheduling",
                "optimal_known": False
            },
            "retail_inventory": {
                "name": "Retail Inventory Benchmarks", 
                "description": "Multi-store inventory optimization problems",
                "instances": ["grocery_chain_10s", "electronics_15s", "clothing_8s", "pharmacy_12s"],
                "problem_type": "retail_inventory",
                "optimal_known": False
            },
            "financial_portfolio": {
                "name": "Financial Portfolio Benchmarks",
                "description": "Portfolio optimization with real market data",
                "instances": ["sp500_50a", "nasdaq_30a", "european_40a", "emerging_25a"],
                "problem_type": "financial_portfolio", 
                "optimal_known": False
            }
        }
    
    def _load_benchmark_instances(self) -> List[BenchmarkInstance]:
        """Load benchmark instances with synthetic data"""
        instances = []
        
        # TSP instances
        tsp_instances = [
            ("eil51", 426, {"nodes": 51}),
            ("berlin52", 7542, {"nodes": 52}),
            ("st70", 675, {"nodes": 70}),
            ("eil76", 538, {"nodes": 76}),
            ("pr76", 108159, {"nodes": 76}),
            ("rat99", 1211, {"nodes": 99}),
            ("kroA100", 21282, {"nodes": 100}),
            ("kroB100", 22141, {"nodes": 100})
        ]
        
        for name, optimal, size in tsp_instances:
            instances.append(BenchmarkInstance(
                name=name,
                dataset=BenchmarkDataset.TSP_LIB,
                problem_type="tsp",
                size=size,
                optimal_value=optimal,
                instance_data=self._generate_tsp_data(size["nodes"]),
                metadata={"source": "TSPLIB", "year": 1995}
            ))
        
        # Manufacturing instances
        manufacturing_instances = [
            ("automotive_parts_3f", {"facilities": 3, "products": 12, "customers": 4}),
            ("electronics_5f", {"facilities": 5, "products": 20, "customers": 8}),
            ("textile_4f", {"facilities": 4, "products": 15, "customers": 6}),
            ("food_processing_6f", {"facilities": 6, "products": 25, "customers": 10})
        ]
        
        for name, size in manufacturing_instances:
            instances.append(BenchmarkInstance(
                name=name,
                dataset=BenchmarkDataset.MANUFACTURING_SCHEDULING,
                problem_type="manufacturing_scheduling",
                size=size,
                optimal_value=None,
                instance_data=self._generate_manufacturing_data(size),
                metadata={"source": "synthetic", "domain": "manufacturing"}
            ))
        
        # Retail instances
        retail_instances = [
            ("grocery_chain_10s", {"stores": 10, "products": 50, "suppliers": 5}),
            ("electronics_15s", {"stores": 15, "products": 30, "suppliers": 8}),
            ("clothing_8s", {"stores": 8, "products": 40, "suppliers": 6}),
            ("pharmacy_12s", {"stores": 12, "products": 25, "suppliers": 4})
        ]
        
        for name, size in retail_instances:
            instances.append(BenchmarkInstance(
                name=name,
                dataset=BenchmarkDataset.RETAIL_INVENTORY,
                problem_type="retail_inventory",
                size=size,
                optimal_value=None,
                instance_data=self._generate_retail_data(size),
                metadata={"source": "synthetic", "domain": "retail"}
            ))
        
        return instances
    
    def _generate_tsp_data(self, num_nodes: int) -> Dict[str, Any]:
        """Generate TSP instance data"""
        np.random.seed(42)  # For reproducibility
        
        # Generate random coordinates
        coordinates = np.random.uniform(0, 100, (num_nodes, 2))
        
        # Calculate distance matrix
        distances = np.zeros((num_nodes, num_nodes))
        for i in range(num_nodes):
            for j in range(num_nodes):
                if i != j:
                    distances[i][j] = np.sqrt(
                        (coordinates[i][0] - coordinates[j][0])**2 + 
                        (coordinates[i][1] - coordinates[j][1])**2
                    )
        
        return {
            "coordinates": coordinates.tolist(),
            "distances": distances.tolist(),
            "num_nodes": num_nodes,
            "depot": 0
        }
    
    def _generate_manufacturing_data(self, size: Dict[str, int]) -> Dict[str, Any]:
        """Generate manufacturing scheduling instance data"""
        np.random.seed(42)
        
        facilities = size["facilities"]
        products = size["products"]
        customers = size["customers"]
        
        # Generate facility capacities
        capacities = np.random.uniform(300, 800, facilities)
        
        # Generate product demands
        demands = np.random.uniform(50, 200, (customers, products))
        
        # Generate production costs
        production_costs = np.random.uniform(10, 50, (facilities, products))
        
        # Generate inventory costs
        inventory_costs = np.random.uniform(2, 8, (facilities, products))
        
        # Generate setup costs
        setup_costs = np.random.uniform(100, 500, (facilities, products))
        
        return {
            "facilities": {
                "names": [f"facility_{i+1}" for i in range(facilities)],
                "capacities": capacities.tolist(),
                "locations": np.random.uniform(0, 100, (facilities, 2)).tolist()
            },
            "products": {
                "names": [f"product_{i+1}" for i in range(products)],
                "production_costs": production_costs.tolist(),
                "inventory_costs": inventory_costs.tolist(),
                "setup_costs": setup_costs.tolist()
            },
            "customers": {
                "names": [f"customer_{i+1}" for i in range(customers)],
                "demands": demands.tolist(),
                "locations": np.random.uniform(0, 100, (customers, 2)).tolist()
            }
        }
    
    def _generate_retail_data(self, size: Dict[str, int]) -> Dict[str, Any]:
        """Generate retail inventory instance data"""
        np.random.seed(42)
        
        stores = size["stores"]
        products = size["products"]
        suppliers = size["suppliers"]
        
        # Generate store capacities
        store_capacities = np.random.uniform(1000, 5000, stores)
        
        # Generate product demands
        demands = np.random.uniform(10, 100, (stores, products))
        
        # Generate supplier capacities
        supplier_capacities = np.random.uniform(500, 2000, (suppliers, products))
        
        # Generate costs
        purchase_costs = np.random.uniform(5, 25, (suppliers, products))
        selling_prices = np.random.uniform(10, 50, (stores, products))
        
        return {
            "stores": {
                "names": [f"store_{i+1}" for i in range(stores)],
                "capacities": store_capacities.tolist(),
                "locations": np.random.uniform(0, 100, (stores, 2)).tolist()
            },
            "products": {
                "names": [f"product_{i+1}" for i in range(products)],
                "demands": demands.tolist(),
                "selling_prices": selling_prices.tolist()
            },
            "suppliers": {
                "names": [f"supplier_{i+1}" for i in range(suppliers)],
                "capacities": supplier_capacities.tolist(),
                "purchase_costs": purchase_costs.tolist(),
                "locations": np.random.uniform(0, 100, (suppliers, 2)).tolist()
            }
        }
    
    def get_benchmark_instances(self, dataset: Optional[BenchmarkDataset] = None) -> List[BenchmarkInstance]:
        """Get benchmark instances, optionally filtered by dataset"""
        if dataset:
            return [inst for inst in self.benchmark_instances if inst.dataset == dataset]
        return self.benchmark_instances
    
    def get_instance_by_name(self, name: str) -> Optional[BenchmarkInstance]:
        """Get specific benchmark instance by name"""
        for instance in self.benchmark_instances:
            if instance.name == name:
                return instance
        return None
    
    async def evaluate_algorithm(
        self, 
        instance: BenchmarkInstance,
        algorithm: str,
        solver_config: Dict[str, Any],
        timeout: int = 300
    ) -> BenchmarkResult:
        """Evaluate an algorithm on a benchmark instance"""
        
        start_time = datetime.now()
        
        try:
            logger.info(f"🔬 Evaluating {algorithm} on {instance.name}")
            
            # Simulate algorithm execution (replace with actual solver calls)
            await asyncio.sleep(0.1)  # Simulate computation time
            
            # Generate synthetic result based on problem type
            if instance.problem_type == "tsp":
                objective_value = self._simulate_tsp_solution(instance)
            elif instance.problem_type == "manufacturing_scheduling":
                objective_value = self._simulate_manufacturing_solution(instance)
            elif instance.problem_type == "retail_inventory":
                objective_value = self._simulate_retail_solution(instance)
            else:
                objective_value = np.random.uniform(1000, 10000)
            
            solve_time = (datetime.now() - start_time).total_seconds()
            
            # Calculate gap if optimal is known
            gap_percentage = None
            if instance.optimal_value:
                gap_percentage = ((objective_value - instance.optimal_value) / instance.optimal_value) * 100
            
            # Determine solution quality
            solution_quality = self._assess_solution_quality(gap_percentage)
            
            result = BenchmarkResult(
                instance_name=instance.name,
                algorithm=algorithm,
                objective_value=objective_value,
                optimal_value=instance.optimal_value,
                gap_percentage=gap_percentage,
                solve_time=solve_time,
                status="optimal" if gap_percentage and gap_percentage < 0.1 else "feasible",
                solution_quality=solution_quality,
                metadata={
                    "solver_config": solver_config,
                    "timeout": timeout,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            logger.info(f"✅ {algorithm} completed on {instance.name}: {objective_value:.2f} (gap: {gap_percentage:.2f}%)")
            return result
            
        except Exception as e:
            logger.error(f"❌ {algorithm} failed on {instance.name}: {e}")
            return BenchmarkResult(
                instance_name=instance.name,
                algorithm=algorithm,
                objective_value=float('inf'),
                optimal_value=instance.optimal_value,
                gap_percentage=None,
                solve_time=(datetime.now() - start_time).total_seconds(),
                status="failed",
                solution_quality="failed",
                metadata={"error": str(e)}
            )
    
    def _simulate_tsp_solution(self, instance: BenchmarkInstance) -> float:
        """Simulate TSP solution (nearest neighbor heuristic)"""
        distances = np.array(instance.instance_data["distances"])
        n = len(distances)
        
        # Simple nearest neighbor heuristic
        visited = [False] * n
        tour = [0]
        visited[0] = True
        total_distance = 0
        
        current = 0
        for _ in range(n - 1):
            nearest = None
            min_dist = float('inf')
            
            for i in range(n):
                if not visited[i] and distances[current][i] < min_dist:
                    min_dist = distances[current][i]
                    nearest = i
            
            tour.append(nearest)
            visited[nearest] = True
            total_distance += min_dist
            current = nearest
        
        # Return to start
        total_distance += distances[current][0]
        
        # Add some randomness to simulate different algorithms
        return total_distance * np.random.uniform(1.0, 1.2)
    
    def _simulate_manufacturing_solution(self, instance: BenchmarkInstance) -> float:
        """Simulate manufacturing scheduling solution"""
        data = instance.instance_data
        facilities = len(data["facilities"]["capacities"])
        products = len(data["products"]["names"])
        customers = len(data["customers"]["names"])
        
        # Simple cost calculation
        production_cost = np.sum(data["products"]["production_costs"]) * 100
        inventory_cost = np.sum(data["products"]["inventory_costs"]) * 50
        setup_cost = np.sum(data["products"]["setup_costs"]) * 20
        
        total_cost = production_cost + inventory_cost + setup_cost
        
        # Add randomness
        return total_cost * np.random.uniform(0.8, 1.2)
    
    def _simulate_retail_solution(self, instance: BenchmarkInstance) -> float:
        """Simulate retail inventory solution"""
        data = instance.instance_data
        stores = len(data["stores"]["capacities"])
        products = len(data["products"]["names"])
        
        # Simple profit calculation
        revenue = np.sum(data["products"]["selling_prices"]) * 1000
        costs = np.sum(data["products"]["demands"]) * 5
        
        profit = revenue - costs
        
        # Add randomness
        return profit * np.random.uniform(0.9, 1.1)
    
    def _assess_solution_quality(self, gap_percentage: Optional[float]) -> str:
        """Assess solution quality based on gap"""
        if gap_percentage is None:
            return "unknown"
        elif gap_percentage < 0.1:
            return "optimal"
        elif gap_percentage < 1.0:
            return "excellent"
        elif gap_percentage < 5.0:
            return "good"
        elif gap_percentage < 10.0:
            return "acceptable"
        else:
            return "poor"
    
    async def run_benchmark_suite(
        self,
        algorithms: List[str],
        datasets: Optional[List[BenchmarkDataset]] = None,
        timeout: int = 300
    ) -> Dict[str, List[BenchmarkResult]]:
        """Run complete benchmark suite"""
        
        logger.info(f"🚀 Starting benchmark suite with {len(algorithms)} algorithms")
        
        if datasets is None:
            datasets = list(BenchmarkDataset)
        
        results = {alg: [] for alg in algorithms}
        
        for dataset in datasets:
            instances = self.get_benchmark_instances(dataset)
            logger.info(f"📊 Testing {len(instances)} instances from {dataset.value}")
            
            for instance in instances:
                for algorithm in algorithms:
                    solver_config = {
                        "algorithm": algorithm,
                        "timeout": timeout,
                        "precision": 1e-6
                    }
                    
                    result = await self.evaluate_algorithm(
                        instance, algorithm, solver_config, timeout
                    )
                    results[algorithm].append(result)
        
        logger.info(f"✅ Benchmark suite completed: {sum(len(r) for r in results.values())} evaluations")
        return results
    
    def generate_benchmark_report(self, results: Dict[str, List[BenchmarkResult]]) -> Dict[str, Any]:
        """Generate comprehensive benchmark report"""
        
        report = {
            "summary": {
                "total_evaluations": sum(len(r) for r in results.values()),
                "algorithms_tested": len(results),
                "timestamp": datetime.now().isoformat()
            },
            "algorithm_performance": {},
            "dataset_performance": {},
            "detailed_results": results
        }
        
        # Analyze algorithm performance
        for algorithm, algorithm_results in results.items():
            successful_results = [r for r in algorithm_results if r.status != "failed"]
            
            if successful_results:
                avg_gap = np.mean([r.gap_percentage for r in successful_results if r.gap_percentage is not None])
                avg_time = np.mean([r.solve_time for r in successful_results])
                success_rate = len(successful_results) / len(algorithm_results)
                
                report["algorithm_performance"][algorithm] = {
                    "success_rate": success_rate,
                    "average_gap_percentage": avg_gap if not np.isnan(avg_gap) else None,
                    "average_solve_time": avg_time,
                    "total_evaluations": len(algorithm_results),
                    "successful_evaluations": len(successful_results)
                }
        
        return report
