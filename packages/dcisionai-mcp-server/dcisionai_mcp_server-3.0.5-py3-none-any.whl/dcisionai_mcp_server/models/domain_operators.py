#!/usr/bin/env python3
"""
Domain-Specific Operators for Universal LMEA Engine

Provides domain-specific:
1. Solution Initializers: Generate random valid solutions
2. Constraint Checkers: Validate solutions against domain constraints
3. Crossover Operators: Domain-specific recombination (optional, falls back to default)
4. Mutation Operators: Domain-specific perturbation (optional, falls back to default)

These are injected into the Universal LMEA Engine as strategies.
"""

import random
import copy
from typing import Any, Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


# =========================================================================
# VRP (Vehicle Routing Problem) - Operators
# =========================================================================

def vrp_solution_initializer(problem_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate random VRP solution"""
    customers = problem_data.get('customers', [])
    vehicles = problem_data.get('vehicles', [])
    
    if not customers or not vehicles:
        return {'routes': []}
    
    # Randomly assign customers to vehicles
    customer_ids = [c['id'] for c in customers]
    random.shuffle(customer_ids)
    
    # Split customers across vehicles
    routes = []
    customers_per_vehicle = len(customer_ids) // len(vehicles) + 1
    
    for i, vehicle in enumerate(vehicles):
        start_idx = i * customers_per_vehicle
        end_idx = min((i + 1) * customers_per_vehicle, len(customer_ids))
        customer_sequence = customer_ids[start_idx:end_idx]
        
        # Calculate simple distance (can be enhanced with actual routing)
        total_distance = len(customer_sequence) * random.uniform(5, 15)
        total_load = sum(
            next((c['demand'] for c in customers if c['id'] == cid), 0)
            for cid in customer_sequence
        )
        
        routes.append({
            'vehicle_id': vehicle['id'],
            'customer_sequence': customer_sequence,
            'total_distance': total_distance,
            'total_load': total_load
        })
    
    return {'routes': routes}


def vrp_constraint_checker(solution: Dict[str, Any], problem_data: Dict[str, Any]) -> List[str]:
    """Check VRP constraints"""
    violations = []
    routes = solution.get('routes', [])
    customers = problem_data.get('customers', [])
    vehicles = problem_data.get('vehicles', [])
    
    # All customers must be served exactly once
    served_customers = set()
    for route in routes:
        served_customers.update(route.get('customer_sequence', []))
    
    all_customer_ids = {c['id'] for c in customers}
    if served_customers != all_customer_ids:
        violations.append(f"Not all customers served: {len(served_customers)}/{len(all_customer_ids)}")
    
    # Vehicle capacity constraints
    for route in routes:
        vehicle = next((v for v in vehicles if v['id'] == route['vehicle_id']), None)
        if vehicle and route.get('total_load', 0) > vehicle.get('capacity', float('inf')):
            violations.append(f"Vehicle {route['vehicle_id']} exceeds capacity")
    
    return violations


# =========================================================================
# Job Shop Scheduling - Operators
# =========================================================================

def job_shop_solution_initializer(problem_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate random job shop schedule"""
    jobs = problem_data.get('jobs', [])
    machines = problem_data.get('machines', [])
    
    if not jobs or not machines:
        return {'schedule': [], 'makespan': 0}
    
    schedule = []
    machine_availability = {m['id']: 0 for m in machines}
    
    # Simple random scheduling
    for job in jobs:
        job_start = 0
        for operation in job.get('operations', []):
            machine_id = operation.get('machine_id')
            duration = operation.get('duration', 1)
            
            # Schedule at earliest available time on required machine
            start_time = max(job_start, machine_availability.get(machine_id, 0))
            end_time = start_time + duration
            
            schedule.append({
                'job_id': job['id'],
                'operation_id': operation.get('id', 0),
                'machine_id': machine_id,
                'start_time': start_time,
                'end_time': end_time
            })
            
            machine_availability[machine_id] = end_time
            job_start = end_time
    
    makespan = max(task['end_time'] for task in schedule) if schedule else 0
    
    return {'schedule': schedule, 'makespan': makespan}


def job_shop_constraint_checker(solution: Dict[str, Any], problem_data: Dict[str, Any]) -> List[str]:
    """Check job shop constraints"""
    violations = []
    schedule = solution.get('schedule', [])
    jobs = problem_data.get('jobs', [])
    
    # Check operation precedence within each job
    job_operations = {}
    for task in schedule:
        job_id = task['job_id']
        if job_id not in job_operations:
            job_operations[job_id] = []
        job_operations[job_id].append(task)
    
    for job_id, operations in job_operations.items():
        # Sort by operation_id (assuming operation_id indicates sequence)
        operations.sort(key=lambda x: x['operation_id'])
        
        # Check if each operation starts after previous one ends
        for i in range(len(operations) - 1):
            if operations[i+1]['start_time'] < operations[i]['end_time']:
                violations.append(f"Job {job_id} operation precedence violated")
                break
    
    # Check machine conflicts (no two operations on same machine at same time)
    machine_tasks = {}
    for task in schedule:
        machine_id = task['machine_id']
        if machine_id not in machine_tasks:
            machine_tasks[machine_id] = []
        machine_tasks[machine_id].append(task)
    
    for machine_id, tasks in machine_tasks.items():
        tasks.sort(key=lambda x: x['start_time'])
        for i in range(len(tasks) - 1):
            if tasks[i]['end_time'] > tasks[i+1]['start_time']:
                violations.append(f"Machine {machine_id} has overlapping tasks")
                break
    
    return violations


# =========================================================================
# Workforce Rostering - Operators
# =========================================================================

def workforce_solution_initializer(problem_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate random workforce schedule"""
    workers = problem_data.get('workers', [])
    days = problem_data.get('days', ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
    shifts = problem_data.get('shifts', ['morning', 'afternoon', 'night'])
    
    if not workers:
        return {'assignments': []}
    
    assignments = []
    
    # Randomly assign workers to shifts (respecting max shifts per worker)
    max_shifts_per_worker = problem_data.get('max_shifts_per_worker', 5)
    
    for worker in workers:
        num_shifts = random.randint(2, max_shifts_per_worker)
        worker_assignments = random.sample(
            [(day, shift) for day in days for shift in shifts],
            min(num_shifts, len(days) * len(shifts))
        )
        
        for day, shift in worker_assignments:
            assignments.append({
                'worker_id': worker['id'],
                'day': day,
                'shift': shift
            })
    
    return {'assignments': assignments}


def workforce_constraint_checker(solution: Dict[str, Any], problem_data: Dict[str, Any]) -> List[str]:
    """Check workforce constraints"""
    violations = []
    assignments = solution.get('assignments', [])
    workers = problem_data.get('workers', [])
    shift_requirements = problem_data.get('shift_requirements', {})
    max_shifts_per_worker = problem_data.get('max_shifts_per_worker', 5)
    
    # Check max shifts per worker
    worker_shift_count = {}
    for assignment in assignments:
        worker_id = assignment['worker_id']
        worker_shift_count[worker_id] = worker_shift_count.get(worker_id, 0) + 1
    
    for worker_id, count in worker_shift_count.items():
        if count > max_shifts_per_worker:
            violations.append(f"Worker {worker_id} exceeds max shifts: {count} > {max_shifts_per_worker}")
    
    # Check minimum shift coverage
    shift_coverage = {}
    for assignment in assignments:
        shift_key = f"{assignment['day']}_{assignment['shift']}"
        shift_coverage[shift_key] = shift_coverage.get(shift_key, 0) + 1
    
    for shift_key, required in shift_requirements.items():
        actual = shift_coverage.get(shift_key, 0)
        if actual < required:
            violations.append(f"Shift {shift_key} understaffed: {actual} < {required}")
    
    return violations


# =========================================================================
# Maintenance Scheduling - Operators
# =========================================================================

def maintenance_solution_initializer(problem_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate random maintenance schedule"""
    machines = problem_data.get('machines', [])
    technicians = problem_data.get('technicians', [])
    max_days = problem_data.get('max_days', 30)
    
    if not machines or not technicians:
        return {'schedule': []}
    
    schedule = []
    
    for machine in machines:
        # Randomly assign technician and schedule day
        technician = random.choice(technicians)
        start_day = random.randint(0, max_days - machine.get('maintenance_duration', 1))
        duration = machine.get('maintenance_duration', 1)
        
        schedule.append({
            'machine_id': machine['id'],
            'technician_id': technician['id'],
            'start_day': start_day,
            'duration': duration
        })
    
    return {'schedule': schedule}


def maintenance_constraint_checker(solution: Dict[str, Any], problem_data: Dict[str, Any]) -> List[str]:
    """Check maintenance constraints"""
    violations = []
    schedule = solution.get('schedule', [])
    machines = problem_data.get('machines', [])
    technicians = problem_data.get('technicians', [])
    max_days = problem_data.get('max_days', 30)
    
    # All machines must be maintained
    maintained_machines = {task['machine_id'] for task in schedule}
    all_machine_ids = {m['id'] for m in machines}
    
    if maintained_machines != all_machine_ids:
        violations.append(f"Not all machines maintained: {len(maintained_machines)}/{len(all_machine_ids)}")
    
    # Technician availability (no overlapping tasks)
    technician_tasks = {}
    for task in schedule:
        tech_id = task['technician_id']
        if tech_id not in technician_tasks:
            technician_tasks[tech_id] = []
        technician_tasks[tech_id].append(task)
    
    for tech_id, tasks in technician_tasks.items():
        tasks.sort(key=lambda x: x['start_day'])
        for i in range(len(tasks) - 1):
            task1_end = tasks[i]['start_day'] + tasks[i]['duration']
            task2_start = tasks[i+1]['start_day']
            if task1_end > task2_start:
                violations.append(f"Technician {tech_id} has overlapping tasks")
                break
    
    # Maintenance window (all tasks within max_days)
    for task in schedule:
        if task['start_day'] + task['duration'] > max_days:
            violations.append(f"Maintenance for machine {task['machine_id']} exceeds time window")
    
    return violations


# =========================================================================
# Promotion Scheduling - Operators
# =========================================================================

def promotion_solution_initializer(problem_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate random promotion schedule"""
    products = problem_data.get('products', [])
    weeks = problem_data.get('weeks', 12)
    budget = problem_data.get('budget', 50000)
    
    if not products:
        return {'promotions': [], 'total_budget_used': 0}
    
    promotions = []
    total_budget = 0
    
    # Select random subset of products for promotion
    num_promotions = random.randint(len(products) // 2, len(products))
    selected_products = random.sample(products, num_promotions)
    
    for product in selected_products:
        week = random.randint(1, weeks)
        discount = random.uniform(0.10, 0.30)
        promo_cost = product.get('base_revenue', 1000) * discount * 0.5
        expected_revenue = product.get('base_revenue', 1000) * (1 + discount * 2)
        
        if total_budget + promo_cost <= budget:
            promotions.append({
                'product_id': product['id'],
                'week': week,
                'discount': discount,
                'cost': promo_cost,
                'expected_revenue': expected_revenue
            })
            total_budget += promo_cost
    
    return {'promotions': promotions, 'total_budget_used': total_budget}


def promotion_constraint_checker(solution: Dict[str, Any], problem_data: Dict[str, Any]) -> List[str]:
    """Check promotion constraints"""
    violations = []
    promotions = solution.get('promotions', [])
    budget = problem_data.get('budget', 50000)
    total_budget_used = solution.get('total_budget_used', 0)
    blackout_weeks = problem_data.get('blackout_weeks', [])
    
    # Budget constraint
    if total_budget_used > budget:
        violations.append(f"Budget exceeded: ${total_budget_used} > ${budget}")
    
    # Blackout weeks
    for promo in promotions:
        if promo['week'] in blackout_weeks:
            violations.append(f"Promotion in blackout week {promo['week']}")
    
    # No duplicate promotions for same product in same week
    promo_keys = [(p['product_id'], p['week']) for p in promotions]
    if len(promo_keys) != len(set(promo_keys)):
        violations.append("Duplicate promotions for same product in same week")
    
    return violations


# =========================================================================
# Portfolio Rebalancing - Operators
# =========================================================================

def portfolio_solution_initializer(problem_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate random portfolio allocation"""
    assets = problem_data.get('assets', [])
    
    if not assets:
        return {'allocations': [], 'expected_return': 0, 'volatility': 0, 'sharpe_ratio': 0, 'transaction_costs': 0}
    
    # Random weights that sum to 1.0
    weights = [random.random() for _ in assets]
    total = sum(weights)
    weights = [w / total for w in weights]
    
    allocations = []
    expected_return = 0
    volatility = 0
    transaction_costs = 0
    
    for i, asset in enumerate(assets):
        weight = weights[i]
        trades_required = abs(weight - asset.get('current_weight', 0)) * 1000000  # Assume $1M portfolio
        
        allocations.append({
            'asset_id': asset['id'],
            'weight': weight,
            'trades_required': trades_required
        })
        
        expected_return += weight * asset.get('expected_return', 0.05)
        volatility += (weight ** 2) * (asset.get('volatility', 0.10) ** 2)
        transaction_costs += trades_required * asset.get('transaction_cost_rate', 0.001)
    
    volatility = volatility ** 0.5
    risk_free_rate = problem_data.get('risk_free_rate', 0.02)
    sharpe_ratio = (expected_return - risk_free_rate) / volatility if volatility > 0 else 0
    
    return {
        'allocations': allocations,
        'expected_return': expected_return,
        'volatility': volatility,
        'sharpe_ratio': sharpe_ratio,
        'transaction_costs': transaction_costs
    }


def portfolio_constraint_checker(solution: Dict[str, Any], problem_data: Dict[str, Any]) -> List[str]:
    """Check portfolio constraints"""
    violations = []
    allocations = solution.get('allocations', [])
    
    # Weights must sum to 1.0 (fully invested)
    total_weight = sum(a['weight'] for a in allocations)
    if abs(total_weight - 1.0) > 0.01:
        violations.append(f"Weights don't sum to 1.0: {total_weight:.4f}")
    
    # No negative weights (no short selling unless allowed)
    for alloc in allocations:
        if alloc['weight'] < 0:
            violations.append(f"Negative weight for asset {alloc['asset_id']}")
    
    # Position size limits
    max_position_size = problem_data.get('max_position_size', 0.25)
    for alloc in allocations:
        if alloc['weight'] > max_position_size:
            violations.append(f"Asset {alloc['asset_id']} exceeds max position size: {alloc['weight']:.2%}")
    
    return violations


# =========================================================================
# Trading Schedule Optimization - Operators
# =========================================================================

def trading_solution_initializer(problem_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate random trading execution schedule"""
    target_quantity = problem_data.get('target_quantity', 50000)
    time_window = problem_data.get('time_window', 120)  # minutes
    num_orders = random.randint(10, 20)
    
    # Split quantity across child orders
    child_orders = []
    remaining_qty = target_quantity
    
    for i in range(num_orders):
        if i == num_orders - 1:
            size = remaining_qty
        else:
            size = random.randint(int(remaining_qty * 0.05), int(remaining_qty * 0.15))
        
        time = random.randint(0, time_window)
        expected_price = 100 + random.gauss(0, 0.5)  # Assume base price ~$100
        
        child_orders.append({
            'time': time,
            'size': size,
            'expected_price': expected_price
        })
        
        remaining_qty -= size
        if remaining_qty <= 0:
            break
    
    # Calculate metrics
    total_slippage = sum(abs(o['expected_price'] - 100) * o['size'] for o in child_orders) / 100
    vwap_deviation = random.uniform(-0.02, 0.02)
    market_impact = len(child_orders) * 0.01
    
    return {
        'child_orders': child_orders,
        'total_slippage': total_slippage,
        'vwap_deviation': vwap_deviation,
        'market_impact': market_impact
    }


def trading_constraint_checker(solution: Dict[str, Any], problem_data: Dict[str, Any]) -> List[str]:
    """Check trading constraints"""
    violations = []
    child_orders = solution.get('child_orders', [])
    target_quantity = problem_data.get('target_quantity', 50000)
    time_window = problem_data.get('time_window', 120)
    
    # Must execute target quantity
    total_executed = sum(o['size'] for o in child_orders)
    if abs(total_executed - target_quantity) > target_quantity * 0.01:
        violations.append(f"Quantity mismatch: {total_executed} != {target_quantity}")
    
    # All orders within time window
    for order in child_orders:
        if order['time'] < 0 or order['time'] > time_window:
            violations.append(f"Order at time {order['time']} outside window [0, {time_window}]")
    
    return violations


# =========================================================================
# Operator Registry
# =========================================================================

SOLUTION_INITIALIZERS = {
    'vrp': vrp_solution_initializer,
    'job_shop': job_shop_solution_initializer,
    'workforce': workforce_solution_initializer,
    'maintenance': maintenance_solution_initializer,
    'promotion': promotion_solution_initializer,
    'portfolio': portfolio_solution_initializer,
    'trading': trading_solution_initializer
}

CONSTRAINT_CHECKERS = {
    'vrp': vrp_constraint_checker,
    'job_shop': job_shop_constraint_checker,
    'workforce': workforce_constraint_checker,
    'maintenance': maintenance_constraint_checker,
    'promotion': promotion_constraint_checker,
    'portfolio': portfolio_constraint_checker,
    'trading': trading_constraint_checker
}


def get_solution_initializer(domain_id: str):
    """Get solution initializer for a domain"""
    initializer = SOLUTION_INITIALIZERS.get(domain_id)
    if not initializer:
        raise ValueError(f"No solution initializer found for domain: {domain_id}")
    return initializer


def get_constraint_checker(domain_id: str):
    """Get constraint checker for a domain"""
    checker = CONSTRAINT_CHECKERS.get(domain_id)
    if not checker:
        raise ValueError(f"No constraint checker found for domain: {domain_id}")
    return checker

