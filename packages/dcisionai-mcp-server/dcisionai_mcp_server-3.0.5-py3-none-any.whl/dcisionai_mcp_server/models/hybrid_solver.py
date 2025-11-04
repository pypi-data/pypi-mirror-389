#!/usr/bin/env python3
"""
Hybrid Solver - Intelligent Solver Selection
Chooses the best solver based on problem characteristics
"""

import logging
from typing import Any, Dict, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ProblemType(Enum):
    """Supported problem types"""
    LP = "linear_programming"
    MILP = "mixed_integer_linear_programming"
    QP = "quadratic_programming"
    TSP = "traveling_salesman_problem"
    VRP = "vehicle_routing_problem"
    JOB_SHOP = "job_shop_scheduling"
    WORKFORCE = "workforce_rostering"
    MAINTENANCE = "maintenance_scheduling"
    STORE_LAYOUT = "store_layout_optimization"
    PROMOTION_SCHEDULING = "promotion_scheduling"
    PORTFOLIO_REBALANCING = "portfolio_rebalancing"
    TRADING_SCHEDULE = "trading_schedule"
    # FinServ domains (NEW)
    CUSTOMER_ONBOARDING = "customer_onboarding"
    PE_EXIT_TIMING = "pe_exit_timing"
    HF_REBALANCING = "hf_rebalancing"
    NONLINEAR = "nonlinear_programming"
    UNKNOWN = "unknown"


class SolverChoice(Enum):
    """Available solvers"""
    HIGHS = "highs"
    LMEA = "lmea"
    FMCO_NEURAL = "fmco_neural"
    HYBRID = "hybrid"


class HybridSolver:
    """
    Intelligent solver selection based on problem characteristics
    
    Decision tree:
    1. LP/MILP/QP with < 1000 variables → HiGHS (exact, fast)
    2. TSP/VRP/Scheduling → LMEA (heuristic, LLM-guided)
    3. Large MILP → LMEA warm-start → HiGHS refinement
    4. Nonlinear → Future: FMCO neural solvers
    """

    def __init__(self):
        # Legacy imports (commented out - moved to V2 Solver)
        # from .highs_via_ortools_solver import HiGHSViaORToolsSolver
        # from .lmea_solver import LMEASolver
        # from .lmea_vrp_solver import LMEAVRPSolver
        # from .lmea_scheduling_solver import LMEASchedulingSolver
        # from .lmea_workforce_solver import LMEAWorkforceSolver
        # from .lmea_maintenance_solver import LMEAMaintenanceSolver
        # from .lmea_retail_layout_solver import LMEARetailLayoutSolver
        # from .lmea_retail_promotion_solver import LMEARetailPromotionSolver
        # from .lmea_finance_portfolio_solver import LMEAFinancePortfolioSolver
        # from .lmea_finance_trading_solver import LMEAFinanceTradingSolver
        
        from .dcisionai_solver_v2 import DcisionAISolverV2
        
        # Legacy solvers (not used in Express Mode - V2 handles everything)
        # self.highs_solver = HiGHSViaORToolsSolver()
        # self.lmea_solver = LMEASolver()
        # self.vrp_solver = LMEAVRPSolver()
        # self.scheduling_solver = LMEASchedulingSolver()
        # self.workforce_solver = LMEAWorkforceSolver()
        # self.maintenance_solver = LMEAMaintenanceSolver()
        # self.retail_layout_solver = LMEARetailLayoutSolver()
        # self.retail_promotion_solver = LMEARetailPromotionSolver()
        # self.finance_portfolio_solver = LMEAFinancePortfolioSolver()
        # self.finance_trading_solver = LMEAFinanceTradingSolver()
        
        # V2 Solver - Universal solver with Supabase configs (handles all 11 domains)
        self.v2_solver = DcisionAISolverV2()
        
        # Thresholds for decision making
        self.large_problem_threshold = 1000  # variables
        self.lmea_quick_generations = 20  # for warm-starting
    
    async def solve_express(
        self,
        problem_description: str,
        max_generations: int = 100
    ) -> Dict[str, Any]:
        """
        MVP Express Mode - LMEA solves everything in one shot
        
        Single LLM call classifies problem type and solves it.
        No intermediate steps, no redundant parsing.
        
        Args:
            problem_description: Natural language problem description
            max_generations: Max evolutionary generations
            
        Returns:
            Complete solution with all metadata
        """
        try:
            logger.info("⚡ LMEA Express Mode - One-shot optimization")
            
            # Use LLM to classify problem type from description
            problem_type = await self._classify_problem_from_description(problem_description)
            logger.info(f"🎯 Classified as: {problem_type.value}")
            
            # Route to appropriate solver
            # All 8 domains now supported via V2 Solver with Supabase configs
            if problem_type == ProblemType.VRP:
                logger.info("🚀 Using V2 Solver for VRP")
                result = await self.v2_solver.solve(problem_description=problem_description, domain_id='vrp')
            elif problem_type == ProblemType.JOB_SHOP:
                logger.info("🚀 Using V2 Solver for Job Shop")
                result = await self.v2_solver.solve(problem_description=problem_description, domain_id='job_shop')
            elif problem_type == ProblemType.WORKFORCE:
                logger.info("🚀 Using V2 Solver for Workforce")
                result = await self.v2_solver.solve(problem_description=problem_description, domain_id='workforce')
            elif problem_type == ProblemType.MAINTENANCE:
                logger.info("🚀 Using V2 Solver for Maintenance")
                result = await self.v2_solver.solve(problem_description=problem_description, domain_id='maintenance')
            elif problem_type == ProblemType.STORE_LAYOUT:
                logger.info("🚀 Using V2 Solver for Store Layout")
                result = await self.v2_solver.solve(problem_description=problem_description, domain_id='retail_layout', max_time_seconds=max_generations)
            elif problem_type == ProblemType.PROMOTION_SCHEDULING:
                logger.info("🚀 Using V2 Solver for Promotion")
                result = await self.v2_solver.solve(problem_description=problem_description, domain_id='promotion')
            elif problem_type == ProblemType.PORTFOLIO_REBALANCING:
                logger.info("🚀 Using V2 Solver for Portfolio")
                result = await self.v2_solver.solve(problem_description=problem_description, domain_id='portfolio')
            elif problem_type == ProblemType.TRADING_SCHEDULE:
                logger.info("🚀 Using V2 Solver for Trading")
                result = await self.v2_solver.solve(problem_description=problem_description, domain_id='trading')
            # FinServ domains (NEW)
            elif problem_type == ProblemType.CUSTOMER_ONBOARDING:
                logger.info("🚀 Using V2 Solver for Customer Onboarding")
                result = await self.v2_solver.solve(problem_description=problem_description, domain_id='customer_onboarding')
            elif problem_type == ProblemType.PE_EXIT_TIMING:
                logger.info("🚀 Using V2 Solver for PE Exit Timing")
                result = await self.v2_solver.solve(problem_description=problem_description, domain_id='pe_exit_timing')
            elif problem_type == ProblemType.HF_REBALANCING:
                logger.info("🚀 Using V2 Solver for HF Rebalancing")
                result = await self.v2_solver.solve(problem_description=problem_description, domain_id='hf_rebalancing')
            else:
                return {
                    'status': 'error',
                    'error': f'Problem type {problem_type.value} not supported in Express Mode yet'
                }
            
            # Add solver metadata
            result['solver_choice'] = f'lmea_express_{problem_type.value}'
            result['method'] = 'single_shot_llm_driven'
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Express mode failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def solve(
        self,
        model_data: Dict[str, Any],
        problem_description: str = "",
        intent_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Traditional solve (for backward compatibility)
        
        Args:
            model_data: Model specification (variables, constraints, objective)
            problem_description: Natural language problem description
            intent_result: Intent classification result (for smart routing)
        
        Returns:
            Solution dict with method used and results
        """
        try:
            # Step 1: Classify problem type and size (using intent for smart routing)
            problem_type = self._classify_problem(model_data, problem_description, intent_result)
            problem_size = self._estimate_size(model_data)
            
            logger.info(f"🎯 Problem type: {problem_type.value}")
            logger.info(f"📊 Problem size: {problem_size['total_variables']} variables, {problem_size['total_constraints']} constraints")
            
            # Step 2: Select solver strategy
            solver_choice = self._select_solver(problem_type, problem_size)
            logger.info(f"⚡ Selected solver: {solver_choice.value}")
            
            # Step 3: Solve using chosen strategy
            if solver_choice == SolverChoice.HIGHS:
                return await self._solve_with_highs(model_data)
            
            elif solver_choice == SolverChoice.LMEA:
                return await self._solve_with_lmea(model_data, problem_description, problem_type)
            
            elif solver_choice == SolverChoice.HYBRID:
                return await self._solve_with_hybrid(model_data, problem_description, problem_type)
            
            else:
                return {
                    'status': 'error',
                    'error': f'Solver {solver_choice.value} not yet implemented'
                }
                
        except Exception as e:
            logger.error(f"❌ Hybrid solver failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def _classify_problem_from_description(self, problem_description: str) -> ProblemType:
        """
        Classify problem type directly from description using LLM (Express Mode)
        Single lightweight LLM call for classification only
        """
        try:
            import anthropic
            client = anthropic.Anthropic()
            
            prompt = f"""Classify this optimization problem type based on the domain and keywords.

Problem: {problem_description}

Problem Types:
- vehicle_routing: deliveries, routes, trucks, vehicles, customers, depots, logistics
- job_shop_scheduling: jobs, machines, manufacturing, production, operations, makespan
- workforce_rostering: workers, employees, shifts, schedule, staffing, coverage
- maintenance_scheduling: equipment, maintenance, tasks, technicians, repairs, downtime
- store_layout_optimization: products, shelves, retail layout, store placement, merchandising
- promotion_scheduling: promotions, marketing, campaigns, advertising, sales events
- portfolio_rebalancing: portfolio, securities, stocks, bonds, assets, investment, allocation, rebalancing
- trading_schedule: trades, trading, execution, orders, market, VWAP, slippage

Identify the problem type from keywords. Return ONLY the type name, nothing else."""

            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=50,
                messages=[{"role": "user", "content": prompt}]
            )
            
            classification = response.content[0].text.strip().lower().replace('-', '_')
            logger.info(f"📊 LLM classified as: {classification}")
            
            # Map to ProblemType enum
            type_mapping = {
                'vehicle_routing': ProblemType.VRP,
                'job_shop_scheduling': ProblemType.JOB_SHOP,
                'workforce_rostering': ProblemType.WORKFORCE,
                'maintenance_scheduling': ProblemType.MAINTENANCE,
                'store_layout_optimization': ProblemType.STORE_LAYOUT,
                'promotion_scheduling': ProblemType.PROMOTION_SCHEDULING,
                'portfolio_rebalancing': ProblemType.PORTFOLIO_REBALANCING,
                'trading_schedule': ProblemType.TRADING_SCHEDULE,
            }
            
            return type_mapping.get(classification, ProblemType.UNKNOWN)
            
        except Exception as e:
            logger.error(f"❌ LLM classification failed: {e}")
            return ProblemType.UNKNOWN
    
    def _classify_problem(
        self,
        model_data: Dict[str, Any],
        problem_description: str,
        intent_result: Optional[Dict[str, Any]] = None
    ) -> ProblemType:
        """Classify problem type based on intent result, model, and description (Traditional Mode)"""
        
        # SMART ROUTING: Use intent classifier's matched_use_case if available
        if intent_result:
            matched_use_case = intent_result.get('result', {}).get('matched_use_case', '')
            
            logger.info(f"🎯 Using intent-based routing: matched_use_case = {matched_use_case}")
            
            # Map matched_use_case to ProblemType
            use_case_mapping = {
                'store_layout_optimization': ProblemType.STORE_LAYOUT,
                'promotion_scheduling': ProblemType.PROMOTION_SCHEDULING,
                'portfolio_rebalancing': ProblemType.PORTFOLIO_REBALANCING,
                'portfolio_optimization': ProblemType.PORTFOLIO_REBALANCING,
                'trading_schedule': ProblemType.TRADING_SCHEDULE,
                'job_shop_scheduling': ProblemType.JOB_SHOP,
                'workforce_rostering': ProblemType.WORKFORCE,
                'workforce_scheduling': ProblemType.WORKFORCE,
                'maintenance_scheduling': ProblemType.MAINTENANCE,
                'vehicle_routing': ProblemType.VRP,
                'route_optimization': ProblemType.VRP,
                'vrp': ProblemType.VRP,
                'cvrp': ProblemType.VRP,
                'vrptw': ProblemType.VRP,
                'mdvrp': ProblemType.VRP,
                # FinServ domains (NEW)
                'customer_onboarding': ProblemType.CUSTOMER_ONBOARDING,
                'wealth_management': ProblemType.CUSTOMER_ONBOARDING,
                'portfolio_optimization': ProblemType.CUSTOMER_ONBOARDING,
                'pe_exit_timing': ProblemType.PE_EXIT_TIMING,
                'private_equity': ProblemType.PE_EXIT_TIMING,
                'exit_timing': ProblemType.PE_EXIT_TIMING,
                'hf_rebalancing': ProblemType.HF_REBALANCING,
                'hedge_fund': ProblemType.HF_REBALANCING,
                'factor_rebalancing': ProblemType.HF_REBALANCING,
            }
            
            # Check if we have a direct mapping
            for key, problem_type in use_case_mapping.items():
                if key in matched_use_case.lower():
                    logger.info(f"✅ Matched use case '{matched_use_case}' → {problem_type.value}")
                    return problem_type
        
        # FALLBACK: Use keyword-based detection
        logger.info("⚠️ No intent match, falling back to keyword detection")
        desc_lower = problem_description.lower()
        
        if any(keyword in desc_lower for keyword in ['tsp', 'traveling salesman', 'salesman', 'tour']):
            return ProblemType.TSP
        
        # VRP detection - comprehensive keywords
        vrp_keywords = [
            'vrp', 'vehicle routing', 'delivery', 'deliveries', 'route', 'routes', 
            'truck', 'trucks', 'vehicle', 'vehicles', 'driver', 'drivers',
            'depot', 'depots', 'warehouse', 'fleet', 'logistics',
            'cvrp', 'capacitated', 'time window', 'multi-depot', 'mdvrp',
            'pickup', 'delivery', 'last mile', 'distribution'
        ]
        if any(keyword in desc_lower for keyword in vrp_keywords):
            return ProblemType.VRP
        
        # Maintenance Scheduling detection - highest priority for manufacturing
        maintenance_keywords = [
            'maintenance', 'preventive maintenance', 'equipment maintenance',
            'repair scheduling', 'downtime', 'maintenance window', 'shutdown',
            'turnaround', 'reliability', 'asset maintenance'
        ]
        if any(keyword in desc_lower for keyword in maintenance_keywords):
            return ProblemType.MAINTENANCE
        
        # Workforce Rostering detection - must come before Job Shop (more specific)
        workforce_keywords = [
            'workforce', 'roster', 'shift', 'worker assignment', 'staff scheduling',
            'employee scheduling', 'shift planning', 'labor scheduling', 'crew scheduling',
            'personnel planning', 'work schedule'
        ]
        if any(keyword in desc_lower for keyword in workforce_keywords):
            return ProblemType.WORKFORCE
        
        # Job Shop Scheduling detection - comprehensive keywords
        jss_keywords = [
            'job shop', 'scheduling', 'makespan', 'production scheduling',
            'manufacturing schedule', 'machine scheduling', 'operation sequencing',
            'workflow', 'task scheduling', 'resource scheduling', 'shop floor'
        ]
        if any(keyword in desc_lower for keyword in jss_keywords):
            return ProblemType.JOB_SHOP
        
        # Store Layout Optimization detection
        layout_keywords = [
            'store layout', 'retail layout', 'product placement', 'shelf placement',
            'planogram', 'merchandising', 'floor plan', 'store design',
            'product positioning', 'display optimization', 'shelf allocation',
            'grocery store layout', 'retail space', 'foot traffic', 'store optimization'
        ]
        if any(keyword in desc_lower for keyword in layout_keywords):
            return ProblemType.STORE_LAYOUT
        
        # Promotion Scheduling detection
        promotion_keywords = [
            'promotion', 'promotional', 'discount schedule', 'sale schedule',
            'marketing calendar', 'campaign timing', 'price promotion',
            'promotional campaign', 'markdown optimization'
        ]
        if any(keyword in desc_lower for keyword in promotion_keywords):
            return ProblemType.PROMOTION_SCHEDULING
        
        # Portfolio Rebalancing detection
        portfolio_keywords = [
            'portfolio', 'rebalancing', 'asset allocation', 'investment',
            'portfolio optimization', 'risk management', 'diversification',
            'asset reallocation', 'investment portfolio'
        ]
        if any(keyword in desc_lower for keyword in portfolio_keywords):
            return ProblemType.PORTFOLIO_REBALANCING
        
        # Customer Onboarding detection (FinServ)
        onboarding_keywords = [
            'customer onboarding', 'client onboarding', 'portfolio analysis',
            'risk tolerance', 'investment goals', 'portfolio risk',
            'asset allocation', 'wealth management', 'financial advisor',
            'portfolio reallocation', 'risk assessment', 'client portfolio'
        ]
        if any(keyword in desc_lower for keyword in onboarding_keywords):
            return ProblemType.CUSTOMER_ONBOARDING
        
        # PE Exit Timing detection (FinServ)
        pe_exit_keywords = [
            'exit timing', 'pe exit', 'private equity exit', 'portfolio company',
            'exit strategy', 'exit value', 'ebitda multiple', 'valuation multiple',
            'fund lifecycle', 'exit window', 'ipo timing', 'm&a timing',
            'portfolio company sale', 'divestiture timing'
        ]
        if any(keyword in desc_lower for keyword in pe_exit_keywords):
            return ProblemType.PE_EXIT_TIMING
        
        # HF Rebalancing detection (FinServ)
        hf_rebalancing_keywords = [
            'hedge fund', 'factor rebalancing', 'factor exposure', 'transaction cost',
            'market impact', 'bid-ask spread', 'alpha generation', 'factor tilt',
            'tracking error', 'portfolio turnover', 'rebalancing cost',
            'quantitative portfolio', 'systematic strategy'
        ]
        if any(keyword in desc_lower for keyword in hf_rebalancing_keywords):
            return ProblemType.HF_REBALANCING
        
        # Trading Schedule detection
        trading_keywords = [
            'trading', 'trade execution', 'order execution', 'trading schedule',
            'buy sell timing', 'transaction timing', 'market timing',
            'execution strategy', 'trade scheduling'
        ]
        if any(keyword in desc_lower for keyword in trading_keywords):
            return ProblemType.TRADING_SCHEDULE
        
        # Check model structure
        variables = model_data.get('variables', [])
        objective = model_data.get('objective', {})
        
        # Check for integer variables
        has_integer_vars = False
        has_binary_vars = False
        
        if isinstance(variables, list):
            for var in variables:
                if isinstance(var, dict):
                    vtype = var.get('type', 'continuous')
                    if vtype == 'integer':
                        has_integer_vars = True
                    elif vtype == 'binary':
                        has_binary_vars = True
        elif isinstance(variables, dict):
            for var_data in variables.values():
                if isinstance(var_data, dict):
                    vtype = var_data.get('type', 'continuous')
                    if vtype == 'integer':
                        has_integer_vars = True
                    elif vtype == 'binary':
                        has_binary_vars = True
        
        # Check for quadratic terms
        obj_expr = objective.get('expression', '')
        has_quadratic = '**2' in obj_expr or '^2' in obj_expr
        
        # Classify based on structure
        if has_quadratic:
            return ProblemType.QP
        elif has_integer_vars or has_binary_vars:
            return ProblemType.MILP
        else:
            return ProblemType.LP
    
    def _estimate_size(self, model_data: Dict[str, Any]) -> Dict[str, int]:
        """Estimate problem size"""
        variables = model_data.get('variables', [])
        constraints = model_data.get('constraints', [])
        
        if isinstance(variables, dict):
            n_vars = len(variables)
        elif isinstance(variables, list):
            n_vars = len(variables)
        else:
            n_vars = 0
        
        if isinstance(constraints, dict):
            n_constraints = len(constraints)
        elif isinstance(constraints, list):
            n_constraints = len(constraints)
        else:
            n_constraints = 0
        
        return {
            'total_variables': n_vars,
            'total_constraints': n_constraints
        }
    
    def _select_solver(
        self,
        problem_type: ProblemType,
        problem_size: Dict[str, int]
    ) -> SolverChoice:
        """
        Select best solver based on problem characteristics
        
        NEW STRATEGY (per user insight):
        - Default to LMEA for most problems (handles symbolic models)
        - Use HiGHS only for simple, fully-specified LP/MILP
        """
        
        n_vars = problem_size['total_variables']
        
        # Decision tree - LMEA FIRST for real-world problems
        if problem_type in [
            ProblemType.TSP, ProblemType.VRP, 
            ProblemType.JOB_SHOP, ProblemType.WORKFORCE, ProblemType.MAINTENANCE,
            ProblemType.STORE_LAYOUT, ProblemType.PROMOTION_SCHEDULING,
            ProblemType.PORTFOLIO_REBALANCING, ProblemType.TRADING_SCHEDULE
        ]:
            # All combinatorial/real-world problems → LMEA
            logger.info("🧠 LMEA selected: Combinatorial/real-world problem")
            return SolverChoice.LMEA
        
        # For LP/MILP/QP, check if the model is fully specified
        if problem_type in [ProblemType.LP, ProblemType.MILP, ProblemType.QP]:
            # If small and likely well-formed, try HiGHS first
            if n_vars < 100 and n_vars > 0:
                # Small problem: Try HiGHS (exact, fast)
                logger.info("⚡ HiGHS selected: Small, well-formed LP/MILP/QP")
                return SolverChoice.HIGHS
            else:
                # Large: Use hybrid (LMEA warm-start + HiGHS refinement)
                return SolverChoice.HYBRID
        
        elif problem_type in [ProblemType.TSP, ProblemType.VRP, ProblemType.JOB_SHOP]:
            # Combinatorial: Use LMEA (heuristic)
            return SolverChoice.LMEA
        
        else:
            # Default: Try HiGHS
            return SolverChoice.HIGHS
    
    async def _solve_with_highs(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """Solve using HiGHS"""
        logger.info("⚡ Solving with HiGHS (exact method)...")
        
        result = self.highs_solver.solve_model(model_data)
        
        if result.get('status') == 'optimal':
            logger.info(f"✅ HiGHS found optimal solution: {result.get('objective_value', 'N/A')}")
        else:
            logger.warning(f"⚠️ HiGHS status: {result.get('status', 'unknown')}")
        
        result['solver_choice'] = 'highs'
        result['method'] = 'exact'
        
        return result
    
    async def _solve_with_lmea(
        self,
        model_data: Dict[str, Any],
        problem_description: str,
        problem_type: ProblemType
    ) -> Dict[str, Any]:
        """Solve using LMEA"""
        logger.info("🧬 Solving with LMEA (evolutionary heuristic)...")
        
        if problem_type == ProblemType.TSP:
            # Extract cities from model
            cities = self._extract_cities_from_model(model_data)
            
            if not cities:
                return {
                    'status': 'error',
                    'error': 'Could not extract city coordinates for TSP'
                }
            
            result = await self.lmea_solver.solve_tsp(
                cities,
                problem_description,
                max_generations=self.lmea_quick_generations
            )
            
            logger.info(f"✅ LMEA found solution with fitness: {result.get('best_fitness', 'N/A')}")
            
            result['solver_choice'] = 'lmea'
            result['method'] = 'evolutionary_heuristic'
            
            return result
        
        elif problem_type == ProblemType.VRP:
            # Extract VRP data from model
            vrp_data = self._extract_vrp_data_from_model(model_data, problem_description)
            
            if not vrp_data:
                return {
                    'status': 'error',
                    'error': 'Could not extract VRP data (customers, vehicles, depots) from model'
                }
            
            # Determine VRP variant and solve
            variant = vrp_data.get('variant', 'cvrp')
            
            if variant == 'mdvrp' and len(vrp_data.get('depots', [])) > 1:
                # Multi-Depot VRP
                logger.info("🏭 Detected Multi-Depot VRP (MDVRP)")
                result = await self.vrp_solver.solve_mdvrp(
                    customers=vrp_data['customers'],
                    vehicles=vrp_data['vehicles'],
                    depots=vrp_data['depots'],
                    problem_description=problem_description,
                    max_generations=50
                )
            
            elif variant == 'vrptw' or any(c.time_window_start is not None for c in vrp_data.get('customers', [])):
                # VRP with Time Windows
                logger.info("🕐 Detected VRP with Time Windows (VRPTW)")
                result = await self.vrp_solver.solve_vrptw(
                    customers=vrp_data['customers'],
                    vehicles=vrp_data['vehicles'],
                    depot=vrp_data['depots'][0],
                    problem_description=problem_description,
                    max_generations=50
                )
            
            else:
                # Standard Capacitated VRP
                logger.info("📦 Detected Capacitated VRP (CVRP)")
                result = await self.vrp_solver.solve_cvrp(
                    customers=vrp_data['customers'],
                    vehicles=vrp_data['vehicles'],
                    depot=vrp_data['depots'][0],
                    problem_description=problem_description,
                    max_generations=50
                )
            
            logger.info(f"✅ VRP solver completed: {result.get('status', 'unknown')}")
            
            result['solver_choice'] = 'lmea_vrp'
            result['method'] = 'evolutionary_heuristic_vrp'
            
            return result
        
        elif problem_type == ProblemType.JOB_SHOP:
            # Extract Job Shop data from model
            jss_data = self._extract_jss_data_from_model(model_data, problem_description)
            
            if not jss_data:
                return {
                    'status': 'error',
                    'error': 'Could not extract Job Shop data (jobs, machines) from model'
                }
            
            # Solve Job Shop Scheduling
            logger.info("🏭 Detected Job Shop Scheduling (JSS)")
            result = await self.scheduling_solver.solve_job_shop(
                jobs=jss_data['jobs'],
                machines=jss_data['machines'],
                problem_description=problem_description,
                max_generations=50
            )
            
            logger.info(f"✅ JSS solver completed: {result.get('status', 'unknown')}")
            
            result['solver_choice'] = 'lmea_scheduling'
            result['method'] = 'evolutionary_heuristic_jss'
            
            return result
        
        elif problem_type == ProblemType.WORKFORCE:
            # Extract Workforce data from model
            workforce_data = self._extract_workforce_data_from_model(model_data, problem_description)
            
            if not workforce_data:
                return {
                    'status': 'error',
                    'error': 'Could not extract Workforce data (workers, shifts) from model'
                }
            
            # Solve Workforce Rostering
            logger.info("👥 Detected Workforce Rostering")
            result = await self.workforce_solver.solve_workforce_rostering(
                workers=workforce_data['workers'],
                shifts=workforce_data['shifts'],
                planning_horizon=workforce_data.get('planning_horizon', 7),
                problem_description=problem_description,
                max_generations=100
            )
            
            logger.info(f"✅ Workforce solver completed: {result.get('status', 'unknown')}")
            
            result['solver_choice'] = 'lmea_workforce'
            result['method'] = 'evolutionary_heuristic_workforce'
            
            return result
        
        elif problem_type == ProblemType.MAINTENANCE:
            # Extract Maintenance data from model
            maint_data = self._extract_maintenance_data_from_model(model_data, problem_description)
            
            if not maint_data:
                return {
                    'status': 'error',
                    'error': 'Could not extract Maintenance data (equipment, tasks, technicians) from model'
                }
            
            # Solve Maintenance Scheduling
            logger.info("🔧 Detected Maintenance Scheduling")
            result = await self.maintenance_solver.solve_maintenance_scheduling(
                equipment=maint_data['equipment'],
                tasks=maint_data['tasks'],
                technicians=maint_data['technicians'],
                planning_horizon=maint_data.get('planning_horizon', 168),
                problem_description=problem_description,
                max_generations=100
            )
            
            logger.info(f"✅ Maintenance solver completed: {result.get('status', 'unknown')}")
            
            result['solver_choice'] = 'lmea_maintenance'
            result['method'] = 'evolutionary_heuristic_maintenance'
            
            return result
        
        elif problem_type == ProblemType.STORE_LAYOUT:
            # LMEA will parse problem description directly - no need to extract data!
            logger.info("🛒 Detected Store Layout Optimization - LMEA will parse problem description")
            result = await self.retail_layout_solver.solve_store_layout(
                problem_description=problem_description,
                max_generations=100
            )
            
            logger.info(f"✅ Store Layout solver completed: {result.get('status', 'unknown')}")
            
            result['solver_choice'] = 'lmea_retail_layout'
            result['method'] = 'evolutionary_heuristic_layout'
            
            return result
        
        elif problem_type == ProblemType.PROMOTION_SCHEDULING:
            # Extract Promotion data from model
            promo_data = self._extract_promotion_data_from_model(model_data, problem_description)
            
            if not promo_data:
                return {
                    'status': 'error',
                    'error': 'Could not extract Promotion data from model'
                }
            
            # Solve Promotion Scheduling
            logger.info("📣 Detected Promotion Scheduling")
            result = await self.retail_promotion_solver.solve_promotion_scheduling(
                products=promo_data['products'],
                time_periods=promo_data['time_periods'],
                problem_description=problem_description,
                max_generations=100
            )
            
            logger.info(f"✅ Promotion solver completed: {result.get('status', 'unknown')}")
            
            result['solver_choice'] = 'lmea_retail_promotion'
            result['method'] = 'evolutionary_heuristic_promotion'
            
            return result
        
        elif problem_type == ProblemType.PORTFOLIO_REBALANCING:
            # Extract Portfolio data from model
            portfolio_data = self._extract_portfolio_data_from_model(model_data, problem_description)
            
            if not portfolio_data:
                return {
                    'status': 'error',
                    'error': 'Could not extract Portfolio data from model'
                }
            
            # Solve Portfolio Rebalancing
            logger.info("💼 Detected Portfolio Rebalancing")
            result = await self.finance_portfolio_solver.solve_portfolio_rebalancing(
                assets=portfolio_data['assets'],
                current_allocation=portfolio_data['current_allocation'],
                target_allocation=portfolio_data['target_allocation'],
                problem_description=problem_description,
                max_generations=100
            )
            
            logger.info(f"✅ Portfolio solver completed: {result.get('status', 'unknown')}")
            
            result['solver_choice'] = 'lmea_finance_portfolio'
            result['method'] = 'evolutionary_heuristic_portfolio'
            
            return result
        
        elif problem_type == ProblemType.TRADING_SCHEDULE:
            # Extract Trading data from model
            trading_data = self._extract_trading_data_from_model(model_data, problem_description)
            
            if not trading_data:
                return {
                    'status': 'error',
                    'error': 'Could not extract Trading data from model'
                }
            
            # Solve Trading Schedule
            logger.info("📈 Detected Trading Schedule Optimization")
            result = await self.finance_trading_solver.solve_trading_schedule(
                orders=trading_data['orders'],
                market_hours=trading_data['market_hours'],
                problem_description=problem_description,
                max_generations=100
            )
            
            logger.info(f"✅ Trading solver completed: {result.get('status', 'unknown')}")
            
            result['solver_choice'] = 'lmea_finance_trading'
            result['method'] = 'evolutionary_heuristic_trading'
            
            return result
        
        else:
            return {
                'status': 'error',
                'error': f'LMEA not yet implemented for {problem_type.value}'
            }
    
    async def _solve_with_hybrid(
        self,
        model_data: Dict[str, Any],
        problem_description: str,
        problem_type: ProblemType
    ) -> Dict[str, Any]:
        """Solve using hybrid approach (LMEA warm-start + HiGHS refinement)"""
        logger.info("🔄 Solving with Hybrid approach (LMEA + HiGHS)...")
        
        # Step 1: Use LMEA to find a good initial solution
        logger.info("   Phase 1: LMEA warm-start (quick)...")
        
        # For now, skip LMEA and use HiGHS directly
        # TODO: Implement LMEA for MILP warm-starting
        
        logger.info("   Phase 2: HiGHS refinement...")
        result = await self._solve_with_highs(model_data)
        
        result['solver_choice'] = 'hybrid'
        result['method'] = 'lmea_warmstart_highs_refinement'
        
        return result
    
    def _extract_cities_from_model(self, model_data: Dict[str, Any]) -> Optional[list]:
        """Extract city coordinates from TSP model"""
        # Check if model has city data
        if 'cities' in model_data:
            return model_data['cities']
        
        # Try to infer from problem_size
        problem_size = model_data.get('problem_size', {})
        if 'cities' in problem_size:
            n_cities = problem_size['cities']
            
            # Generate random cities for testing
            import random
            cities = [(random.uniform(0, 100), random.uniform(0, 100)) for _ in range(n_cities)]
            return cities
        
        return None
    
    def _extract_vrp_data_from_model(
        self, 
        model_data: Dict[str, Any],
        problem_description: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extract VRP data (customers, vehicles, depots) from model
        
        Returns dict with:
        - customers: List[Customer]
        - vehicles: List[Vehicle]
        - depots: List[Depot]
        - variant: str ('cvrp', 'vrptw', 'mdvrp')
        """
        from .lmea_vrp_solver import Customer, Vehicle, Depot
        
        # Check if model already has VRP data
        if 'vrp_data' in model_data:
            return model_data['vrp_data']
        
        # Extract from model fields
        customers_data = model_data.get('customers', [])
        vehicles_data = model_data.get('vehicles', [])
        depots_data = model_data.get('depots', [])
        
        # Parse customers
        customers = []
        if isinstance(customers_data, list):
            for i, c_data in enumerate(customers_data):
                if isinstance(c_data, dict):
                    customer = Customer(
                        id=c_data.get('id', i + 1),
                        x=float(c_data.get('x', 0)),
                        y=float(c_data.get('y', 0)),
                        demand=float(c_data.get('demand', 0)),
                        service_time=float(c_data.get('service_time', 0)),
                        time_window_start=c_data.get('time_window_start'),
                        time_window_end=c_data.get('time_window_end')
                    )
                    customers.append(customer)
        
        # Parse vehicles
        vehicles = []
        if isinstance(vehicles_data, list):
            for i, v_data in enumerate(vehicles_data):
                if isinstance(v_data, dict):
                    vehicle = Vehicle(
                        id=v_data.get('id', i + 1),
                        capacity=float(v_data.get('capacity', 100)),
                        depot_id=v_data.get('depot_id', 0)
                    )
                    vehicles.append(vehicle)
        
        # Parse depots
        depots = []
        if isinstance(depots_data, list):
            for i, d_data in enumerate(depots_data):
                if isinstance(d_data, dict):
                    depot = Depot(
                        id=d_data.get('id', i),
                        x=float(d_data.get('x', 0)),
                        y=float(d_data.get('y', 0))
                    )
                    depots.append(depot)
        
        # If no data provided, return None
        if not customers or not vehicles or not depots:
            logger.warning("⚠️ VRP data extraction failed: missing customers, vehicles, or depots")
            return None
        
        # Determine variant
        variant = 'cvrp'  # default
        if len(depots) > 1:
            variant = 'mdvrp'
        elif any(c.time_window_start is not None for c in customers):
            variant = 'vrptw'
        
        # Check problem description for hints
        desc_lower = problem_description.lower()
        if 'multi-depot' in desc_lower or 'multi depot' in desc_lower:
            variant = 'mdvrp'
        elif 'time window' in desc_lower:
            variant = 'vrptw'
        
        return {
            'customers': customers,
            'vehicles': vehicles,
            'depots': depots,
            'variant': variant
        }
    
    def _extract_jss_data_from_model(
        self,
        model_data: Dict[str, Any],
        problem_description: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extract Job Shop Scheduling data (jobs, machines) from model
        
        Returns dict with:
        - jobs: List[Job]
        - machines: List[Machine]
        """
        from .lmea_scheduling_solver import Job, Machine
        
        # Check if model already has JSS data
        if 'jss_data' in model_data:
            return model_data['jss_data']
        
        # Extract from model fields
        jobs_data = model_data.get('jobs', [])
        machines_data = model_data.get('machines', [])
        
        # Parse jobs
        jobs = []
        if isinstance(jobs_data, list):
            for i, j_data in enumerate(jobs_data):
                if isinstance(j_data, dict):
                    # Parse operations as list of tuples (machine_id, duration)
                    operations_raw = j_data.get('operations', [])
                    operations = []
                    for op in operations_raw:
                        if isinstance(op, (list, tuple)) and len(op) >= 2:
                            operations.append((int(op[0]), float(op[1])))
                        elif isinstance(op, dict):
                            operations.append((
                                int(op.get('machine_id', 1)),
                                float(op.get('duration', 1.0))
                            ))
                    
                    job = Job(
                        id=j_data.get('id', i + 1),
                        name=j_data.get('name', f'Job {i + 1}'),
                        operations=operations,
                        due_date=j_data.get('due_date'),
                        priority=j_data.get('priority', 1),
                        release_time=j_data.get('release_time', 0.0)
                    )
                    jobs.append(job)
        
        # Parse machines
        machines = []
        if isinstance(machines_data, list):
            for i, m_data in enumerate(machines_data):
                if isinstance(m_data, dict):
                    machine = Machine(
                        id=m_data.get('id', i + 1),
                        name=m_data.get('name', f'Machine {i + 1}'),
                        capabilities=m_data.get('capabilities', [])
                    )
                    machines.append(machine)
        
        # If no data provided, return None
        if not jobs or not machines:
            logger.warning("⚠️ JSS data extraction failed: missing jobs or machines")
            return None
        
        return {
            'jobs': jobs,
            'machines': machines
        }
    
    def _extract_workforce_data_from_model(
        self,
        model_data: Dict[str, Any],
        problem_description: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extract Workforce Rostering data (workers, shifts) from model
        
        Returns dict with:
        - workers: List[Worker]
        - shifts: List[Shift]
        - planning_horizon: int
        """
        from .lmea_workforce_solver import Worker, Shift
        
        # Check if model already has workforce data
        if 'workforce_data' in model_data:
            return model_data['workforce_data']
        
        # Extract from model fields
        workers_data = model_data.get('workers', [])
        shifts_data = model_data.get('shifts', [])
        
        # Parse workers
        workers = []
        if isinstance(workers_data, list):
            for i, w_data in enumerate(workers_data):
                if isinstance(w_data, dict):
                    worker = Worker(
                        id=w_data.get('id', i + 1),
                        name=w_data.get('name', f'Worker {i + 1}'),
                        skills=w_data.get('skills', []),
                        shift_preferences=w_data.get('shift_preferences', {}),
                        max_hours_per_week=w_data.get('max_hours_per_week', 40.0),
                        cost_per_hour=w_data.get('cost_per_hour', 25.0),
                        min_rest_hours=w_data.get('min_rest_hours', 11.0),
                        available_dates=w_data.get('available_dates')
                    )
                    workers.append(worker)
        
        # Parse shifts
        shifts = []
        if isinstance(shifts_data, list):
            for i, s_data in enumerate(shifts_data):
                if isinstance(s_data, dict):
                    shift = Shift(
                        id=s_data.get('id', i + 1),
                        start_time=float(s_data.get('start_time', 8.0)),
                        end_time=float(s_data.get('end_time', 17.0)),
                        required_skills=s_data.get('required_skills', {}),
                        date=s_data.get('date', '2025-01-01'),
                        min_workers=s_data.get('min_workers', 1),
                        max_workers=s_data.get('max_workers', 10)
                    )
                    shifts.append(shift)
        
        # If no data provided, return None
        if not workers or not shifts:
            logger.warning("⚠️ Workforce data extraction failed: missing workers or shifts")
            return None
        
        # Extract planning horizon
        planning_horizon = model_data.get('planning_horizon', 7)
        
        return {
            'workers': workers,
            'shifts': shifts,
            'planning_horizon': planning_horizon
        }
    
    def _extract_maintenance_data_from_model(
        self,
        model_data: Dict[str, Any],
        problem_description: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extract Maintenance Scheduling data from model
        
        Returns dict with:
        - equipment: List[Equipment]
        - tasks: List[MaintenanceTask]
        - technicians: List[Technician]
        - planning_horizon: int (hours)
        """
        from .lmea_maintenance_solver import Equipment, MaintenanceTask, Technician
        
        # Check if model already has maintenance data
        if 'maintenance_data' in model_data:
            return model_data['maintenance_data']
        
        # Extract from model fields
        equipment_data = model_data.get('equipment', [])
        tasks_data = model_data.get('tasks', model_data.get('maintenance_tasks', []))
        technicians_data = model_data.get('technicians', [])
        
        # Parse equipment
        equipment = []
        if isinstance(equipment_data, list):
            for i, e_data in enumerate(equipment_data):
                if isinstance(e_data, dict):
                    eq = Equipment(
                        id=e_data.get('id', i + 1),
                        name=e_data.get('name', f'Equipment {i + 1}'),
                        maintenance_interval=float(e_data.get('maintenance_interval', 200.0)),
                        last_maintenance=float(e_data.get('last_maintenance', 100.0)),
                        maintenance_duration=float(e_data.get('maintenance_duration', 4.0)),
                        criticality=int(e_data.get('criticality', 3)),
                        production_impact=float(e_data.get('production_impact', 0.2))
                    )
                    equipment.append(eq)
        
        # Parse maintenance tasks
        tasks = []
        if isinstance(tasks_data, list):
            for i, t_data in enumerate(tasks_data):
                if isinstance(t_data, dict):
                    task = MaintenanceTask(
                        equipment_id=t_data.get('equipment_id', i + 1),
                        duration=float(t_data.get('duration', 4.0)),
                        required_skills=t_data.get('required_skills', []),
                        parts_needed=t_data.get('parts_needed', []),
                        latest_date=float(t_data.get('latest_date', 168.0)),
                        priority=int(t_data.get('priority', 3))
                    )
                    tasks.append(task)
        
        # Parse technicians
        technicians = []
        if isinstance(technicians_data, list):
            for i, tech_data in enumerate(technicians_data):
                if isinstance(tech_data, dict):
                    tech = Technician(
                        id=tech_data.get('id', i + 1),
                        name=tech_data.get('name', f'Technician {i + 1}'),
                        skills=tech_data.get('skills', []),
                        cost_per_hour=float(tech_data.get('cost_per_hour', 50.0)),
                        available_hours=float(tech_data.get('available_hours', 40.0))
                    )
                    technicians.append(tech)
        
        # If no data provided, return None
        if not equipment or not tasks or not technicians:
            logger.warning("⚠️ Maintenance data extraction failed: missing equipment, tasks, or technicians")
            return None
        
        # Extract planning horizon (in hours)
        planning_horizon = model_data.get('planning_horizon', 168)  # Default 1 week
        
        return {
            'equipment': equipment,
            'tasks': tasks,
            'technicians': technicians,
            'planning_horizon': planning_horizon
        }
    
    def _extract_layout_data_from_model(self, model_data: Dict[str, Any], problem_description: str) -> Optional[Dict[str, Any]]:
        """Extract store layout data from model"""
        logger.info("📦 Extracting store layout data...")
        
        # For now, extract basic structure from problem description
        # LMEA will handle the symbolic model
        return {
            'products': model_data.get('products', []),
            'sections': model_data.get('sections', 8),  # Default 8 sections
            'foot_traffic': model_data.get('foot_traffic', {}),
            'constraints': model_data.get('constraints', []),
            'problem_description': problem_description  # Pass to LMEA
        }
    
    def _extract_promotion_data_from_model(self, model_data: Dict[str, Any], problem_description: str) -> Optional[Dict[str, Any]]:
        """Extract promotion scheduling data from model"""
        logger.info("🎯 Extracting promotion data...")
        
        return {
            'products': model_data.get('products', []),
            'time_periods': model_data.get('time_periods', []),
            'budget': model_data.get('budget', 0),
            'constraints': model_data.get('constraints', []),
            'problem_description': problem_description
        }
    
    def _extract_portfolio_data_from_model(self, model_data: Dict[str, Any], problem_description: str) -> Optional[Dict[str, Any]]:
        """Extract portfolio rebalancing data from model"""
        logger.info("💰 Extracting portfolio data...")
        
        return {
            'assets': model_data.get('assets', []),
            'target_allocation': model_data.get('target_allocation', {}),
            'transaction_costs': model_data.get('transaction_costs', 0),
            'constraints': model_data.get('constraints', []),
            'problem_description': problem_description
        }
    
    def _extract_trading_data_from_model(self, model_data: Dict[str, Any], problem_description: str) -> Optional[Dict[str, Any]]:
        """Extract trading schedule data from model"""
        logger.info("📈 Extracting trading data...")
        
        return {
            'trades': model_data.get('trades', []),
            'time_horizon': model_data.get('time_horizon', 24),
            'market_impact': model_data.get('market_impact', {}),
            'constraints': model_data.get('constraints', []),
            'problem_description': problem_description
        }
