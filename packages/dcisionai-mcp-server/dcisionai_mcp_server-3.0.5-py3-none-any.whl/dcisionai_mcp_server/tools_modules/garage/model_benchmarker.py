#!/usr/bin/env python3
"""
Model Benchmarking Tool for DcisionAI
Compares different LLM models across various metrics without breaking core platform flow
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import statistics
from openai import OpenAI
from anthropic import Anthropic

logger = logging.getLogger(__name__)

@dataclass
class BenchmarkMetrics:
    """Metrics collected for each model benchmark"""
    model_name: str
    accuracy_score: float
    edit_distance: float
    cost_per_query: float
    latency_seconds: float
    token_count: int
    success_rate: float
    error_count: int
    timestamp: str

@dataclass
class BenchmarkResult:
    """Complete benchmark result for a model"""
    model_name: str
    total_queries: int
    successful_queries: int
    failed_queries: int
    avg_accuracy: float
    avg_edit_distance: float
    avg_cost_per_query: float
    avg_latency: float
    total_cost: float
    total_tokens: int
    metrics: List[BenchmarkMetrics]

class ModelBenchmarker:
    """Benchmarking tool for comparing different LLM models"""
    
    def __init__(self):
        # Initialize clients with proper API key loading
        try:
            import os
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
                logger.info("✅ OpenAI client initialized for benchmarking")
            else:
                logger.warning("⚠️ OPENAI_API_KEY not found in environment")
                self.openai_client = None
        except Exception as e:
            logger.warning(f"⚠️ OpenAI client not available: {e}")
            self.openai_client = None
        
        try:
            import os
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                self.anthropic_client = Anthropic(api_key=api_key)
                logger.info("✅ Anthropic client initialized for benchmarking")
            else:
                logger.warning("⚠️ ANTHROPIC_API_KEY not found in environment")
                self.anthropic_client = None
        except Exception as e:
            logger.warning(f"⚠️ Anthropic client not available: {e}")
            self.anthropic_client = None
        
        # Model configurations
        self.model_configs = {
            "fine-tuned": {
                "provider": "openai",
                "model": "ft:gpt-4o-2024-08-06:dcisionai:dcisionai-model:CV0blOhg",
                "cost_per_1k_tokens": 0.03,  # Fine-tuned pricing
                "max_tokens": 4000
            },
            "gpt-4o": {
                "provider": "openai", 
                "model": "gpt-4o",
                "cost_per_1k_tokens": 0.06,  # GPT-4o pricing
                "max_tokens": 4000
            },
            "gpt-4o-mini": {
                "provider": "openai",
                "model": "gpt-4o-mini", 
                "cost_per_1k_tokens": 0.00015,  # GPT-4o-mini pricing
                "max_tokens": 4000
            },
            "claude-3-5-sonnet": {
                "provider": "anthropic",
                "model": "claude-3-5-sonnet-20241022",
                "cost_per_1k_tokens": 0.015,  # Claude pricing
                "max_tokens": 4000
            },
            "claude-3-haiku": {
                "provider": "anthropic",
                "model": "claude-3-haiku-20240307",
                "cost_per_1k_tokens": 0.00025,  # Claude Haiku pricing
                "max_tokens": 4000
            }
        }
        
        # Benchmark test cases
        self.test_cases = [
            {
                "name": "Manufacturing Production Scheduling",
                "query": "Our manufacturing plant produces 200 units daily across 4 production lines. We're experiencing 15% downtime and 20% overtime costs. We need to optimize our production scheduling and resource allocation to improve efficiency.",
                "expected_intent": "manufacturing_production_scheduling",
                "expected_industry": "MANUFACTURING"
            },
            {
                "name": "Retail Promotional Planning", 
                "query": "Optimize our Black Friday campaign to maximize revenue while managing inventory constraints and competitor responses.",
                "expected_intent": "retail_promotional_planning",
                "expected_industry": "RETAIL"
            },
            {
                "name": "Supply Chain Optimization",
                "query": "We need to optimize our supply chain network with 5 warehouses, 20 suppliers, and 100 retail locations to minimize costs while meeting service level agreements.",
                "expected_intent": "supply_chain_optimization", 
                "expected_industry": "MANUFACTURING"
            },
            {
                "name": "Portfolio Optimization",
                "query": "Optimize our investment portfolio allocation across stocks, bonds, and alternative investments to maximize returns while managing risk within our constraints.",
                "expected_intent": "portfolio_optimization",
                "expected_industry": "FINANCE"
            },
            {
                "name": "Inventory Management",
                "query": "We have 50 SKUs across 3 warehouses with seasonal demand patterns. Optimize our inventory levels to minimize holding costs while maintaining 95% service levels.",
                "expected_intent": "inventory_management",
                "expected_industry": "RETAIL"
            }
        ]

    async def benchmark_model(self, model_name: str, test_cases: Optional[List[Dict]] = None) -> BenchmarkResult:
        """Benchmark a specific model against test cases"""
        if model_name not in self.model_configs:
            raise ValueError(f"Unknown model: {model_name}")
        
        config = self.model_configs[model_name]
        test_cases = test_cases or self.test_cases
        
        logger.info(f"🔍 Starting benchmark for {model_name}")
        
        metrics = []
        total_cost = 0
        total_tokens = 0
        successful_queries = 0
        failed_queries = 0
        
        for i, test_case in enumerate(test_cases):
            logger.info(f"📊 Running test case {i+1}/{len(test_cases)}: {test_case['name']}")
            
            try:
                # Run the benchmark for this test case
                metric = await self._run_single_benchmark(
                    model_name, config, test_case
                )
                metrics.append(metric)
                
                total_cost += metric.cost_per_query
                total_tokens += metric.token_count
                
                if metric.success_rate > 0:
                    successful_queries += 1
                else:
                    failed_queries += 1
                    
            except Exception as e:
                logger.error(f"❌ Benchmark failed for {model_name} on test case {test_case['name']}: {e}")
                failed_queries += 1
                
                # Create a failed metric
                failed_metric = BenchmarkMetrics(
                    model_name=model_name,
                    accuracy_score=0.0,
                    edit_distance=10.0,  # High edit distance for failures
                    cost_per_query=0.0,
                    latency_seconds=0.0,
                    token_count=0,
                    success_rate=0.0,
                    error_count=1,
                    timestamp=datetime.now().isoformat()
                )
                metrics.append(failed_metric)
        
        # Calculate averages
        successful_metrics = [m for m in metrics if m.success_rate > 0]
        
        avg_accuracy = statistics.mean([m.accuracy_score for m in successful_metrics]) if successful_metrics else 0.0
        avg_edit_distance = statistics.mean([m.edit_distance for m in successful_metrics]) if successful_metrics else 10.0
        avg_latency = statistics.mean([m.latency_seconds for m in successful_metrics]) if successful_metrics else 0.0
        
        return BenchmarkResult(
            model_name=model_name,
            total_queries=len(test_cases),
            successful_queries=successful_queries,
            failed_queries=failed_queries,
            avg_accuracy=avg_accuracy,
            avg_edit_distance=avg_edit_distance,
            avg_cost_per_query=total_cost / len(test_cases) if test_cases else 0.0,
            avg_latency=avg_latency,
            total_cost=total_cost,
            total_tokens=total_tokens,
            metrics=metrics
        )

    async def _run_single_benchmark(self, model_name: str, config: Dict, test_case: Dict) -> BenchmarkMetrics:
        """Run a single benchmark test case"""
        start_time = time.time()
        
        # Create the prompt for intent classification
        prompt = f"""Classify this optimization problem and extract key information:

PROBLEM: {test_case['query']}

Provide a JSON response with:
{{
  "intent": "specific_intent_name",
  "industry": "MANUFACTURING|RETAIL|FINANCE",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}}"""

        try:
            # Create a simple prompt for direct model comparison
            prompt = f"""Classify this optimization problem:

PROBLEM: {test_case['query']}

Respond with JSON format:
{{
  "intent": "specific_intent_name",
  "industry": "MANUFACTURING|RETAIL|FINANCE|LOGISTICS",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}}"""

            # Call the appropriate model directly for true comparison
            if config["provider"] == "openai" and self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model=config["model"],
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=config["max_tokens"]
                )
                response_text = response.choices[0].message.content
                token_count = response.usage.total_tokens
                
            elif config["provider"] == "anthropic" and self.anthropic_client:
                response = self.anthropic_client.messages.create(
                    model=config["model"],
                    max_tokens=config["max_tokens"],
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = response.content[0].text
                token_count = response.usage.input_tokens + response.usage.output_tokens
                
            else:
                raise Exception(f"Provider {config['provider']} not available")
            
            latency = time.time() - start_time
            
            # Calculate cost
            cost_per_query = (token_count / 1000) * config["cost_per_1k_tokens"]
            
            # Parse response and calculate accuracy
            try:
                # Clean up markdown code blocks if present
                cleaned_response = response_text.strip()
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response[7:]  # Remove ```json
                if cleaned_response.endswith('```'):
                    cleaned_response = cleaned_response[:-3]  # Remove ```
                cleaned_response = cleaned_response.strip()
                
                result = json.loads(cleaned_response)
                accuracy_score = self._calculate_accuracy(result, test_case)
                edit_distance = self._calculate_edit_distance(result, test_case)
                success_rate = 1.0
                error_count = 0
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parsing failed for {model_name}: {e}")
                logger.warning(f"Response was: {response_text[:200]}...")
                # Failed to parse JSON
                accuracy_score = 0.0
                edit_distance = 10.0
                success_rate = 0.0
                error_count = 1
            
            return BenchmarkMetrics(
                model_name=model_name,
                accuracy_score=accuracy_score,
                edit_distance=edit_distance,
                cost_per_query=cost_per_query,
                latency_seconds=latency,
                token_count=token_count,
                success_rate=success_rate,
                error_count=error_count,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"❌ Model call failed for {model_name}: {e}")
            return BenchmarkMetrics(
                model_name=model_name,
                accuracy_score=0.0,
                edit_distance=10.0,
                cost_per_query=0.0,
                latency_seconds=time.time() - start_time,
                token_count=0,
                success_rate=0.0,
                error_count=1,
                timestamp=datetime.now().isoformat()
            )

    def _calculate_accuracy_from_tool_result(self, tool_result: Dict, test_case: Dict) -> float:
        """Calculate accuracy score from actual tool result"""
        expected_intent = test_case.get('expected_intent', '')
        expected_industry = test_case.get('expected_industry', '')
        
        actual_intent = tool_result.get('intent', '').lower()
        actual_industry = tool_result.get('industry', '').upper()
        
        # Check if intent matches (fuzzy matching)
        intent_match = 0.0
        if expected_intent.lower() in actual_intent or actual_intent in expected_intent.lower():
            intent_match = 1.0
        elif any(word in actual_intent for word in expected_intent.lower().split('_')):
            intent_match = 0.7  # Partial match
        
        # Check if industry matches
        industry_match = 1.0 if expected_industry.upper() in actual_industry or actual_industry in expected_industry.upper() else 0.0
        
        # Check confidence score
        confidence = tool_result.get('confidence', 0.0)
        confidence_score = min(confidence, 1.0)
        
        # Weighted average: 50% intent, 30% industry, 20% confidence
        return (intent_match * 0.5) + (industry_match * 0.3) + (confidence_score * 0.2)
    
    def _calculate_edit_distance_from_tool_result(self, tool_result: Dict, test_case: Dict) -> float:
        """Calculate edit distance from actual tool result"""
        # Simple heuristic based on confidence and match quality
        confidence = tool_result.get('confidence', 0.0)
        if confidence >= 0.8:
            return 2.0
        elif confidence >= 0.6:
            return 5.0
        elif confidence >= 0.4:
            return 8.0
        else:
            return 12.0

    def _calculate_accuracy(self, result: Dict, test_case: Dict) -> float:
        """Calculate accuracy score based on expected vs actual results"""
        expected_intent = test_case.get('expected_intent', '')
        expected_industry = test_case.get('expected_industry', '')
        
        actual_intent = result.get('intent', '').lower()
        actual_industry = result.get('industry', '').upper()
        
        # Check intent match (fuzzy matching for variations)
        intent_match = 0.0
        if expected_intent.lower() in actual_intent or actual_intent in expected_intent.lower():
            intent_match = 1.0
        elif any(word in actual_intent for word in expected_intent.lower().split('_')):
            intent_match = 0.7  # Partial match
        elif any(word in actual_intent for word in ['production', 'scheduling', 'inventory', 'portfolio', 'supply', 'chain', 'promotional', 'markdown']):
            intent_match = 0.5  # Related concepts
        
        # Check industry match
        industry_match = 1.0 if expected_industry.upper() in actual_industry or actual_industry in expected_industry.upper() else 0.0
        
        # Check confidence score
        confidence = result.get('confidence', 0.0)
        confidence_score = min(confidence, 1.0)
        
        # Weighted average: 50% intent, 30% industry, 20% confidence
        return (intent_match * 0.5) + (industry_match * 0.3) + (confidence_score * 0.2)

    def _calculate_edit_distance(self, result: Dict, test_case: Dict) -> float:
        """Calculate edit distance between expected and actual results"""
        # Simple edit distance calculation
        expected_intent = test_case.get("expected_intent", "")
        actual_intent = result.get("intent", "")
        
        if expected_intent == actual_intent:
            return 0.0
        
        # Calculate Levenshtein distance
        m, n = len(expected_intent), len(actual_intent)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
            
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if expected_intent[i-1] == actual_intent[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
        
        return dp[m][n]

    async def compare_models(self, model_names: List[str], test_cases: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Compare multiple models and generate comparison report"""
        logger.info(f"🔍 Starting comparison of models: {model_names}")
        
        results = {}
        
        # Run benchmarks for each model
        for model_name in model_names:
            try:
                result = await self.benchmark_model(model_name, test_cases)
                results[model_name] = result
                logger.info(f"✅ Completed benchmark for {model_name}")
            except Exception as e:
                logger.error(f"❌ Benchmark failed for {model_name}: {e}")
                results[model_name] = None
        
        # Generate comparison report
        comparison_report = self._generate_comparison_report(results)
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "models_compared": model_names,
            "results": {k: asdict(v) if v else None for k, v in results.items()},
            "comparison_report": comparison_report
        }

    def _generate_comparison_report(self, results: Dict[str, BenchmarkResult]) -> Dict[str, Any]:
        """Generate a comparison report from benchmark results"""
        valid_results = {k: v for k, v in results.items() if v is not None}
        
        if not valid_results:
            return {"error": "No valid results to compare"}
        
        # Create comparison table
        comparison_table = []
        
        for model_name, result in valid_results.items():
            comparison_table.append({
                "model": model_name,
                "accuracy": f"{result.avg_accuracy:.1%}",
                "edit_distance": f"{result.avg_edit_distance:.1f}",
                "cost_per_query": f"${result.avg_cost_per_query:.3f}",
                "latency": f"{result.avg_latency:.1f}s",
                "success_rate": f"{result.successful_queries}/{result.total_queries}",
                "total_cost": f"${result.total_cost:.3f}",
                "total_tokens": result.total_tokens
            })
        
        # Find best performing model in each category
        best_accuracy = max(valid_results.items(), key=lambda x: x[1].avg_accuracy)
        best_cost = min(valid_results.items(), key=lambda x: x[1].avg_cost_per_query)
        best_latency = min(valid_results.items(), key=lambda x: x[1].avg_latency)
        best_edit_distance = min(valid_results.items(), key=lambda x: x[1].avg_edit_distance)
        
        return {
            "comparison_table": comparison_table,
            "best_performers": {
                "accuracy": best_accuracy[0],
                "cost_efficiency": best_cost[0], 
                "speed": best_latency[0],
                "precision": best_edit_distance[0]
            },
            "summary": {
                "total_models_tested": len(valid_results),
                "total_test_cases": valid_results[list(valid_results.keys())[0]].total_queries,
                "overall_success_rate": sum(r.successful_queries for r in valid_results.values()) / 
                                      sum(r.total_queries for r in valid_results.values())
            }
        }

    async def benchmark_tool(self, tool_name: str, model_names: List[str], test_cases: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Benchmark specific tools across different models"""
        logger.info(f"🔍 Starting tool benchmark for {tool_name} with models: {model_names}")
        
        # This would integrate with the actual tool execution
        # For now, we'll use the intent classification as an example
        if tool_name == "classify_intent":
            return await self.compare_models(model_names, test_cases)
        else:
            return {
                "status": "error",
                "message": f"Tool {tool_name} benchmarking not yet implemented"
            }
