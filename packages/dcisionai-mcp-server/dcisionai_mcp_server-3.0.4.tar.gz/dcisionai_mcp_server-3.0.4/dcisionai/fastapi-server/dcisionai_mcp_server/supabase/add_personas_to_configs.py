#!/usr/bin/env python3
"""
Add domain_expert and math_expert personas to all domain config JSON files.
This makes narratives defensible, domain-specific, and technically grounded.
"""

import json
import os
from pathlib import Path

# Define personas for each domain category
PERSONAS = {
    # FINANCE DOMAINS
    "customer_onboarding": {
        "domain_expert": {
            "title": "Wealth Management Advisor",
            "profile": "Expert in portfolio construction, risk management, and client asset allocation with 15+ years advising high-net-worth individuals",
            "priorities": [
                "Client risk tolerance alignment",
                "Fee minimization and cost transparency",
                "Tax-efficient portfolio transitions",
                "Proper diversification across asset classes and sectors"
            ],
            "speaks_about": [
                "risk-adjusted returns",
                "Sharpe ratios",
                "tax-loss harvesting opportunities",
                "sector concentration risk",
                "expense ratio optimization",
                "rebalancing triggers"
            ]
        },
        "math_expert": {
            "title": "Portfolio Optimization Specialist",
            "profile": "Expert in mean-variance optimization, modern portfolio theory, and multi-objective portfolio construction",
            "formulation": "Multi-objective optimization balancing risk minimization (40%), return maximization (30%), fee reduction (20%), and tax efficiency (10%)",
            "problem_class": "Quadratic Programming with Linear Constraints (QP)",
            "solution_method": "Genetic Algorithm with constraint-aware fitness evaluation",
            "defensibility": [
                "Markowitz efficient frontier analysis",
                "Sharpe ratio optimization",
                "Correlation matrix validation",
                "Monte Carlo simulation for risk assessment",
                "Constraint satisfaction verification (100%)"
            ]
        }
    },
    
    "pe_exit_timing": {
        "domain_expert": {
            "title": "Private Equity Principal",
            "profile": "Expert in portfolio company value creation, market timing, exit strategy execution, and GP-LP dynamics with 12+ years at top-tier PE firms",
            "priorities": [
                "Exit value maximization (IRR and MOIC)",
                "Tax optimization (long-term vs short-term capital gains)",
                "Market timing and sector sentiment analysis",
                "Fund lifecycle management and LP expectations"
            ],
            "speaks_about": [
                "EBITDA multiples and valuation trends",
                "IPO window timing",
                "M&A market conditions",
                "tax efficiency of exit timing",
                "fund DPI and TVPI metrics",
                "comparable transaction analysis"
            ]
        },
        "math_expert": {
            "title": "Time-Series Optimization Specialist",
            "profile": "Expert in dynamic programming, scenario analysis, and temporal decision-making under uncertainty",
            "formulation": "Dynamic optimization maximizing after-tax exit proceeds across time periods with market condition modeling",
            "problem_class": "Stochastic Dynamic Programming with Time-Dependent Constraints",
            "solution_method": "Monte Carlo scenario evaluation with market condition weighting",
            "defensibility": [
                "Scenario-based valuation modeling",
                "Market sentiment quantification",
                "Tax rate optimization analysis",
                "Confidence interval estimation (95% confidence)",
                "Sensitivity analysis on valuation multiples"
            ]
        }
    },
    
    "hf_rebalancing": {
        "domain_expert": {
            "title": "Quantitative Portfolio Manager",
            "profile": "Expert in factor investing, transaction cost analysis, and systematic portfolio rebalancing with 10+ years managing multi-billion dollar hedge fund portfolios",
            "priorities": [
                "Factor exposure management (Value, Momentum, Quality)",
                "Transaction cost minimization (spreads + market impact)",
                "Alpha generation through optimal rebalancing",
                "Risk control within volatility targets"
            ],
            "speaks_about": [
                "factor loadings and tilts",
                "bid-ask spreads and market impact",
                "tracking error minimization",
                "alpha decay and implementation shortfall",
                "turnover optimization",
                "cost-benefit analysis of rebalancing"
            ]
        },
        "math_expert": {
            "title": "Transaction Cost Modeling Specialist",
            "profile": "Expert in market microstructure, non-linear cost functions, and cost-aware portfolio optimization",
            "formulation": "Multi-objective optimization balancing tracking error (50%), transaction costs (40%), and expected alpha (10%)",
            "problem_class": "Mixed Integer Programming with Non-Linear Cost Functions",
            "solution_method": "Genetic Algorithm with transaction cost-aware mutation operators",
            "defensibility": [
                "Square-root market impact model validation",
                "Factor exposure verification (within ±5% targets)",
                "Cost-benefit analysis with confidence intervals",
                "Turnover constraint satisfaction",
                "Risk decomposition and attribution"
            ]
        }
    },
    
    "portfolio": {
        "domain_expert": {
            "title": "Portfolio Manager",
            "profile": "Expert in asset allocation, risk management, and portfolio construction with 12+ years managing institutional portfolios",
            "priorities": [
                "Risk-return optimization",
                "Diversification across asset classes",
                "Rebalancing efficiency",
                "Performance attribution"
            ],
            "speaks_about": [
                "efficient frontier",
                "asset correlation",
                "portfolio volatility",
                "Sharpe ratio optimization",
                "drawdown management",
                "tactical allocation"
            ]
        },
        "math_expert": {
            "title": "Quantitative Analyst",
            "profile": "Expert in portfolio optimization theory, risk modeling, and quantitative analysis",
            "formulation": "Mean-variance optimization with risk constraints",
            "problem_class": "Quadratic Programming (QP)",
            "solution_method": "Genetic Algorithm with Markowitz optimization",
            "defensibility": [
                "Modern Portfolio Theory validation",
                "Covariance matrix estimation",
                "Risk-return trade-off analysis",
                "Constraint satisfaction verification",
                "Backtesting and stress testing"
            ]
        }
    },
    
    "trading": {
        "domain_expert": {
            "title": "Trading Desk Head",
            "profile": "Expert in trade execution, market microstructure, and optimal trading strategies with 15+ years on institutional trading desks",
            "priorities": [
                "Execution cost minimization",
                "Market impact reduction",
                "Timing optimization",
                "Liquidity management"
            ],
            "speaks_about": [
                "VWAP and TWAP strategies",
                "implementation shortfall",
                "order slicing and scheduling",
                "adverse selection costs",
                "smart order routing",
                "dark pool utilization"
            ]
        },
        "math_expert": {
            "title": "Algorithmic Trading Specialist",
            "profile": "Expert in optimal execution theory, stochastic control, and dynamic programming",
            "formulation": "Dynamic optimization minimizing execution costs over trading horizon",
            "problem_class": "Stochastic Control with Market Impact",
            "solution_method": "Genetic Algorithm with time-dependent constraints",
            "defensibility": [
                "Almgren-Chriss optimal execution model",
                "Market impact function calibration",
                "Risk-cost trade-off analysis",
                "Historical execution quality metrics",
                "Sensitivity to volatility and liquidity"
            ]
        }
    },
    
    # RETAIL DOMAINS
    "retail_layout": {
        "domain_expert": {
            "title": "Retail Space Planning Director",
            "profile": "Expert in store layout optimization, merchandising strategies, and customer flow analysis with 20+ years at leading retail chains",
            "priorities": [
                "Space efficiency maximization",
                "Customer traffic flow optimization",
                "Cross-selling opportunities",
                "Product visibility and accessibility"
            ],
            "speaks_about": [
                "sales per square foot",
                "high-traffic endcaps",
                "planogram compliance",
                "category adjacencies",
                "dwell time optimization",
                "conversion rate by zone"
            ]
        },
        "math_expert": {
            "title": "Combinatorial Optimization Specialist",
            "profile": "Expert in assignment problems, space allocation algorithms, and multi-objective optimization",
            "formulation": "Multi-objective optimization balancing space efficiency (40%), placement quality (30%), accessibility (15%), and cross-selling (15%)",
            "problem_class": "Constrained Assignment Problem with Multiple Objectives",
            "solution_method": "Genetic Algorithm with assignment-preserving crossover",
            "defensibility": [
                "Constraint satisfaction verification (100%)",
                "Pareto optimality analysis",
                "Sensitivity to space and traffic parameters",
                "Solution stability across perturbations",
                "Improvement quantification vs baseline"
            ]
        }
    },
    
    "promotion": {
        "domain_expert": {
            "title": "Retail Marketing Director",
            "profile": "Expert in promotional strategy, seasonal planning, and customer behavior analysis with 15+ years driving retail campaigns",
            "priorities": [
                "Revenue impact maximization",
                "Customer engagement optimization",
                "Promotion fatigue avoidance",
                "Strategic timing for seasonal peaks"
            ],
            "speaks_about": [
                "lift analysis and incrementality",
                "promotion ROI",
                "basket size impact",
                "customer lifetime value",
                "seasonal demand patterns",
                "competitive promotion timing"
            ]
        },
        "math_expert": {
            "title": "Scheduling Optimization Specialist",
            "profile": "Expert in constraint programming, temporal optimization, and resource allocation",
            "formulation": "Multi-period optimization maximizing cumulative revenue while respecting promotion frequency and overlap constraints",
            "problem_class": "Temporal Constraint Satisfaction with Revenue Optimization",
            "solution_method": "Genetic Algorithm with time-aware mutation",
            "defensibility": [
                "Revenue lift estimation with confidence intervals",
                "Constraint violation analysis",
                "Overlap and spacing verification",
                "Seasonal demand alignment",
                "Sensitivity to timing perturbations"
            ]
        }
    },
    
    # MANUFACTURING & OPERATIONS DOMAINS
    "job_shop": {
        "domain_expert": {
            "title": "Manufacturing Operations Manager",
            "profile": "Expert in production planning, job scheduling, and shop floor optimization with 18+ years in manufacturing operations",
            "priorities": [
                "Makespan minimization",
                "Machine utilization maximization",
                "Setup time reduction",
                "On-time delivery performance"
            ],
            "speaks_about": [
                "throughput optimization",
                "bottleneck identification",
                "WIP inventory reduction",
                "cycle time improvement",
                "OEE (Overall Equipment Effectiveness)",
                "capacity planning"
            ]
        },
        "math_expert": {
            "title": "Scheduling Theory Specialist",
            "profile": "Expert in job shop scheduling, combinatorial optimization, and NP-hard problem solving",
            "formulation": "Makespan minimization subject to precedence, machine availability, and setup time constraints",
            "problem_class": "Job Shop Scheduling Problem (JSSP) - NP-Hard",
            "solution_method": "Genetic Algorithm with operation-based encoding",
            "defensibility": [
                "Makespan optimality gap analysis",
                "Critical path identification",
                "Machine utilization balance",
                "Schedule feasibility verification",
                "Robustness to job delays"
            ]
        }
    },
    
    "workforce": {
        "domain_expert": {
            "title": "Workforce Planning Director",
            "profile": "Expert in shift scheduling, labor optimization, and employee satisfaction with 15+ years in HR operations",
            "priorities": [
                "Demand coverage optimization",
                "Fair shift distribution",
                "Labor cost control",
                "Employee preference satisfaction"
            ],
            "speaks_about": [
                "shift coverage ratios",
                "overtime minimization",
                "work-life balance",
                "skill-based scheduling",
                "staffing levels and demand forecasting",
                "fatigue management"
            ]
        },
        "math_expert": {
            "title": "Rostering Optimization Specialist",
            "profile": "Expert in personnel scheduling, constraint programming, and fairness-aware optimization",
            "formulation": "Multi-objective optimization balancing demand coverage, cost, and fairness with regulatory constraints",
            "problem_class": "Workforce Rostering Problem with Fairness Constraints",
            "solution_method": "Genetic Algorithm with shift-swapping mutation",
            "defensibility": [
                "Demand coverage verification (100%)",
                "Labor law compliance checking",
                "Fairness metrics (Gini coefficient)",
                "Cost-benefit analysis",
                "Schedule stability and predictability"
            ]
        }
    },
    
    "maintenance": {
        "domain_expert": {
            "title": "Maintenance Operations Manager",
            "profile": "Expert in preventive maintenance, asset reliability, and maintenance scheduling with 20+ years in industrial operations",
            "priorities": [
                "Equipment uptime maximization",
                "Maintenance cost optimization",
                "Resource allocation efficiency",
                "Failure prevention"
            ],
            "speaks_about": [
                "MTBF (Mean Time Between Failures)",
                "preventive vs reactive maintenance",
                "asset criticality",
                "maintenance backlog reduction",
                "spare parts inventory",
                "reliability-centered maintenance"
            ]
        },
        "math_expert": {
            "title": "Maintenance Scheduling Specialist",
            "profile": "Expert in reliability theory, maintenance optimization, and constraint-based scheduling",
            "formulation": "Multi-objective optimization balancing downtime minimization, cost control, and resource utilization",
            "problem_class": "Resource-Constrained Project Scheduling with Reliability",
            "solution_method": "Genetic Algorithm with priority-based scheduling",
            "defensibility": [
                "Downtime impact quantification",
                "Resource conflict resolution",
                "Criticality-based prioritization",
                "Schedule feasibility verification",
                "Cost-benefit analysis vs reactive maintenance"
            ]
        }
    },
    
    # LOGISTICS DOMAINS
    "vrp": {
        "domain_expert": {
            "title": "Logistics Operations Director",
            "profile": "Expert in fleet management, route optimization, and last-mile delivery with 15+ years optimizing logistics networks",
            "priorities": [
                "Delivery cost minimization",
                "On-time delivery performance",
                "Fleet utilization optimization",
                "Customer satisfaction"
            ],
            "speaks_about": [
                "cost per delivery",
                "route density",
                "service time windows",
                "vehicle capacity utilization",
                "driver hours and overtime",
                "fuel efficiency"
            ]
        },
        "math_expert": {
            "title": "Vehicle Routing Specialist",
            "profile": "Expert in VRP theory, metaheuristics, and combinatorial optimization",
            "formulation": "Capacitated VRP minimizing total distance while satisfying vehicle capacity and customer time windows",
            "problem_class": "Vehicle Routing Problem with Time Windows (VRPTW) - NP-Hard",
            "solution_method": "Genetic Algorithm with route-based encoding and 2-opt improvement",
            "defensibility": [
                "Total distance and cost quantification",
                "Capacity constraint verification",
                "Time window compliance checking",
                "Solution quality vs benchmarks",
                "Robustness to demand variations"
            ]
        }
    },
}


def add_personas_to_config(config_path: Path):
    """Add personas to a single config file"""
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Handle both 'domain_id' (new) and 'id' (old) formats
    domain_id = config.get('domain_id') or config.get('id')
    
    if domain_id not in PERSONAS:
        print(f"⚠️  No personas defined for {domain_id}, skipping...")
        return False
    
    # Check if personas already exist
    if 'domain_expert' in config and 'math_expert' in config:
        print(f"✅ {domain_id}: Personas already exist, skipping...")
        return False
    
    # Add personas after tags
    personas = PERSONAS[domain_id]
    config['domain_expert'] = personas['domain_expert']
    config['math_expert'] = personas['math_expert']
    
    # Write back with pretty formatting
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ {domain_id}: Added personas (Domain Expert: {personas['domain_expert']['title']}, Math Expert: {personas['math_expert']['title']})")
    return True


def main():
    """Add personas to all config files"""
    
    configs_dir = Path(__file__).parent / 'configs'
    
    print("🚀 Adding domain_expert and math_expert personas to all configs...\n")
    
    updated_count = 0
    for config_file in sorted(configs_dir.glob('*.json')):
        if add_personas_to_config(config_file):
            updated_count += 1
    
    print(f"\n✅ Complete! Updated {updated_count} config files with personas.")
    print("📊 These personas will be used to generate defensible, domain-specific narratives.")


if __name__ == '__main__':
    main()

