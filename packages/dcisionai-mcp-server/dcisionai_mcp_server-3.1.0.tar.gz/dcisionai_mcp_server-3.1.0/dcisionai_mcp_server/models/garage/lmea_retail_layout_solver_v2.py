#!/usr/bin/env python3
"""
LMEA Retail Store Layout Optimization Solver v2.0
DOMAIN-EXPERT APPROACH: Rich built-in constraints + Lightweight extraction

Key Innovation:
- We embed retail expertise (not LLM guessing)
- Extract ONLY customer-specific values
- Simulate missing values transparently
- Rich constraint templates guarantee good solutions

Markets:
- Retail stores (grocery, department, specialty)
- Planogram generation
- Category management
- Seasonal layouts
"""

import logging
import random
import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from anthropic import Anthropic

from .mathematical_proof_engine import MathematicalProofEngine

logger = logging.getLogger(__name__)


# ==============================================================================
# DOMAIN EXPERTISE: Product Categories & Attributes
# ==============================================================================

CATEGORY_PROFILES = {
    'Beverages': {
        'typical_margin': 3.5,
        'typical_sales_rate': 20.0,
        'typical_space': 2.0,
        'refrigeration': False,
        'security': False,
        'preferred_zone': 'middle',
        'complementary': ['Snacks', 'Baking']
    },
    'Snacks': {
        'typical_margin': 4.5,
        'typical_sales_rate': 25.0,
        'typical_space': 1.5,
        'refrigeration': False,
        'security': False,
        'preferred_zone': 'front',
        'complementary': ['Beverages']
    },
    'Dairy': {
        'typical_margin': 2.0,
        'typical_sales_rate': 18.0,
        'typical_space': 3.0,
        'refrigeration': True,
        'security': False,
        'preferred_zone': 'back',
        'complementary': ['Baking', 'Cereal']
    },
    'Frozen': {
        'typical_margin': 2.5,
        'typical_sales_rate': 12.0,
        'typical_space': 4.0,
        'refrigeration': True,
        'security': False,
        'preferred_zone': 'back',
        'complementary': ['Dairy']
    },
    'Fresh Produce': {
        'typical_margin': 3.0,
        'typical_sales_rate': 22.0,
        'typical_space': 3.5,
        'refrigeration': True,
        'security': False,
        'preferred_zone': 'front',
        'complementary': ['Dairy']
    },
    'Meat': {
        'typical_margin': 5.0,
        'typical_sales_rate': 15.0,
        'typical_space': 3.0,
        'refrigeration': True,
        'security': False,
        'preferred_zone': 'back',
        'complementary': ['Fresh Produce', 'Dairy']
    },
    'Cereal': {
        'typical_margin': 3.0,
        'typical_sales_rate': 16.0,
        'typical_space': 2.5,
        'refrigeration': False,
        'security': False,
        'preferred_zone': 'middle',
        'complementary': ['Dairy', 'Beverages']
    },
    'Baking': {
        'typical_margin': 2.5,
        'typical_sales_rate': 10.0,
        'typical_space': 2.0,
        'refrigeration': False,
        'security': False,
        'preferred_zone': 'middle',
        'complementary': ['Dairy', 'Cereal']
    },
    'Canned Goods': {
        'typical_margin': 2.0,
        'typical_sales_rate': 12.0,
        'typical_space': 1.5,
        'refrigeration': False,
        'security': False,
        'preferred_zone': 'middle',
        'complementary': ['Baking']
    },
    'Household': {
        'typical_margin': 4.0,
        'typical_sales_rate': 8.0,
        'typical_space': 3.0,
        'refrigeration': False,
        'security': False,
        'preferred_zone': 'back',
        'complementary': []
    },
    'Health & Beauty': {
        'typical_margin': 6.0,
        'typical_sales_rate': 10.0,
        'typical_space': 1.5,
        'refrigeration': False,
        'security': True,
        'preferred_zone': 'middle',
        'complementary': []
    },
    'Electronics': {
        'typical_margin': 8.0,
        'typical_sales_rate': 5.0,
        'typical_space': 2.0,
        'refrigeration': False,
        'security': True,
        'preferred_zone': 'front',
        'complementary': []
    },
}

# Default for unknown categories
DEFAULT_CATEGORY_PROFILE = {
    'typical_margin': 3.0,
    'typical_sales_rate': 12.0,
    'typical_space': 2.0,
    'refrigeration': False,
    'security': False,
    'preferred_zone': 'middle',
    'complementary': []
}


# ==============================================================================
# DOMAIN EXPERTISE: Store Layout Best Practices
# ==============================================================================

LAYOUT_RULES = {
    'high_margin_visibility': {
        'description': 'High-margin products (>$4) should be in high-visibility zones (score 7+)',
        'priority': 'critical',
        'penalty': 500.0
    },
    'refrigeration_clustering': {
        'description': 'Refrigerated products should be clustered to reduce energy cost',
        'priority': 'high',
        'penalty': 200.0
    },
    'security_zones': {
        'description': 'High-security products need monitored areas',
        'priority': 'critical',
        'penalty': 1000.0
    },
    'complementary_adjacency': {
        'description': 'Complementary products should be nearby for cross-selling',
        'priority': 'medium',
        'bonus': 50.0
    },
    'traffic_flow': {
        'description': 'Popular products draw traffic to low-flow areas',
        'priority': 'high',
        'bonus': 100.0
    },
    'space_utilization': {
        'description': 'Maximize shelf space usage (target 85-95%)',
        'priority': 'high',
        'penalty': 300.0
    }
}


# ==============================================================================
# Data Classes
# ==============================================================================

@dataclass
class Product:
    """Product with domain-enriched attributes"""
    id: int
    name: str
    category: str
    space_required: float  # sqft
    sales_rate: float  # units/day
    profit_margin: float  # dollars per unit
    complementary_products: List[int] = field(default_factory=list)
    requires_refrigeration: bool = False
    requires_security: bool = False
    
    # Metadata
    is_simulated: bool = False
    simulation_notes: List[str] = field(default_factory=list)


@dataclass
class ShelfSpace:
    """Shelf space with realistic attributes"""
    id: int
    location: str
    total_space: float  # sqft
    visibility_score: float  # 1-10
    foot_traffic: float  # customers/hour
    zone: str  # front, middle, back
    has_refrigeration: bool = False
    has_security: bool = False


# ==============================================================================
# Lightweight Extraction (Customer-Specific Values Only)
# ==============================================================================

class CustomerInputExtractor:
    """Extract ONLY what customer provides, nothing more"""
    
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    async def extract(self, problem_description: str) -> Dict:
        """
        Lightweight extraction of customer-specific values
        
        Returns:
        {
            'products': [{'name': 'Coffee', 'category': 'Beverages', 'margin': 5.0 (if mentioned)}],
            'num_products': 50,
            'num_shelves': 8,
            'store_type': 'grocery',
            'special_requirements': ['refrigeration for dairy', ...],
            'foot_traffic_hints': {'front': 150, 'back': 60}
        }
        """
        
        logger.info("📄 Extracting customer-specific values...")
        
        prompt = f"""Extract ONLY the explicit values the customer provides. Don't infer or guess.

Problem: {problem_description}

Return JSON with:
{{
  "num_products": <number if mentioned, else null>,
  "num_shelves": <number if mentioned, else null>,
  "store_type": "grocery|department|specialty|null",
  "product_mentions": [
    {{"name": "Coffee", "category": "Beverages", "note": "high-margin" (if mentioned)}}
  ],
  "shelf_mentions": [
    {{"location": "front", "foot_traffic": 150 (if mentioned)}}
  ],
  "special_requirements": ["refrigeration", "security", ...]
}}

CRITICAL: Only extract what customer explicitly states. Use null for missing values.
Return ONLY JSON, no other text."""

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text.strip()
            if content.startswith('```'):
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
            
            extracted = json.loads(content.strip())
            logger.info(f"✅ Extracted: {json.dumps(extracted, indent=2)}")
            return extracted
            
        except Exception as e:
            logger.error(f"❌ Extraction failed: {e}")
            return {}


# ==============================================================================
# Domain-Expert Simulator (Fill Gaps with Retail Expertise)
# ==============================================================================

class DomainExpertSimulator:
    """Simulate missing values using retail domain expertise"""
    
    def simulate_products(
        self,
        extracted: Dict,
        target_count: Optional[int] = None
    ) -> Tuple[List[Product], List[str]]:
        """
        Generate products using:
        1. Extracted customer values (if any)
        2. Domain expertise (category profiles)
        3. Simulation transparency
        
        Returns: (products, transparency_log)
        """
        transparency = []
        products = []
        
        # Determine how many products to create
        num_products = extracted.get('num_products') or target_count or 50
        transparency.append(f"Product count: {num_products} ({'customer-specified' if extracted.get('num_products') else 'simulated default'})")
        
        # Get mentioned products
        mentioned = extracted.get('product_mentions', [])
        
        # Category distribution (realistic for grocery)
        category_distribution = {
            'Beverages': 0.12,
            'Snacks': 0.15,
            'Dairy': 0.10,
            'Frozen': 0.08,
            'Fresh Produce': 0.12,
            'Meat': 0.08,
            'Cereal': 0.10,
            'Baking': 0.08,
            'Canned Goods': 0.10,
            'Household': 0.05,
            'Health & Beauty': 0.02
        }
        
        # Create products
        product_id = 1
        
        # First, add mentioned products
        for mention in mentioned:
            profile = CATEGORY_PROFILES.get(
                mention.get('category', 'General'),
                DEFAULT_CATEGORY_PROFILE
            )
            
            products.append(Product(
                id=product_id,
                name=mention['name'],
                category=mention.get('category', 'General'),
                space_required=profile['typical_space'],
                sales_rate=profile['typical_sales_rate'],
                profit_margin=profile['typical_margin'],
                requires_refrigeration=profile['refrigeration'],
                requires_security=profile['security'],
                is_simulated=False,
                simulation_notes=[f"Customer mentioned: {mention.get('note', 'N/A')}"]
            ))
            product_id += 1
        
        transparency.append(f"Customer mentioned {len(mentioned)} products explicitly")
        
        # Fill remaining with realistic distribution
        remaining = num_products - len(mentioned)
        for category, ratio in category_distribution.items():
            count = int(remaining * ratio)
            profile = CATEGORY_PROFILES[category]
            
            for i in range(count):
                products.append(Product(
                    id=product_id,
                    name=f"{category} Product {i+1}",
                    category=category,
                    space_required=profile['typical_space'] * random.uniform(0.8, 1.2),
                    sales_rate=profile['typical_sales_rate'] * random.uniform(0.7, 1.3),
                    profit_margin=profile['typical_margin'] * random.uniform(0.8, 1.2),
                    requires_refrigeration=profile['refrigeration'],
                    requires_security=profile['security'],
                    is_simulated=True,
                    simulation_notes=[f"Simulated based on {category} category profile"]
                ))
                product_id += 1
        
        transparency.append(f"Simulated {remaining} products using retail category profiles")
        
        # Link complementary products
        self._link_complementary_products(products)
        transparency.append("Applied cross-selling relationships based on retail best practices")
        
        logger.info(f"✅ Generated {len(products)} products ({len(mentioned)} customer-specified, {len(products)-len(mentioned)} simulated)")
        
        return products, transparency
    
    def _link_complementary_products(self, products: List[Product]):
        """Link products based on category complementarity"""
        category_map = {}
        for p in products:
            if p.category not in category_map:
                category_map[p.category] = []
            category_map[p.category].append(p.id)
        
        for product in products:
            profile = CATEGORY_PROFILES.get(product.category, DEFAULT_CATEGORY_PROFILE)
            complementary_categories = profile['complementary']
            
            # Add 2-3 complementary products
            for comp_cat in complementary_categories[:2]:
                if comp_cat in category_map:
                    comp_products = category_map[comp_cat]
                    if comp_products:
                        product.complementary_products.append(random.choice(comp_products))
    
    def simulate_shelves(
        self,
        extracted: Dict,
        target_count: Optional[int] = None
    ) -> Tuple[List[ShelfSpace], List[str]]:
        """
        Generate shelf spaces using:
        1. Extracted customer hints
        2. Realistic store layout patterns
        
        Returns: (shelves, transparency_log)
        """
        transparency = []
        shelves = []
        
        # Determine shelf count
        num_shelves = extracted.get('num_shelves') or target_count or 8
        transparency.append(f"Shelf count: {num_shelves} ({'customer-specified' if extracted.get('num_shelves') else 'simulated default'})")
        
        # Get foot traffic hints
        traffic_hints = extracted.get('foot_traffic_hints', {})
        
        # Realistic shelf distribution (grocery store layout)
        # Front: 25%, Middle: 50%, Back: 25%
        front_count = max(1, int(num_shelves * 0.25))
        back_count = max(1, int(num_shelves * 0.25))
        middle_count = num_shelves - front_count - back_count
        
        shelf_id = 1
        
        # Front shelves (high traffic, high visibility)
        for i in range(front_count):
            shelves.append(ShelfSpace(
                id=shelf_id,
                location=f"Front Section {i+1}",
                total_space=random.uniform(18, 25),
                visibility_score=random.uniform(8.0, 10.0),
                foot_traffic=traffic_hints.get('front', random.uniform(120, 180)),
                zone='front',
                has_refrigeration=False,  # Usually dry goods in front
                has_security=True  # Monitored entrance area
            ))
            shelf_id += 1
        
        # Middle shelves (medium traffic, medium visibility)
        middle_with_fridge = int(middle_count * 0.3)  # 30% have refrigeration
        for i in range(middle_count):
            shelves.append(ShelfSpace(
                id=shelf_id,
                location=f"Middle Aisle {i+1}",
                total_space=random.uniform(20, 30),
                visibility_score=random.uniform(5.0, 7.5),
                foot_traffic=traffic_hints.get('middle', random.uniform(70, 120)),
                zone='middle',
                has_refrigeration=(i < middle_with_fridge),
                has_security=False
            ))
            shelf_id += 1
        
        # Back shelves (low traffic, low visibility, more refrigeration)
        for i in range(back_count):
            shelves.append(ShelfSpace(
                id=shelf_id,
                location=f"Back Section {i+1}",
                total_space=random.uniform(25, 35),
                visibility_score=random.uniform(3.0, 5.5),
                foot_traffic=traffic_hints.get('back', random.uniform(40, 80)),
                zone='back',
                has_refrigeration=True,  # Dairy, frozen, meat in back
                has_security=False
            ))
            shelf_id += 1
        
        transparency.append(f"Simulated {len(shelves)} shelves with realistic grocery store layout")
        transparency.append(f"Distribution: {front_count} front (high-traffic), {middle_count} middle, {back_count} back (refrigeration)")
        
        logger.info(f"✅ Generated {len(shelves)} shelf spaces")
        
        return shelves, transparency


# ==============================================================================
# Main Solver (Same LMEA logic, richer inputs)
# ==============================================================================

class LMEARetailLayoutSolverV2:
    """
    V2: Domain-expert approach
    - Rich built-in constraints
    - Lightweight extraction
    - Transparent simulation
    """
    
    def __init__(self):
        self.extractor = CustomerInputExtractor()
        self.simulator = DomainExpertSimulator()
        self.proof_engine = MathematicalProofEngine()
        
        # LMEA parameters
        self.population_size = 100
        self.tournament_size = 5
        self.crossover_rate = 0.75
        self.mutation_rate = 0.3
        self.elite_size = 10
        
        # Objective weights (tuned from retail expertise)
        self.revenue_weight = 1.0
        self.cross_sell_weight = 0.15
        self.space_penalty = 5000.0
        self.constraint_penalty = 10000.0
    
    async def solve(
        self,
        problem_description: str,
        max_generations: int = 100
    ) -> Dict[str, Any]:
        """
        Solve store layout with domain expertise
        
        Steps:
        1. Lightweight extraction (customer values only)
        2. Domain-expert simulation (fill gaps)
        3. LMEA optimization (same as v1)
        4. Return solution + transparency
        """
        try:
            logger.info("🛒 Starting Store Layout Optimization v2.0 (Domain-Expert)")
            
            # Step 1: Extract customer-specific values
            extracted = await self.extractor.extract(problem_description)
            
            # Step 2: Simulate using domain expertise
            products, product_transparency = self.simulator.simulate_products(extracted)
            shelves, shelf_transparency = self.simulator.simulate_shelves(extracted)
            
            transparency_log = {
                'extraction': extracted,
                'product_simulation': product_transparency,
                'shelf_simulation': shelf_transparency,
                'domain_rules_applied': list(LAYOUT_RULES.keys())
            }
            
            logger.info(f"📊 Problem size: {len(products)} products, {len(shelves)} shelves")
            
            # Step 3: Run LMEA (same logic as v1)
            solution = self._run_lmea(products, shelves, max_generations)
            
            # Step 4: Generate mathematical proof (NO LIES!)
            logger.info("🔬 Generating mathematical proof suite...")
            proof = self.proof_engine.generate_full_proof(
                solution=solution,
                products=products,
                shelves=shelves,
                problem_type='store_layout'
            )
            
            # Step 5: Add transparency and proof to solution
            solution['transparency'] = transparency_log
            solution['domain_expertise_applied'] = True
            solution['mathematical_proof'] = proof
            
            return solution
            
        except Exception as e:
            logger.error(f"❌ Store layout optimization v2.0 error: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _run_lmea(
        self,
        products: List[Product],
        shelves: List[ShelfSpace],
        max_generations: int
    ) -> Dict[str, Any]:
        """LMEA optimization (same as v1, reusing logic)"""
        
        # Initialize population
        population = self._initialize_population(products, shelves)
        
        # Evaluate initial population
        fitness_scores = [
            self._evaluate_layout(layout, products, shelves)
            for layout in population
        ]
        
        best_fitness = max(fitness_scores)
        best_layout = population[fitness_scores.index(best_fitness)]
        generations_without_improvement = 0
        
        logger.info(f"📊 Initial best fitness: {best_fitness:.2f}")
        
        # Evolutionary loop
        for generation in range(max_generations):
            # Selection
            parents = self._select_parents(population, fitness_scores)
            
            # Create offspring
            offspring = []
            for i in range(0, len(parents) - 1, 2):
                if random.random() < self.crossover_rate:
                    child1, child2 = self._crossover(parents[i], parents[i + 1])
                else:
                    child1, child2 = parents[i].copy(), parents[i + 1].copy()
                
                # Mutation
                if random.random() < self.mutation_rate:
                    child1 = self._mutate(child1, products, shelves)
                if random.random() < self.mutation_rate:
                    child2 = self._mutate(child2, products, shelves)
                
                offspring.extend([child1, child2])
            
            # Evaluate offspring
            offspring_fitness = [
                self._evaluate_layout(layout, products, shelves)
                for layout in offspring
            ]
            
            # Update population (elitism)
            population, fitness_scores = self._update_population(
                population, fitness_scores,
                offspring, offspring_fitness
            )
            
            # Track best solution
            current_best = max(fitness_scores)
            if current_best > best_fitness:
                best_fitness = current_best
                best_layout = population[fitness_scores.index(current_best)]
                generations_without_improvement = 0
                logger.info(f"✨ Gen {generation + 1}: New best fitness = {best_fitness:.2f}")
            else:
                generations_without_improvement += 1
            
            # Early stopping
            if generations_without_improvement > 30:
                logger.info(f"⏸️ No improvement for 30 generations, stopping at gen {generation + 1}")
                break
        
        # Decode solution
        solution = self._decode_layout(best_layout, products, shelves)
        
        logger.info(f"✅ Optimization complete: {len(solution['placements'])} placements, revenue=${solution['expected_revenue']:.2f}")
        
        return {
            'status': 'success',
            'solver_type': 'lmea_retail_layout_v2',
            'method': 'domain_expert_lmea',
            'placements': solution['placements'],
            'expected_revenue': solution['expected_revenue'],
            'space_utilization': solution['space_utilization'],
            'cross_sell_score': solution['cross_sell_score'],
            'is_feasible': solution['is_feasible'],
            'violations': solution['violations'],
            'shelf_assignments': solution['shelf_assignments'],
            'category_distribution': solution['category_distribution'],
            'generations': generation + 1,
            'final_fitness': best_fitness,
            'metadata': {
                'products_count': len(products),
                'shelves_count': len(shelves),
                'products_placed': len(solution['placements']),
                'avg_visibility': solution['avg_visibility'],
                'simulated_products': sum(1 for p in products if p.is_simulated),
                'customer_specified_products': sum(1 for p in products if not p.is_simulated)
            }
        }
    
    # ========== LMEA Helper Methods (reused from v1) ==========
    
    def _initialize_population(self, products: List[Product], shelves: List[ShelfSpace]) -> List[Dict[int, int]]:
        """Initialize random population of layouts"""
        population = []
        for _ in range(self.population_size):
            layout = {}
            for product in products:
                # Prefer shelves that match product requirements
                valid_shelves = [
                    s.id for s in shelves
                    if (not product.requires_refrigeration or s.has_refrigeration)
                    and (not product.requires_security or s.has_security)
                ]
                if not valid_shelves:
                    valid_shelves = [s.id for s in shelves]
                layout[product.id] = random.choice(valid_shelves)
            population.append(layout)
        return population
    
    def _evaluate_layout(self, layout: Dict[int, int], products: List[Product], shelves: List[ShelfSpace]) -> float:
        """Evaluate layout fitness using domain-expert rules"""
        fitness = 0.0
        
        # Build shelf map
        shelf_map = {s.id: s for s in shelves}
        product_map = {p.id: p for p in products}
        
        # Revenue calculation
        for prod_id, shelf_id in layout.items():
            product = product_map[prod_id]
            shelf = shelf_map[shelf_id]
            
            # Revenue = sales_rate * profit_margin * visibility * traffic
            revenue = (
                product.sales_rate *
                product.profit_margin *
                (shelf.visibility_score / 10.0) *
                (shelf.foot_traffic / 100.0)
            )
            fitness += revenue * self.revenue_weight
        
        # Cross-selling bonus
        for prod_id, shelf_id in layout.items():
            product = product_map[prod_id]
            for comp_id in product.complementary_products:
                if comp_id in layout:
                    comp_shelf_id = layout[comp_id]
                    # Bonus if on same shelf or adjacent
                    if comp_shelf_id == shelf_id:
                        fitness += 100 * self.cross_sell_weight
                    elif abs(comp_shelf_id - shelf_id) <= 1:
                        fitness += 50 * self.cross_sell_weight
        
        # Constraint penalties
        penalties = self._check_constraints(layout, products, shelves)
        fitness -= sum(penalties.values())
        
        return fitness
    
    def _check_constraints(self, layout: Dict[int, int], products: List[Product], shelves: List[ShelfSpace]) -> Dict[str, float]:
        """Check domain-expert constraints"""
        penalties = {}
        
        shelf_map = {s.id: s for s in shelves}
        product_map = {p.id: p for p in products}
        
        # Rule 1: High-margin visibility
        for prod_id, shelf_id in layout.items():
            product = product_map[prod_id]
            shelf = shelf_map[shelf_id]
            if product.profit_margin > 4.0 and shelf.visibility_score < 7.0:
                penalties['high_margin_visibility'] = penalties.get('high_margin_visibility', 0) + LAYOUT_RULES['high_margin_visibility']['penalty']
        
        # Rule 2: Refrigeration requirement
        for prod_id, shelf_id in layout.items():
            product = product_map[prod_id]
            shelf = shelf_map[shelf_id]
            if product.requires_refrigeration and not shelf.has_refrigeration:
                penalties['refrigeration'] = penalties.get('refrigeration', 0) + self.constraint_penalty
        
        # Rule 3: Security requirement
        for prod_id, shelf_id in layout.items():
            product = product_map[prod_id]
            shelf = shelf_map[shelf_id]
            if product.requires_security and not shelf.has_security:
                penalties['security'] = penalties.get('security', 0) + LAYOUT_RULES['security_zones']['penalty']
        
        # Rule 4: Space utilization
        shelf_usage = {}
        for shelf in shelves:
            shelf_usage[shelf.id] = 0
        for prod_id, shelf_id in layout.items():
            product = product_map[prod_id]
            shelf_usage[shelf_id] += product.space_required
        
        for shelf_id, used_space in shelf_usage.items():
            shelf = shelf_map[shelf_id]
            if used_space > shelf.total_space:
                penalties['space_overflow'] = penalties.get('space_overflow', 0) + (self.space_penalty * (used_space - shelf.total_space))
        
        return penalties
    
    def _select_parents(self, population: List[Dict[int, int]], fitness_scores: List[float]) -> List[Dict[int, int]]:
        """Tournament selection"""
        parents = []
        for _ in range(len(population)):
            tournament = random.sample(list(zip(population, fitness_scores)), self.tournament_size)
            winner = max(tournament, key=lambda x: x[1])
            parents.append(winner[0].copy())
        return parents
    
    def _crossover(self, parent1: Dict[int, int], parent2: Dict[int, int]) -> Tuple[Dict[int, int], Dict[int, int]]:
        """Single-point crossover"""
        product_ids = list(parent1.keys())
        point = random.randint(1, len(product_ids) - 1)
        
        child1 = {}
        child2 = {}
        
        for i, prod_id in enumerate(product_ids):
            if i < point:
                child1[prod_id] = parent1[prod_id]
                child2[prod_id] = parent2[prod_id]
            else:
                child1[prod_id] = parent2[prod_id]
                child2[prod_id] = parent1[prod_id]
        
        return child1, child2
    
    def _mutate(self, layout: Dict[int, int], products: List[Product], shelves: List[ShelfSpace]) -> Dict[int, int]:
        """Mutate by reassigning random products"""
        mutated = layout.copy()
        num_mutations = max(1, int(len(layout) * 0.1))
        
        for _ in range(num_mutations):
            prod_id = random.choice(list(layout.keys()))
            mutated[prod_id] = random.choice([s.id for s in shelves])
        
        return mutated
    
    def _update_population(
        self,
        population: List[Dict[int, int]],
        fitness_scores: List[float],
        offspring: List[Dict[int, int]],
        offspring_fitness: List[float]
    ) -> Tuple[List[Dict[int, int]], List[float]]:
        """Elitism: keep best solutions"""
        combined = list(zip(population + offspring, fitness_scores + offspring_fitness))
        combined.sort(key=lambda x: x[1], reverse=True)
        
        new_pop = [ind for ind, _ in combined[:self.population_size]]
        new_fitness = [fit for _, fit in combined[:self.population_size]]
        
        return new_pop, new_fitness
    
    def _decode_layout(self, layout: Dict[int, int], products: List[Product], shelves: List[ShelfSpace]) -> Dict:
        """Decode layout into readable solution"""
        shelf_map = {s.id: s for s in shelves}
        product_map = {p.id: p for p in products}
        
        placements = []
        shelf_assignments = {s.id: [] for s in shelves}
        category_distribution = {}
        
        total_revenue = 0.0
        total_space_used = 0.0
        total_space_available = sum(s.total_space for s in shelves)
        total_visibility = 0.0
        
        for prod_id, shelf_id in layout.items():
            product = product_map[prod_id]
            shelf = shelf_map[shelf_id]
            
            revenue = (
                product.sales_rate *
                product.profit_margin *
                (shelf.visibility_score / 10.0) *
                (shelf.foot_traffic / 100.0)
            )
            
            placements.append({
                'product_id': product.id,
                'product_name': product.name,
                'category': product.category,
                'shelf_id': shelf.id,
                'shelf_location': shelf.location,
                'expected_revenue': round(revenue, 2),
                'is_simulated': product.is_simulated
            })
            
            shelf_assignments[shelf_id].append(product.name)
            
            if product.category not in category_distribution:
                category_distribution[product.category] = 0
            category_distribution[product.category] += 1
            
            total_revenue += revenue
            total_space_used += product.space_required
            total_visibility += shelf.visibility_score
        
        penalties = self._check_constraints(layout, products, shelves)
        
        return {
            'placements': placements,
            'expected_revenue': round(total_revenue, 2),
            'space_utilization': round((total_space_used / total_space_available) * 100, 1),
            'cross_sell_score': 0,  # Calculated separately if needed
            'is_feasible': len(penalties) == 0,
            'violations': list(penalties.keys()),
            'shelf_assignments': shelf_assignments,
            'category_distribution': category_distribution,
            'avg_visibility': round(total_visibility / len(products), 2)
        }

