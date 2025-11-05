"""
Synthetic Data Generator for Optimization Problems
==================================================

Generates realistic synthetic data based on LLM-extracted metadata.
This solves the "50 products" problem - instead of asking LLM to generate
50 JSON objects (error-prone), we ask it to extract counts/categories,
then generate the data programmatically.
"""

import random
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class SyntheticDataGenerator:
    """Generates synthetic data for optimization problems"""
    
    def generate_retail_products_and_shelves(self, product_count: int = 10, shelf_count: int = 4, **kwargs) -> Dict[str, Any]:
        """
        Wrapper method for retail layout - combines products and shelves.
        Called by universal parser via config.
        """
        # Calculate total space needed
        total_product_space = product_count * 1.5  # Avg 1.5 units per product
        
        # Generate products
        products = self.generate_retail_products(
            count=product_count,
            mentioned_products=kwargs.get('mentioned_products', []),
            high_margin_products=kwargs.get('high_margin_products', []),
            categories=kwargs.get('categories', [])
        )
        
        # Generate shelves
        shelves = self.generate_retail_shelves(
            count=shelf_count,
            total_product_space=total_product_space,
            has_refrigeration=any(p.get('needs_refrigeration', False) for p in products),
            has_security=any(p.get('needs_security', False) for p in products)
        )
        
        return {
            'products': products,
            'shelves': shelves,
            'complementary_pairs': []  # Can be enhanced later
        }
    
    # Domain-specific templates
    RETAIL_LAYOUT_CATEGORIES = {
        'dairy': {
            'products': ['Milk', 'Cheese', 'Yogurt', 'Butter', 'Cream', 'Cottage Cheese', 'Sour Cream'],
            'space_range': (1.0, 3.0),
            'sales_range': (20.0, 50.0),
            'margin_range': (0.15, 0.30),
            'needs_refrigeration': True
        },
        'produce': {
            'products': ['Apples', 'Bananas', 'Oranges', 'Lettuce', 'Tomatoes', 'Potatoes', 'Carrots', 'Onions'],
            'space_range': (0.5, 2.0),
            'sales_range': (15.0, 40.0),
            'margin_range': (0.20, 0.40),
            'needs_refrigeration': False
        },
        'beverages': {
            'products': ['Soda', 'Juice', 'Water', 'Energy Drinks', 'Tea', 'Coffee', 'Sports Drinks'],
            'space_range': (1.0, 3.0),
            'sales_range': (25.0, 60.0),
            'margin_range': (0.20, 0.35),
            'needs_refrigeration': False
        },
        'frozen': {
            'products': ['Ice Cream', 'Frozen Pizza', 'Frozen Vegetables', 'Frozen Meals', 'Popsicles'],
            'space_range': (2.0, 4.0),
            'sales_range': (10.0, 30.0),
            'margin_range': (0.25, 0.40),
            'needs_refrigeration': True
        },
        'snacks': {
            'products': ['Chips', 'Crackers', 'Cookies', 'Candy', 'Nuts', 'Granola Bars', 'Popcorn'],
            'space_range': (0.5, 2.0),
            'sales_range': (20.0, 55.0),
            'margin_range': (0.30, 0.45),
            'needs_refrigeration': False
        },
        'canned': {
            'products': ['Soup', 'Beans', 'Vegetables', 'Fruit', 'Tuna', 'Tomato Sauce'],
            'space_range': (0.5, 1.5),
            'sales_range': (10.0, 25.0),
            'margin_range': (0.20, 0.30),
            'needs_refrigeration': False
        },
        'household': {
            'products': ['Paper Towels', 'Toilet Paper', 'Detergent', 'Dish Soap', 'Trash Bags', 'Cleaning Spray'],
            'space_range': (2.0, 5.0),
            'sales_range': (15.0, 35.0),
            'margin_range': (0.25, 0.35),
            'needs_refrigeration': False
        },
        'health': {
            'products': ['Vitamins', 'Pain Relief', 'Band-Aids', 'Hand Sanitizer', 'Sunscreen'],
            'space_range': (0.3, 1.0),
            'sales_range': (5.0, 20.0),
            'margin_range': (0.35, 0.50),
            'needs_refrigeration': False,
            'needs_security': True
        },
        'bakery': {
            'products': ['Bread', 'Bagels', 'Muffins', 'Donuts', 'Pastries', 'Rolls'],
            'space_range': (1.0, 3.0),
            'sales_range': (25.0, 50.0),
            'margin_range': (0.30, 0.45),
            'needs_refrigeration': False
        },
        'pantry': {
            'products': ['Cereal', 'Pasta', 'Rice', 'Flour', 'Sugar', 'Oil', 'Spices', 'Sauces'],
            'space_range': (0.5, 2.0),
            'sales_range': (10.0, 30.0),
            'margin_range': (0.25, 0.40),
            'needs_refrigeration': False
        }
    }
    
    def generate_retail_products(
        self,
        count: int,
        mentioned_products: List[str] = None,
        high_margin_products: List[str] = None,
        categories: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate synthetic retail products
        
        Args:
            count: Number of products to generate
            mentioned_products: Specific products mentioned by user (e.g., ['coffee', 'snacks'])
            high_margin_products: Products that should have high margins
            categories: Preferred categories to sample from
            
        Returns:
            List of product dictionaries
        """
        logger.info(f"🔧 Generating {count} synthetic retail products")
        
        products = []
        used_names = set()
        
        # 1. Generate mentioned products first
        if mentioned_products:
            for mentioned in mentioned_products[:count]:
                product = self._generate_product_by_name(
                    mentioned,
                    len(products) + 1,
                    high_margin=mentioned in (high_margin_products or [])
                )
                if product and product['name'] not in used_names:
                    products.append(product)
                    used_names.add(product['name'])
        
        # 2. Fill remaining with diverse products
        # Filter out unknown categories (LLM might return 'breakfast' which doesn't exist)
        if categories:
            available_categories = [c for c in categories if c in self.RETAIL_LAYOUT_CATEGORIES]
            if not available_categories:
                logger.warning(f"⚠️ LLM returned unknown categories {categories}, using all categories")
                available_categories = list(self.RETAIL_LAYOUT_CATEGORIES.keys())
        else:
            available_categories = list(self.RETAIL_LAYOUT_CATEGORIES.keys())
        
        while len(products) < count:
            # Pick a random category (weighted by remaining need)
            category = random.choice(available_categories)
            cat_data = self.RETAIL_LAYOUT_CATEGORIES[category]
            
            # Pick a random product from this category
            product_name = random.choice(cat_data['products'])
            full_name = f"{product_name}"
            
            # Avoid duplicates
            if full_name in used_names:
                # Add variant
                full_name = f"{product_name} ({random.choice(['Store Brand', 'Premium', 'Organic', 'Family Size'])})"
            
            if full_name not in used_names:
                product = {
                    'id': f"prod_{len(products) + 1}",
                    'name': full_name,
                    'category': category,
                    'space_required': round(random.uniform(*cat_data['space_range']), 2),
                    'sales_rate': round(random.uniform(*cat_data['sales_range']), 1),
                    'profit_margin': round(random.uniform(*cat_data['margin_range']), 2),
                    'needs_refrigeration': cat_data.get('needs_refrigeration', False),
                    'needs_security': cat_data.get('needs_security', False)
                }
                products.append(product)
                used_names.add(full_name)
        
        logger.info(f"✅ Generated {len(products)} products across {len(set(p['category'] for p in products))} categories")
        return products
    
    def _generate_product_by_name(
        self,
        name_hint: str,
        product_id: int,
        high_margin: bool = False
    ) -> Dict[str, Any]:
        """Generate a product based on a name hint (e.g., 'coffee' -> Coffee product)"""
        name_hint_lower = name_hint.lower()
        
        # Find matching category
        for category, cat_data in self.RETAIL_LAYOUT_CATEGORIES.items():
            # Check if hint matches category or any product in category
            if name_hint_lower in category.lower() or any(name_hint_lower in p.lower() for p in cat_data['products']):
                # Find exact product name or use category default
                product_name = next(
                    (p for p in cat_data['products'] if name_hint_lower in p.lower()),
                    cat_data['products'][0]
                )
                
                # Adjust margin if high-margin requested
                margin_range = cat_data['margin_range']
                if high_margin:
                    margin_range = (max(margin_range[0], 0.30), max(margin_range[1], 0.45))
                
                return {
                    'id': f"prod_{product_id}",
                    'name': product_name,
                    'category': category,
                    'space_required': round(random.uniform(*cat_data['space_range']), 2),
                    'sales_rate': round(random.uniform(*cat_data['sales_range']), 1),
                    'profit_margin': round(random.uniform(*margin_range), 2),
                    'needs_refrigeration': cat_data.get('needs_refrigeration', False),
                    'needs_security': cat_data.get('needs_security', False)
                }
        
        # Fallback: generic product
        return {
            'id': f"prod_{product_id}",
            'name': name_hint.title(),
            'category': 'pantry',
            'space_required': 1.0,
            'sales_rate': 15.0,
            'profit_margin': 0.25,
            'needs_refrigeration': False,
            'needs_security': False
        }
    
    def generate_retail_shelves(
        self,
        count: int,
        total_product_space: float,
        has_refrigeration: bool = True,
        has_security: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Generate synthetic shelf spaces
        
        Args:
            count: Number of shelves to generate
            total_product_space: Total space needed for products (to ensure feasibility)
            has_refrigeration: Whether any shelves should have refrigeration
            has_security: Whether any shelves should have security
            
        Returns:
            List of shelf dictionaries
        """
        logger.info(f"🔧 Generating {count} synthetic shelves")
        
        # Calculate average shelf space needed
        avg_shelf_space = (total_product_space * 1.2) / count  # 20% buffer for feasibility
        
        shelves = []
        zones = ['front', 'middle', 'back']
        
        for i in range(count):
            zone = zones[i % len(zones)]
            
            # Visibility and foot traffic based on zone
            if zone == 'front':
                visibility = round(random.uniform(0.8, 1.0), 1)
                foot_traffic = round(random.uniform(0.8, 1.0), 1)
            elif zone == 'middle':
                visibility = round(random.uniform(0.6, 0.8), 1)
                foot_traffic = round(random.uniform(0.6, 0.8), 1)
            else:  # back
                visibility = round(random.uniform(0.3, 0.6), 1)
                foot_traffic = round(random.uniform(0.3, 0.6), 1)
            
            # Refrigeration for some shelves
            shelf_has_refrigeration = has_refrigeration and (i < count // 3)  # First third get refrigeration
            
            # Security for some shelves
            shelf_has_security = has_security and (i % 4 == 0)  # Every 4th shelf
            
            # Determine zone type
            if shelf_has_refrigeration:
                zone_type = "refrigerated"
            elif shelf_has_security:
                zone_type = "secured"
            else:
                zone_type = "normal"
            
            shelf = {
                'id': f"shelf_{i + 1}",
                'total_space': round(avg_shelf_space * random.uniform(0.8, 1.2), 1),
                'visibility_score': visibility,
                'foot_traffic': foot_traffic,
                'zone': zone_type,
                'has_security': shelf_has_security
            }
            shelves.append(shelf)
        
        total_shelf_space = sum(s['total_space'] for s in shelves)
        logger.info(f"✅ Generated {count} shelves with total space {total_shelf_space:.1f} (products need {total_product_space:.1f})")
        
        return shelves


    # ============================================================================
    # VRP (Vehicle Routing Problem) Synthetic Data
    # ============================================================================
    
    def generate_vrp_data(
        self,
        customer_count: int,
        vehicle_count: int,
        depot_count: int = 1,
        has_time_windows: bool = False,
        has_capacity: bool = True
    ) -> Dict[str, Any]:
        """Generate synthetic VRP data"""
        logger.info(f"🔧 Generating {customer_count} customers, {vehicle_count} vehicles, {depot_count} depots")
        
        # Generate depots
        depots = []
        for i in range(depot_count):
            depots.append({
                'id': f"depot_{i+1}",
                'location': {'x': random.uniform(0, 100), 'y': random.uniform(0, 100)},
                'capacity': random.randint(50, 100) if has_capacity else None
            })
        
        # Generate customers
        customers = []
        for i in range(customer_count):
            customer = {
                'id': f"customer_{i+1}",
                'location': {'x': random.uniform(0, 100), 'y': random.uniform(0, 100)},
                'demand': random.randint(1, 20) if has_capacity else 0,
                'service_time': random.randint(10, 30)
            }
            if has_time_windows:
                start = random.randint(8, 16) * 60  # minutes
                customer['time_window'] = {'start': start, 'end': start + random.randint(120, 240)}
            customers.append(customer)
        
        # Generate vehicles
        vehicles = []
        for i in range(vehicle_count):
            vehicles.append({
                'id': f"vehicle_{i+1}",
                'capacity': random.randint(30, 60) if has_capacity else None,
                'cost_per_km': round(random.uniform(0.5, 2.0), 2),
                'max_distance': random.randint(200, 400)
            })
        
        logger.info(f"✅ Generated VRP data: {len(customers)} customers, {len(vehicles)} vehicles")
        return {'customers': customers, 'vehicles': vehicles, 'depots': depots}
    
    # ============================================================================
    # Job Shop Scheduling Synthetic Data
    # ============================================================================
    
    def generate_job_shop_data(
        self,
        job_count: int,
        machine_count: int
    ) -> Dict[str, Any]:
        """Generate synthetic job shop data"""
        logger.info(f"🔧 Generating {job_count} jobs, {machine_count} machines")
        
        # Generate machines
        machines = []
        for i in range(machine_count):
            machines.append({
                'id': f"machine_{i+1}",
                'name': f"Machine {i+1}",
                'speed_factor': round(random.uniform(0.8, 1.2), 2),
                'available_hours': 24
            })
        
        # Generate jobs
        jobs = []
        for i in range(job_count):
            # Each job has 2-5 operations
            num_operations = random.randint(2, min(5, machine_count))
            operations = []
            machine_sequence = random.sample(range(machine_count), num_operations)
            
            for j, machine_idx in enumerate(machine_sequence):
                operations.append({
                    'operation_id': f"job{i+1}_op{j+1}",
                    'machine_id': f"machine_{machine_idx+1}",
                    'duration': random.randint(10, 120),
                    'precedence': [f"job{i+1}_op{j}"] if j > 0 else []
                })
            
            jobs.append({
                'id': f"job_{i+1}",
                'name': f"Job {i+1}",
                'operations': operations,
                'due_date': random.randint(200, 500),
                'priority': random.choice(['high', 'medium', 'low'])
            })
        
        logger.info(f"✅ Generated {len(jobs)} jobs with {sum(len(j['operations']) for j in jobs)} total operations")
        return {'jobs': jobs, 'machines': machines}
    
    # ============================================================================
    # Workforce Rostering Synthetic Data
    # ============================================================================
    
    def generate_workforce_data(
        self,
        worker_count: int,
        shift_count: int,
        days: int = 7
    ) -> Dict[str, Any]:
        """Generate synthetic workforce rostering data"""
        logger.info(f"🔧 Generating {worker_count} workers, {shift_count} shifts over {days} days")
        
        skills = ['cashier', 'stock', 'manager', 'customer_service', 'cleaning']
        
        # Generate workers
        workers = []
        for i in range(worker_count):
            workers.append({
                'id': f"worker_{i+1}",
                'name': f"Worker {i+1}",
                'skills': random.sample(skills, random.randint(1, 3)),
                'max_hours_per_week': random.choice([20, 30, 40]),
                'hourly_rate': round(random.uniform(15, 35), 2),
                'availability': random.choice(['full', 'morning', 'evening', 'weekend'])
            })
        
        # Generate shifts
        shifts = []
        shift_types = ['morning', 'afternoon', 'evening', 'night']
        for day in range(days):
            for shift_type in shift_types[:shift_count//days + 1]:
                shifts.append({
                    'id': f"shift_{len(shifts)+1}",
                    'day': day,
                    'type': shift_type,
                    'start_hour': {'morning': 6, 'afternoon': 14, 'evening': 18, 'night': 22}[shift_type],
                    'duration': 8,
                    'required_workers': random.randint(2, 5),
                    'required_skills': random.sample(skills, random.randint(1, 2))
                })
        
        logger.info(f"✅ Generated {len(workers)} workers and {len(shifts)} shifts")
        return {'workers': workers, 'shifts': shifts[:shift_count]}
    
    # ============================================================================
    # Maintenance Scheduling Synthetic Data
    # ============================================================================
    
    def generate_maintenance_data(
        self,
        equipment_count: int,
        task_count: int,
        technician_count: int = 5
    ) -> Dict[str, Any]:
        """Generate synthetic maintenance scheduling data"""
        logger.info(f"🔧 Generating {equipment_count} equipment, {task_count} tasks, {technician_count} technicians")
        
        # Generate equipment
        equipment = []
        for i in range(equipment_count):
            equipment.append({
                'id': f"equipment_{i+1}",
                'name': f"Equipment {i+1}",
                'type': random.choice(['pump', 'motor', 'valve', 'conveyor', 'hvac']),
                'criticality': random.choice(['high', 'medium', 'low']),
                'last_maintenance': random.randint(0, 90),
                'maintenance_interval': random.randint(30, 180)
            })
        
        # Generate tasks
        tasks = []
        for i in range(task_count):
            tasks.append({
                'id': f"task_{i+1}",
                'equipment_id': f"equipment_{random.randint(1, equipment_count)}",
                'type': random.choice(['inspection', 'repair', 'replacement', 'calibration']),
                'duration': random.randint(30, 240),
                'required_skills': random.sample(['electrical', 'mechanical', 'hydraulic', 'software'], random.randint(1, 2)),
                'urgency': random.choice(['urgent', 'normal', 'scheduled'])
            })
        
        # Generate technicians
        technicians = []
        for i in range(technician_count):
            technicians.append({
                'id': f"technician_{i+1}",
                'name': f"Technician {i+1}",
                'skills': random.sample(['electrical', 'mechanical', 'hydraulic', 'software'], random.randint(2, 4)),
                'hourly_cost': round(random.uniform(50, 100), 2)
            })
        
        logger.info(f"✅ Generated maintenance data")
        return {'equipment': equipment, 'tasks': tasks, 'technicians': technicians}
    
    # ============================================================================
    # Retail Promotion Scheduling Synthetic Data
    # ============================================================================
    
    def generate_promotion_data(
        self,
        product_count: int,
        promotion_slot_count: int
    ) -> Dict[str, Any]:
        """Generate synthetic promotion scheduling data"""
        logger.info(f"🔧 Generating {product_count} products, {promotion_slot_count} promotion slots")
        
        categories = ['electronics', 'clothing', 'food', 'home', 'sports']
        
        # Generate products
        products = []
        for i in range(product_count):
            products.append({
                'id': f"product_{i+1}",
                'name': f"Product {i+1}",
                'category': random.choice(categories),
                'base_sales': random.randint(100, 1000),
                'margin': round(random.uniform(0.15, 0.45), 2),
                'inventory': random.randint(500, 5000),
                'promotion_uplift': round(random.uniform(1.2, 3.0), 2)
            })
        
        # Generate promotion slots
        slots = []
        for i in range(promotion_slot_count):
            slots.append({
                'id': f"slot_{i+1}",
                'week': i // 4 + 1,
                'channel': random.choice(['email', 'social', 'in-store', 'website']),
                'reach': random.randint(1000, 50000),
                'cost': random.randint(500, 5000)
            })
        
        logger.info(f"✅ Generated promotion data")
        return {'products': products, 'promotion_slots': slots}
    
    # ============================================================================
    # Portfolio Rebalancing Synthetic Data
    # ============================================================================
    
    def generate_portfolio_data(
        self,
        asset_count: int
    ) -> Dict[str, Any]:
        """Generate synthetic portfolio data"""
        logger.info(f"🔧 Generating portfolio with {asset_count} assets")
        
        asset_types = ['stock', 'bond', 'etf', 'commodity', 'crypto']
        sectors = ['tech', 'healthcare', 'finance', 'energy', 'consumer']
        
        assets = []
        for i in range(asset_count):
            assets.append({
                'id': f"asset_{i+1}",
                'symbol': f"SYM{i+1}",
                'type': random.choice(asset_types),
                'sector': random.choice(sectors),
                'current_price': round(random.uniform(10, 500), 2),
                'expected_return': round(random.uniform(0.05, 0.20), 3),
                'volatility': round(random.uniform(0.10, 0.40), 3),
                'current_allocation': round(random.uniform(0, 0.15), 3)
            })
        
        logger.info(f"✅ Generated {len(assets)} assets")
        return {
            'assets': assets,
            'total_portfolio_value': 1000000,
            'risk_tolerance': 'moderate',
            'target_sectors': {s: 0.20 for s in sectors}
        }
    
    # ============================================================================
    # Trading Schedule Synthetic Data
    # ============================================================================
    
    def generate_trading_data(
        self,
        trade_count: int
    ) -> Dict[str, Any]:
        """Generate synthetic trading schedule data"""
        logger.info(f"🔧 Generating {trade_count} trades")
        
        strategies = ['momentum', 'mean_reversion', 'arbitrage', 'pairs_trading']
        
        trades = []
        for i in range(trade_count):
            trades.append({
                'id': f"trade_{i+1}",
                'symbol': f"STOCK{i%20+1}",
                'action': random.choice(['buy', 'sell']),
                'quantity': random.randint(100, 10000),
                'expected_price': round(random.uniform(50, 500), 2),
                'strategy': random.choice(strategies),
                'urgency': random.choice(['high', 'medium', 'low']),
                'max_slippage': round(random.uniform(0.01, 0.05), 3),
                'time_window': random.randint(60, 300)
            })
        
        logger.info(f"✅ Generated {len(trades)} trades")
        return {
            'trades': trades,
            'market_hours': {'start': 9.5, 'end': 16.0},
            'liquidity_factor': 0.8
        }

    
    # ===========================
    # FINSERV: CUSTOMER ONBOARDING
    # ===========================
    
    def generate_customer_onboarding(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate synthetic customer onboarding data
        
        Creates portfolio holdings with realistic allocations, risk profiles,
        and current market conditions for optimization.
        """
        num_holdings = metadata.get('num_holdings', random.randint(5, 15))
        risk_tolerance = metadata.get('risk_tolerance', random.randint(3, 8))  # 1-10 scale
        total_value = metadata.get('total_portfolio_value', random.randint(250000, 2000000))
        
        logger.info(f"🏦 Generating customer onboarding data: {num_holdings} holdings, ${total_value:,}")
        
        # Common stock tickers for retail portfolios
        tickers = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'JPM',
            'V', 'JNJ', 'WMT', 'PG', 'DIS', 'NFLX', 'PYPL', 'INTC', 'CSCO',
            'VTI', 'VOO', 'QQQ', 'BND', 'AGG', 'TLT', 'GLD', 'VNQ'
        ]
        
        # Generate current holdings with some concentration issues
        holdings = []
        selected_tickers = random.sample(tickers, min(num_holdings, len(tickers)))
        
        # Create biased allocation (to show optimization opportunity)
        weights = [random.random() for _ in range(len(selected_tickers))]
        total_weight = sum(weights)
        weights = [w/total_weight for w in weights]
        
        # Intentionally overweight first 3 (to show concentration risk)
        if len(weights) >= 3:
            weights[0] *= 1.5
            weights[1] *= 1.3
            weights[2] *= 1.2
            total_weight = sum(weights)
            weights = [w/total_weight for w in weights]
        
        for ticker, weight in zip(selected_tickers, weights):
            value = total_value * weight
            shares = int(value / random.uniform(50, 500))  # Assumed price
            
            holdings.append({
                'ticker': ticker,
                'shares': shares,
                'current_value': round(value, 2),
                'weight': round(weight, 4),
                'asset_class': self._get_asset_class(ticker),
                'sector': self._get_sector(ticker),
                'expense_ratio': round(random.uniform(0.03, 1.50), 2),  # 0.03% to 1.5%
                'purchase_date': f"20{random.randint(18, 24)}-{random.randint(1,12):02d}-01"
            })
        
        # Client profile
        age = metadata.get('age', random.randint(30, 65))
        time_horizon = max(65 - age, 5)  # Years to retirement
        
        return {
            'holdings': holdings,
            'total_value': total_value,
            'risk_tolerance': risk_tolerance,
            'risk_tolerance_label': self._risk_tolerance_label(risk_tolerance),
            'client_profile': {
                'age': age,
                'time_horizon_years': time_horizon,
                'investment_goal': random.choice(['retirement', 'growth', 'income', 'education']),
                'tax_bracket': random.choice([0.22, 0.24, 0.32, 0.35]),
                'esg_required': random.choice([True, False])
            },
            'market_conditions': {
                'sp500_pe_ratio': round(random.uniform(18, 25), 1),
                'treasury_10y': round(random.uniform(3.5, 5.5), 2),
                'vix': round(random.uniform(12, 25), 1)
            }
        }
    
    def _get_asset_class(self, ticker: str) -> str:
        """Determine asset class from ticker"""
        if ticker in ['BND', 'AGG', 'TLT']:
            return 'bonds'
        elif ticker == 'GLD':
            return 'commodities'
        elif ticker == 'VNQ':
            return 'real_estate'
        else:
            return 'equities'
    
    def _get_sector(self, ticker: str) -> str:
        """Determine sector from ticker"""
        sectors = {
            'AAPL': 'technology', 'MSFT': 'technology', 'GOOGL': 'technology',
            'AMZN': 'consumer', 'META': 'technology', 'TSLA': 'consumer',
            'NVDA': 'technology', 'JPM': 'financials', 'V': 'financials',
            'JNJ': 'healthcare', 'WMT': 'consumer', 'PG': 'consumer',
            'DIS': 'communication', 'NFLX': 'communication'
        }
        return sectors.get(ticker, 'diversified')
    
    def _risk_tolerance_label(self, score: int) -> str:
        """Convert numeric risk tolerance to label"""
        if score <= 3:
            return 'conservative'
        elif score <= 6:
            return 'moderate'
        else:
            return 'aggressive'
    
    # ===========================
    # FINSERV: PE EXIT TIMING
    # ===========================
    
    def generate_pe_exit_timing(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate synthetic PE portfolio company data for exit timing
        
        Creates company financials, market conditions, and exit scenarios.
        """
        company_name = metadata.get('company_name', f"Portfolio Co {random.randint(1, 20)}")
        current_ebitda = metadata.get('current_ebitda', random.randint(20, 100))  # $M
        sector = metadata.get('sector', random.choice(['software', 'healthcare', 'industrials', 'consumer']))
        
        logger.info(f"💼 Generating PE exit timing data: {company_name}, EBITDA ${current_ebitda}M")
        
        # Company financials (historical + projected)
        years_held = random.randint(2, 5)
        entry_ebitda = round(current_ebitda / (1 + random.uniform(0.15, 0.40)) ** years_held, 1)
        
        financials = {
            'current': {
                'revenue': round(current_ebitda * random.uniform(4, 8), 1),
                'ebitda': current_ebitda,
                'ebitda_margin': round(random.uniform(0.15, 0.35), 2),
                'growth_rate': round(random.uniform(0.15, 0.40), 2)
            },
            'historical': [
                {
                    'year': f"Y-{i}",
                    'revenue': round(current_ebitda * random.uniform(3, 7) / (1.2 ** i), 1),
                    'ebitda': round(current_ebitda / (1.2 ** i), 1)
                }
                for i in range(years_held, 0, -1)
            ],
            'projections': [
                {
                    'quarter': f"Q{q}",
                    'year': '2025',
                    'ebitda': round(current_ebitda * (1 + 0.1 * q/4), 1)
                }
                for q in range(1, 5)
            ]
        }
        
        # Deal information
        entry_multiple = round(random.uniform(8, 12), 1)
        purchase_price = round(entry_ebitda * entry_multiple, 1)
        
        deal_info = {
            'acquisition_date': f"20{random.randint(19, 22)}-{random.randint(1,12):02d}-01",
            'purchase_price': purchase_price,
            'entry_multiple': entry_multiple,
            'ownership_pct': round(random.uniform(60, 100), 1),
            'debt_at_entry': round(purchase_price * random.uniform(0.4, 0.6), 1)
        }
        
        # Fund context
        fund_vintage = 2018 + random.randint(0, 5)
        
        fund_context = {
            'fund_name': f"Fund {random.choice(['IV', 'V', 'VI', 'VII'])}",
            'vintage_year': fund_vintage,
            'fund_end_date': f"{fund_vintage + 10}-12-31",
            'target_irr': round(random.uniform(0.20, 0.30), 2),
            'deployed_capital_pct': round(random.uniform(0.70, 0.95), 2)
        }
        
        # Market conditions
        sector_multiples = {
            'software': (12, 18),
            'healthcare': (10, 14),
            'industrials': (8, 12),
            'consumer': (9, 13)
        }
        
        min_mult, max_mult = sector_multiples.get(sector, (9, 13))
        current_market_multiple = round(random.uniform(min_mult, max_mult), 1)
        
        market_conditions = {
            'sector': sector,
            'current_public_comps_multiple': current_market_multiple,
            'ipo_window': random.choice(['open', 'moderate', 'closed']),
            'm&a_activity': random.choice(['high', 'moderate', 'low']),
            'interest_rates': round(random.uniform(4.0, 6.0), 2),
            'gdp_growth': round(random.uniform(1.5, 3.5), 1),
            'sector_sentiment': random.choice(['bullish', 'neutral', 'bearish'])
        }
        
        # Exit scenarios (Q1-Q4 of next 2 years)
        scenarios = []
        for year_offset in [0, 1]:
            for quarter in range(1, 5):
                projected_ebitda = current_ebitda * (1 + 0.10 * (year_offset + quarter/4))
                scenario_multiple = current_market_multiple * random.uniform(0.9, 1.1)
                exit_value = projected_ebitda * scenario_multiple
                
                scenarios.append({
                    'quarter': f"Q{quarter} {2025 + year_offset}",
                    'projected_ebitda': round(projected_ebitda, 1),
                    'estimated_multiple': round(scenario_multiple, 1),
                    'exit_value': round(exit_value, 1),
                    'holding_costs': round(random.uniform(1, 3), 1),
                    'tax_rate': 0.20 if years_held + year_offset >= 1 else 0.37
                })
        
        return {
            'company_name': company_name,
            'sector': sector,
            'financials': financials,
            'deal_info': deal_info,
            'fund_context': fund_context,
            'market_conditions': market_conditions,
            'exit_scenarios': scenarios,
            'years_held': years_held
        }
    
    # ===========================
    # FINSERV: HF REBALANCING
    # ===========================
    
    def generate_hf_rebalancing(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate synthetic hedge fund portfolio for rebalancing optimization
        
        Creates multi-factor portfolio with transaction costs and target exposures.
        """
        num_positions = metadata.get('num_positions', random.randint(50, 200))
        total_aum = metadata.get('total_aum', random.randint(100, 1000))  # $M
        
        logger.info(f"📈 Generating HF rebalancing data: {num_positions} positions, ${total_aum}M AUM")
        
        # Generate portfolio positions
        tickers = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'JPM', 'BAC', 'WFC',
            'V', 'MA', 'JNJ', 'PFE', 'UNH', 'XOM', 'CVX', 'COP', 'WMT', 'HD',
            'PG', 'KO', 'PEP', 'DIS', 'NFLX', 'CMCSA', 'T', 'VZ', 'INTC', 'AMD',
            'CSCO', 'ORCL', 'CRM', 'ADBE', 'NOW', 'UBER', 'ABNB', 'COIN', 'SQ', 'SHOP'
        ]
        
        # Extend with more tickers if needed
        while len(tickers) < num_positions:
            tickers.append(f"STOCK{len(tickers)}")
        
        selected_tickers = random.sample(tickers, num_positions)
        
        # Generate current positions
        positions = []
        total_value = total_aum * 1_000_000
        
        # Create random weights
        weights = [random.random() ** 2 for _ in range(num_positions)]  # Skew towards smaller positions
        total_weight = sum(weights)
        weights = [w/total_weight for w in weights]
        
        for ticker, weight in zip(selected_tickers, weights):
            value = total_value * weight
            price = random.uniform(50, 500)
            shares = int(value / price)
            
            # Factor loadings (value, momentum, quality, size)
            positions.append({
                'ticker': ticker,
                'shares': shares,
                'price': round(price, 2),
                'value': round(value, 2),
                'weight': round(weight, 4),
                'sector': random.choice(['tech', 'financials', 'healthcare', 'energy', 'consumer']),
                'factor_loadings': {
                    'value': round(random.uniform(-1, 1), 2),
                    'momentum': round(random.uniform(-1, 1), 2),
                    'quality': round(random.uniform(-1, 1), 2),
                    'size': round(random.uniform(-1, 1), 2)
                },
                'volatility': round(random.uniform(0.15, 0.45), 2),
                'avg_daily_volume': random.randint(1_000_000, 50_000_000),
                'bid_ask_spread_bps': round(random.uniform(2, 20), 1)
            })
        
        # Calculate current factor exposures
        current_exposures = {
            'value': sum(p['weight'] * p['factor_loadings']['value'] for p in positions),
            'momentum': sum(p['weight'] * p['factor_loadings']['momentum'] for p in positions),
            'quality': sum(p['weight'] * p['factor_loadings']['quality'] for p in positions),
            'size': sum(p['weight'] * p['factor_loadings']['size'] for p in positions)
        }
        
        # Target exposures (intentionally different to create rebalancing opportunity)
        target_exposures = {
            'value': round(current_exposures['value'] + random.uniform(-0.10, 0.10), 2),
            'momentum': round(current_exposures['momentum'] + random.uniform(-0.10, 0.10), 2),
            'quality': round(current_exposures['quality'] + random.uniform(-0.10, 0.10), 2),
            'size': round(current_exposures['size'] + random.uniform(-0.10, 0.10), 2)
        }
        
        # Risk constraints
        constraints = {
            'max_portfolio_volatility': round(random.uniform(0.12, 0.18), 2),
            'max_turnover': round(random.uniform(0.15, 0.25), 2),
            'max_single_stock_weight': 0.05,
            'factor_tolerance': 0.05  # ±5%
        }
        
        # Transaction cost parameters
        transaction_costs = {
            'commission_bps': round(random.uniform(0.5, 2.0), 1),
            'market_impact_factor': round(random.uniform(0.1, 0.3), 2),
            'avg_spread_bps': round(sum(p['bid_ask_spread_bps'] * p['weight'] for p in positions), 1)
        }
        
        return {
            'portfolio_aum': total_aum,
            'num_positions': num_positions,
            'positions': positions,
            'current_factor_exposures': current_exposures,
            'target_factor_exposures': target_exposures,
            'constraints': constraints,
            'transaction_costs': transaction_costs,
            'market_conditions': {
                'volatility_regime': random.choice(['low', 'medium', 'high']),
                'liquidity_conditions': random.choice(['normal', 'stressed']),
                'factor_premia': {
                    'value': round(random.uniform(0.02, 0.06), 3),
                    'momentum': round(random.uniform(0.03, 0.08), 3),
                    'quality': round(random.uniform(0.02, 0.05), 3),
                    'size': round(random.uniform(0.01, 0.04), 3)
                }
            }
        }


# Global instance
synthetic_data_generator = SyntheticDataGenerator()

