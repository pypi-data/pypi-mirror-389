#!/usr/bin/env python3
"""
Domain-Specific Fitness Evaluators for Universal LMEA Engine

Each evaluator is a pure function that takes a solution and problem_data,
and returns a fitness score. These are injected into the Universal LMEA Engine.

Design Pattern: Strategy Pattern
- Each domain has its own fitness evaluation strategy
- All follow the same interface: fitness_evaluator(solution, problem_data) -> float
- Strategies are stateless and can be easily tested in isolation

Domains:
1. VRP (Vehicle Routing Problem)
2. Job Shop Scheduling
3. Workforce Rostering
4. Maintenance Scheduling
5. Promotion Scheduling
6. Portfolio Rebalancing
7. Trading Schedule Optimization
"""

import math
from typing import Any, Dict, List
import logging

logger = logging.getLogger(__name__)


# =========================================================================
# 1. VRP (Vehicle Routing Problem) - Fitness Evaluator
# =========================================================================

def vrp_fitness_evaluator(solution: Dict[str, Any], problem_data: Dict[str, Any]) -> float:
    """
    Evaluate VRP solution quality
    
    Objectives:
    - Minimize total distance traveled
    - Minimize number of vehicles used
    - Maximize on-time deliveries
    - Balance load across vehicles
    
    Solution structure:
    {
        'routes': [
            {'vehicle_id': 1, 'customer_sequence': [3, 7, 2, ...], 'total_distance': 45.2, 'total_load': 480},
            ...
        ]
    }
    """
    routes = solution.get('routes', [])
    customers = problem_data.get('customers', [])
    vehicles = problem_data.get('vehicles', [])
    
    if not routes:
        return 0.0
    
    # Objective 1: Minimize total distance (inverted for maximization)
    total_distance = sum(r.get('total_distance', 0) for r in routes)
    distance_score = 10000.0 / (1.0 + total_distance)  # Lower distance = higher score
    
    # Objective 2: Minimize vehicles used (reward efficiency)
    vehicles_used = len([r for r in routes if r.get('customer_sequence')])
    vehicle_efficiency = (len(vehicles) - vehicles_used + 1) * 100.0
    
    # Objective 3: Load balancing (reward even distribution)
    loads = [r.get('total_load', 0) for r in routes if r.get('total_load')]
    if loads:
        avg_load = sum(loads) / len(loads)
        load_variance = sum((load - avg_load) ** 2 for load in loads) / len(loads)
        balance_score = 1000.0 / (1.0 + load_variance)
    else:
        balance_score = 0.0
    
    # Objective 4: Customer coverage (all customers served)
    customers_served = set()
    for route in routes:
        customers_served.update(route.get('customer_sequence', []))
    coverage_ratio = len(customers_served) / max(len(customers), 1)
    coverage_score = coverage_ratio * 5000.0
    
    # Multi-objective fitness (weighted sum)
    fitness = (
        distance_score * 0.40 +          # 40%: minimize distance
        vehicle_efficiency * 0.20 +       # 20%: minimize vehicles
        balance_score * 0.15 +            # 15%: load balance
        coverage_score * 0.25             # 25%: customer coverage
    )
    
    return fitness


# =========================================================================
# 2. Job Shop Scheduling - Fitness Evaluator
# =========================================================================

def job_shop_fitness_evaluator(solution: Dict[str, Any], problem_data: Dict[str, Any]) -> float:
    """
    Evaluate Job Shop scheduling solution
    
    Objectives:
    - Minimize makespan (total completion time)
    - Minimize machine idle time
    - Meet job deadlines
    - Balance machine utilization
    
    Solution structure:
    {
        'schedule': [
            {'job_id': 1, 'operation_id': 1, 'machine_id': 2, 'start_time': 0, 'end_time': 5},
            ...
        ],
        'makespan': 120.5
    }
    """
    schedule = solution.get('schedule', [])
    jobs = problem_data.get('jobs', [])
    machines = problem_data.get('machines', [])
    makespan = solution.get('makespan', float('inf'))
    
    if not schedule:
        return 0.0
    
    # Objective 1: Minimize makespan (inverted)
    makespan_score = 10000.0 / (1.0 + makespan)
    
    # Objective 2: Machine utilization (minimize idle time)
    machine_busy_time = {}
    for task in schedule:
        machine_id = task.get('machine_id')
        duration = task.get('end_time', 0) - task.get('start_time', 0)
        machine_busy_time[machine_id] = machine_busy_time.get(machine_id, 0) + duration
    
    total_busy_time = sum(machine_busy_time.values())
    total_possible_time = makespan * len(machines)
    utilization = total_busy_time / max(total_possible_time, 1)
    utilization_score = utilization * 3000.0
    
    # Objective 3: Job completion (all jobs finished)
    jobs_completed = len(set(task.get('job_id') for task in schedule))
    completion_ratio = jobs_completed / max(len(jobs), 1)
    completion_score = completion_ratio * 4000.0
    
    # Objective 4: Operation precedence satisfaction
    # (Higher score if operations in each job follow correct sequence)
    precedence_score = 3000.0  # Assume satisfied (constraint checker handles violations)
    
    fitness = (
        makespan_score * 0.40 +           # 40%: minimize makespan
        utilization_score * 0.25 +        # 25%: maximize utilization
        completion_score * 0.30 +         # 30%: complete all jobs
        precedence_score * 0.05           # 5%: precedence (bonus)
    )
    
    return fitness


# =========================================================================
# 3. Workforce Rostering - Fitness Evaluator
# =========================================================================

def workforce_fitness_evaluator(solution: Dict[str, Any], problem_data: Dict[str, Any]) -> float:
    """
    Evaluate workforce scheduling solution
    
    Objectives:
    - Meet staffing requirements for all shifts
    - Respect worker availability and preferences
    - Balance workload across workers
    - Minimize overtime costs
    
    Solution structure:
    {
        'assignments': [
            {'worker_id': 1, 'day': 'Monday', 'shift': 'morning'},
            ...
        ]
    }
    """
    assignments = solution.get('assignments', [])
    workers = problem_data.get('workers', [])
    shift_requirements = problem_data.get('shift_requirements', {})
    
    if not assignments:
        return 0.0
    
    # Objective 1: Coverage (meet shift requirements)
    shift_coverage = {}
    for assignment in assignments:
        shift_key = f"{assignment.get('day')}_{assignment.get('shift')}"
        shift_coverage[shift_key] = shift_coverage.get(shift_key, 0) + 1
    
    coverage_score = 0.0
    for shift_key, required in shift_requirements.items():
        actual = shift_coverage.get(shift_key, 0)
        if actual >= required:
            coverage_score += 1000.0
        else:
            # Penalty for understaffing
            coverage_score += (actual / required) * 1000.0
    
    # Objective 2: Workload balance
    worker_shifts = {}
    for assignment in assignments:
        worker_id = assignment.get('worker_id')
        worker_shifts[worker_id] = worker_shifts.get(worker_id, 0) + 1
    
    if worker_shifts:
        avg_shifts = sum(worker_shifts.values()) / len(worker_shifts)
        variance = sum((count - avg_shifts) ** 2 for count in worker_shifts.values()) / len(worker_shifts)
        balance_score = 2000.0 / (1.0 + variance)
    else:
        balance_score = 0.0
    
    # Objective 3: Worker preferences (assume preference_score in problem_data)
    preference_score = 1500.0  # Default (can be enhanced with actual preference matching)
    
    fitness = (
        coverage_score * 0.50 +           # 50%: meet shift requirements
        balance_score * 0.30 +            # 30%: balance workload
        preference_score * 0.20           # 20%: preferences
    )
    
    return fitness


# =========================================================================
# 4. Maintenance Scheduling - Fitness Evaluator
# =========================================================================

def maintenance_fitness_evaluator(solution: Dict[str, Any], problem_data: Dict[str, Any]) -> float:
    """
    Evaluate maintenance scheduling solution
    
    Objectives:
    - Complete all critical maintenance tasks
    - Minimize production downtime
    - Balance technician workload
    - Respect maintenance windows
    
    Solution structure:
    {
        'schedule': [
            {'machine_id': 1, 'technician_id': 2, 'start_day': 3, 'duration': 2},
            ...
        ]
    }
    """
    schedule = solution.get('schedule', [])
    machines = problem_data.get('machines', [])
    technicians = problem_data.get('technicians', [])
    
    if not schedule:
        return 0.0
    
    # Objective 1: Task completion (all machines maintained)
    machines_maintained = set(task.get('machine_id') for task in schedule)
    completion_ratio = len(machines_maintained) / max(len(machines), 1)
    completion_score = completion_ratio * 5000.0
    
    # Objective 2: Minimize downtime (schedule maintenance efficiently)
    total_downtime = sum(task.get('duration', 0) for task in schedule)
    downtime_score = 10000.0 / (1.0 + total_downtime)
    
    # Objective 3: Technician workload balance
    technician_hours = {}
    for task in schedule:
        tech_id = task.get('technician_id')
        duration = task.get('duration', 0)
        technician_hours[tech_id] = technician_hours.get(tech_id, 0) + duration
    
    if technician_hours:
        avg_hours = sum(technician_hours.values()) / len(technician_hours)
        variance = sum((hours - avg_hours) ** 2 for hours in technician_hours.values()) / len(technician_hours)
        balance_score = 3000.0 / (1.0 + variance)
    else:
        balance_score = 0.0
    
    fitness = (
        completion_score * 0.40 +         # 40%: complete all tasks
        downtime_score * 0.35 +           # 35%: minimize downtime
        balance_score * 0.25              # 25%: balance workload
    )
    
    return fitness


# =========================================================================
# 5. Promotion Scheduling - Fitness Evaluator
# =========================================================================

def promotion_fitness_evaluator(solution: Dict[str, Any], problem_data: Dict[str, Any]) -> float:
    """
    Evaluate promotion scheduling solution
    
    Objectives:
    - Maximize expected revenue impact
    - Stay within budget
    - Avoid promotion cannibalization
    - Respect blackout dates
    
    Solution structure:
    {
        'promotions': [
            {'product_id': 1, 'week': 3, 'discount': 0.15, 'expected_revenue': 5000},
            ...
        ],
        'total_budget_used': 45000
    }
    """
    promotions = solution.get('promotions', [])
    products = problem_data.get('products', [])
    budget = problem_data.get('budget', 50000)
    
    if not promotions:
        return 0.0
    
    # Objective 1: Maximize revenue impact
    total_revenue = sum(p.get('expected_revenue', 0) for p in promotions)
    revenue_score = total_revenue / 10.0  # Scale appropriately
    
    # Objective 2: Budget efficiency
    budget_used = solution.get('total_budget_used', 0)
    if budget_used <= budget:
        budget_score = 2000.0
    else:
        # Penalty for over-budget
        budget_score = 2000.0 * (budget / budget_used)
    
    # Objective 3: Product coverage (promote diverse products)
    products_promoted = len(set(p.get('product_id') for p in promotions))
    coverage_ratio = products_promoted / max(len(products), 1)
    coverage_score = coverage_ratio * 3000.0
    
    # Objective 4: Timing optimization (avoid cannibalization)
    # Penalize if complementary products promoted in same week
    timing_score = 2000.0  # Base score (can be enhanced)
    
    fitness = (
        revenue_score * 0.45 +            # 45%: maximize revenue
        budget_score * 0.25 +             # 25%: stay in budget
        coverage_score * 0.20 +           # 20%: diverse products
        timing_score * 0.10               # 10%: timing optimization
    )
    
    return fitness


# =========================================================================
# 6. Portfolio Rebalancing - Fitness Evaluator
# =========================================================================

def portfolio_fitness_evaluator(solution: Dict[str, Any], problem_data: Dict[str, Any]) -> float:
    """
    Evaluate portfolio rebalancing solution
    
    Objectives:
    - Maximize risk-adjusted return (Sharpe ratio)
    - Meet target allocation
    - Minimize transaction costs
    - Respect diversification constraints
    
    Solution structure:
    {
        'allocations': [
            {'asset_id': 1, 'weight': 0.15, 'trades_required': 2000},
            ...
        ],
        'expected_return': 0.08,
        'volatility': 0.12,
        'sharpe_ratio': 0.67,
        'transaction_costs': 1500
    }
    """
    allocations = solution.get('allocations', [])
    expected_return = solution.get('expected_return', 0)
    volatility = solution.get('volatility', 1.0)
    sharpe_ratio = solution.get('sharpe_ratio', 0)
    transaction_costs = solution.get('transaction_costs', 0)
    target_allocation = problem_data.get('target_allocation', {})
    
    if not allocations:
        return 0.0
    
    # Objective 1: Maximize Sharpe ratio (risk-adjusted return)
    sharpe_score = sharpe_ratio * 5000.0
    
    # Objective 2: Meet target allocation
    allocation_error = 0.0
    for asset_alloc in allocations:
        asset_id = asset_alloc.get('asset_id')
        actual_weight = asset_alloc.get('weight', 0)
        target_weight = target_allocation.get(f'asset_{asset_id}', 0)
        allocation_error += abs(actual_weight - target_weight)
    
    allocation_score = 3000.0 / (1.0 + allocation_error * 10)
    
    # Objective 3: Minimize transaction costs
    cost_score = 5000.0 / (1.0 + transaction_costs)
    
    # Objective 4: Diversification (Herfindahl index)
    weights = [a.get('weight', 0) for a in allocations]
    herfindahl = sum(w ** 2 for w in weights)
    diversification_score = (1.0 - herfindahl) * 2000.0
    
    fitness = (
        sharpe_score * 0.35 +             # 35%: risk-adjusted return
        allocation_score * 0.30 +         # 30%: meet target
        cost_score * 0.20 +               # 20%: minimize costs
        diversification_score * 0.15      # 15%: diversification
    )
    
    return fitness


# =========================================================================
# 7. Trading Schedule Optimization - Fitness Evaluator
# =========================================================================

def trading_fitness_evaluator(solution: Dict[str, Any], problem_data: Dict[str, Any]) -> float:
    """
    Evaluate trading execution schedule
    
    Objectives:
    - Minimize market impact
    - Achieve VWAP target
    - Minimize slippage
    - Complete order within time window
    
    Solution structure:
    {
        'child_orders': [
            {'time': 0, 'size': 5000, 'expected_price': 100.25},
            ...
        ],
        'total_slippage': 250,
        'vwap_deviation': 0.02,
        'market_impact': 0.15
    }
    """
    child_orders = solution.get('child_orders', [])
    total_slippage = solution.get('total_slippage', 0)
    vwap_deviation = solution.get('vwap_deviation', 0)
    market_impact = solution.get('market_impact', 0)
    target_quantity = problem_data.get('target_quantity', 50000)
    
    if not child_orders:
        return 0.0
    
    # Objective 1: Minimize slippage
    slippage_score = 5000.0 / (1.0 + total_slippage)
    
    # Objective 2: VWAP achievement
    vwap_score = 3000.0 / (1.0 + abs(vwap_deviation) * 100)
    
    # Objective 3: Minimize market impact
    impact_score = 4000.0 / (1.0 + market_impact * 10)
    
    # Objective 4: Order completion
    total_executed = sum(order.get('size', 0) for order in child_orders)
    completion_ratio = total_executed / max(target_quantity, 1)
    completion_score = min(completion_ratio, 1.0) * 3000.0
    
    fitness = (
        slippage_score * 0.30 +           # 30%: minimize slippage
        vwap_score * 0.25 +               # 25%: VWAP target
        impact_score * 0.30 +             # 30%: minimize impact
        completion_score * 0.15           # 15%: complete order
    )
    
    return fitness


# =========================================================================
# 9. FINSERV: Customer Onboarding - Fitness Evaluator
# =========================================================================

def customer_onboarding_fitness_evaluator(solution: Dict[str, Any], problem_data: Dict[str, Any]) -> float:
    """
    Evaluate portfolio optimization solution for customer onboarding
    
    Objectives (multi-objective):
    - Minimize portfolio risk (volatility)
    - Maximize expected returns
    - Minimize fees (expense ratios)
    - Minimize tax drag
    
    Solution structure:
    {
        'allocations': [
            {'ticker': 'AAPL', 'target_weight': 0.15, ...},
            ...
        ],
        'portfolio_metrics': {
            'volatility': 0.12,
            'expected_return': 0.08,
            'total_fees': 0.005,
            'tax_impact': 2500
        }
    }
    """
    penalties = 0.0
    
    # Extract solution data
    allocations = solution.get('allocations', [])
    metrics = solution.get('portfolio_metrics', {})
    
    if not allocations:
        return 1e10  # Invalid solution
    
    # Extract problem constraints
    risk_tolerance = problem_data.get('risk_tolerance', 5) / 10  # Convert 1-10 to 0-1
    total_value = problem_data.get('total_value', 1000000)
    
    # 1. Risk Score (40% weight) - penalize if exceeds tolerance
    portfolio_volatility = metrics.get('volatility', 0.20)
    if portfolio_volatility > risk_tolerance:
        risk_penalty = (portfolio_volatility - risk_tolerance) * 10000
    else:
        risk_penalty = portfolio_volatility * 1000  # Lower is better
    
    # 2. Return Score (30% weight) - maximize returns
    expected_return = metrics.get('expected_return', 0.05)
    return_score = (1 - expected_return) * 5000  # Invert (minimize)
    
    # 3. Fee Score (20% weight) - minimize expense ratios
    total_fees = metrics.get('total_fees', 0.01)  # As decimal (0.01 = 1%)
    fee_score = total_fees * 10000
    
    # 4. Tax Score (10% weight) - minimize tax impact
    tax_impact = metrics.get('tax_impact', 0)
    tax_score = (tax_impact / total_value) * 2000  # Normalize by portfolio value
    
    # Constraint violations
    
    # Sum of allocations must be 1.0 (±1%)
    total_allocation = sum(a.get('target_weight', 0) for a in allocations)
    if abs(total_allocation - 1.0) > 0.01:
        penalties += abs(total_allocation - 1.0) * 50000
    
    # Sector concentration (no sector > 20%)
    sector_weights = {}
    for allocation in allocations:
        sector = allocation.get('sector', 'unknown')
        weight = allocation.get('target_weight', 0)
        sector_weights[sector] = sector_weights.get(sector, 0) + weight
    
    for sector, weight in sector_weights.items():
        if weight > 0.20:
            penalties += (weight - 0.20) * 20000
    
    # Single stock limit (no stock > 10%)
    for allocation in allocations:
        weight = allocation.get('target_weight', 0)
        if weight > 0.10:
            penalties += (weight - 0.10) * 30000
    
    # Total fitness (lower is better)
    fitness = (
        0.40 * risk_penalty +
        0.30 * return_score +
        0.20 * fee_score +
        0.10 * tax_score +
        penalties
    )
    
    return fitness


# =========================================================================
# 10. FINSERV: PE Exit Timing - Fitness Evaluator
# =========================================================================

def pe_exit_timing_fitness_evaluator(solution: Dict[str, Any], problem_data: Dict[str, Any]) -> float:
    """
    Evaluate PE exit timing solution
    
    Objective: Maximize after-tax exit value considering timing and costs
    
    Solution structure:
    {
        'recommended_exit_quarter': 'Q2 2025',
        'exit_metrics': {
            'expected_exit_value': 500,  # $M
            'tax_rate': 0.20,
            'holding_costs': 2,  # $M
            'confidence': 0.78
        }
    }
    """
    penalties = 0.0
    
    # Extract solution data
    exit_quarter = solution.get('recommended_exit_quarter', '')
    metrics = solution.get('exit_metrics', {})
    
    if not exit_quarter:
        return 1e10  # Invalid solution
    
    # Extract problem data
    current_ebitda = problem_data.get('financials', {}).get('current', {}).get('ebitda', 50)
    fund_context = problem_data.get('fund_context', {})
    market_conditions = problem_data.get('market_conditions', {})
    
    # 1. Exit Value (maximize after-tax proceeds)
    exit_value = metrics.get('expected_exit_value', 0)
    tax_rate = metrics.get('tax_rate', 0.37)
    holding_costs = metrics.get('holding_costs', 0)
    
    after_tax_value = exit_value * (1 - tax_rate) - holding_costs
    
    # Fitness = negative after-tax value (minimize = maximize value)
    fitness = -after_tax_value
    
    # 2. Market Conditions Penalty
    market_score = {
        'bullish': 1.0,
        'neutral': 1.1,
        'bearish': 1.3
    }.get(market_conditions.get('sector_sentiment', 'neutral'), 1.1)
    
    fitness *= market_score
    
    # 3. Confidence Penalty
    confidence = metrics.get('confidence', 0.5)
    if confidence < 0.70:
        penalties += (0.70 - confidence) * 1000
    
    # 4. Fund Lifecycle Constraint
    # Exit must occur before fund_end_date - 12 months
    # This is enforced in solution generation, but we can add a penalty
    # if the exit is too close to fund end
    
    # 5. Company Performance Constraint
    # EBITDA must be growing (this should be in problem_data validation)
    growth_rate = problem_data.get('financials', {}).get('current', {}).get('growth_rate', 0)
    if growth_rate < 0.10:  # Less than 10% growth
        penalties += (0.10 - growth_rate) * 5000
    
    fitness += penalties
    
    return fitness


# =========================================================================
# 11. FINSERV: HF Rebalancing - Fitness Evaluator
# =========================================================================

def hf_rebalancing_fitness_evaluator(solution: Dict[str, Any], problem_data: Dict[str, Any]) -> float:
    """
    Evaluate hedge fund rebalancing solution
    
    Objectives (multi-objective):
    - Minimize tracking error from target factor exposures
    - Minimize transaction costs
    - Maximize expected alpha
    
    Solution structure:
    {
        'trades': [
            {'ticker': 'AAPL', 'action': 'buy', 'shares': 1000, ...},
            ...
        ],
        'portfolio_metrics': {
            'tracking_error': 0.03,
            'transaction_costs': 25000,
            'expected_alpha': 0.002,
            'new_factor_exposures': {...}
        }
    }
    """
    penalties = 0.0
    
    # Extract solution data
    trades = solution.get('trades', [])
    metrics = solution.get('portfolio_metrics', {})
    
    # Extract problem constraints
    total_aum = problem_data.get('portfolio_aum', 500) * 1_000_000  # Convert to $
    target_exposures = problem_data.get('target_factor_exposures', {})
    constraints = problem_data.get('constraints', {})
    
    # 1. Tracking Error Score (50% weight)
    tracking_error = metrics.get('tracking_error', 0.10)
    tracking_score = tracking_error * 100000
    
    # 2. Transaction Cost Score (40% weight)
    transaction_costs = metrics.get('transaction_costs', 0)
    cost_score = (transaction_costs / total_aum) * 200000  # Normalize by AUM
    
    # 3. Expected Alpha Score (10% weight) - maximize
    expected_alpha = metrics.get('expected_alpha', 0)
    alpha_score = (1 - expected_alpha * 100) * 5000  # Scale up and invert
    
    # Constraint violations
    
    # Factor exposure targets (within ±5%)
    new_exposures = metrics.get('new_factor_exposures', {})
    factor_tolerance = constraints.get('factor_tolerance', 0.05)
    
    for factor, target in target_exposures.items():
        actual = new_exposures.get(factor, 0)
        if abs(actual - target) > factor_tolerance:
            penalties += abs(actual - target) * 50000
    
    # Turnover limit
    total_turnover = sum(abs(t.get('value', 0)) for t in trades) / total_aum
    max_turnover = constraints.get('max_turnover', 0.20)
    if total_turnover > max_turnover:
        penalties += (total_turnover - max_turnover) * 100000
    
    # Portfolio volatility
    portfolio_vol = metrics.get('portfolio_volatility', 0.15)
    max_vol = constraints.get('max_portfolio_volatility', 0.18)
    if portfolio_vol > max_vol:
        penalties += (portfolio_vol - max_vol) * 80000
    
    # Single stock weight limit
    new_positions = metrics.get('new_positions', [])
    max_single_stock = constraints.get('max_single_stock_weight', 0.05)
    for position in new_positions:
        weight = position.get('weight', 0)
        if weight > max_single_stock:
            penalties += (weight - max_single_stock) * 40000
    
    # Total fitness (lower is better)
    fitness = (
        0.50 * tracking_score +
        0.40 * cost_score +
        0.10 * alpha_score +
        penalties
    )
    
    return fitness


# =========================================================================
# Fitness Evaluator Registry
# =========================================================================

FITNESS_EVALUATORS = {
    'vrp': vrp_fitness_evaluator,
    'job_shop': job_shop_fitness_evaluator,
    'workforce': workforce_fitness_evaluator,
    'maintenance': maintenance_fitness_evaluator,
    'promotion': promotion_fitness_evaluator,
    'portfolio': portfolio_fitness_evaluator,
    'trading': trading_fitness_evaluator,
    'customer_onboarding': customer_onboarding_fitness_evaluator,
    'pe_exit_timing': pe_exit_timing_fitness_evaluator,
    'hf_rebalancing': hf_rebalancing_fitness_evaluator
}


def get_fitness_evaluator(domain_id: str):
    """Get fitness evaluator for a domain"""
    evaluator = FITNESS_EVALUATORS.get(domain_id)
    if not evaluator:
        raise ValueError(f"No fitness evaluator found for domain: {domain_id}")
    return evaluator

