#!/usr/bin/env python3
"""
Market Data Tool - Intelligent Data Augmentation
=================================================

This tool determines what external market data is needed based on:
1. User's intent (portfolio optimization, trading, etc.)
2. Model requirements (what variables need data)
3. Data quality (missing values, confidence)
4. Cost/benefit (API costs vs. model improvement)

Flow:
  User Prompt → Intent → Data Analysis → Market Data Tool → Augmented Data → Model Builder

Key Features:
- Identifies "must-have" vs "nice-to-have" data
- Fetches from external APIs (Polygon, FRED)
- Augments user-provided data
- Tracks data provenance (user vs external)
- Cost-aware (minimizes API calls)
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from anthropic import Anthropic
import os
import json

from .market_data_adapter import MarketDataAdapter

logger = logging.getLogger(__name__)


class MarketDataTool:
    """
    Intelligent market data augmentation tool
    """
    
    def __init__(self):
        self.adapter = MarketDataAdapter()
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    
    async def augment_with_market_data(
        self,
        problem_description: str,
        intent_data: Dict[str, Any],
        user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main entry point: Determine what data is needed and fetch it
        
        Args:
            problem_description: Original user prompt
            intent_data: Output from intent classification
            user_data: Data provided/parsed from user
            
        Returns:
            Dictionary with:
            - data_requirements: What data is needed (must-have, nice-to-have)
            - augmented_data: User data + external data
            - data_provenance: Where each piece of data came from
            - api_costs: Estimated API costs incurred
        """
        logger.info("🔍 Market Data Tool: Analyzing data requirements...")
        
        # Step 1: Determine what data is needed
        data_requirements = await self._determine_data_requirements(
            problem_description,
            intent_data,
            user_data
        )
        
        # Step 2: Fetch required external data
        external_data = await self._fetch_external_data(data_requirements)
        
        # Step 3: Merge user + external data
        augmented_data = self._merge_data(user_data, external_data)
        
        # Step 4: Create provenance trail
        provenance = self._create_provenance(user_data, external_data, data_requirements)
        
        return {
            "status": "success",
            "data_requirements": data_requirements,
            "augmented_data": augmented_data,
            "data_provenance": provenance,
            "api_costs": self._estimate_api_costs(data_requirements, external_data)
        }
    
    
    async def _determine_data_requirements(
        self,
        problem_description: str,
        intent_data: Dict[str, Any],
        user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use LLM to determine what external data is needed
        
        Returns:
            {
                "must_have": [{"type": "stock_prices", "tickers": ["AAPL", "MSFT"], "reason": "..."}],
                "nice_to_have": [{"type": "economic_indicators", "reason": "..."}],
                "skip": [{"type": "news_sentiment", "reason": "not critical for MVP"}]
            }
        """
        
        domain_id = intent_data.get("domain_id", "unknown")
        
        # Domain-specific data requirements (knowledge base)
        domain_requirements = self._get_domain_requirements(domain_id)
        
        # Use LLM to analyze user data and determine gaps
        prompt = f"""You are a financial data analyst for an optimization platform.

**User's Problem:**
{problem_description}

**Problem Domain:** {domain_id}
**User-Provided Data:**
{json.dumps(user_data, indent=2)}

**Task:** Determine what external market data is needed to build a high-quality optimization model.

**Domain Knowledge:**
{json.dumps(domain_requirements, indent=2)}

**Output Format (JSON only):**
{{
  "must_have": [
    {{
      "data_type": "stock_prices|economic_indicators|correlations|volatility",
      "entities": ["AAPL", "MSFT"] or ["GDP", "unemployment"],
      "reason": "Why this data is CRITICAL for optimization",
      "api_source": "polygon|fred",
      "estimated_cost": 0.01
    }}
  ],
  "nice_to_have": [
    {{
      "data_type": "...",
      "entities": [...],
      "reason": "Why this would IMPROVE model but not required",
      "api_source": "...",
      "estimated_cost": 0.0
    }}
  ],
  "skip": [
    {{
      "data_type": "...",
      "reason": "Why we don't need this (user provided, not relevant, too expensive)"
    }}
  ],
  "data_gaps": [
    {{
      "gap": "User didn't provide risk tolerance",
      "impact": "high|medium|low",
      "mitigation": "Use default conservative value or ask user"
    }}
  ]
}}

**Guidelines:**
1. If user provided tickers but no prices → MUST fetch prices
2. If portfolio optimization → MUST fetch correlations & volatility
3. If trading optimization → MUST fetch historical prices
4. Economic indicators are NICE-TO-HAVE for context (always free via FRED)
5. Minimize API calls to reduce costs
6. Only request data that will MATERIALLY improve the optimization

Return ONLY valid JSON, no other text."""

        try:
            response = self.anthropic.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=2048,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text.strip()
            
            # Parse JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            requirements = json.loads(response_text)
            
            logger.info(f"✅ Data requirements determined: {len(requirements.get('must_have', []))} must-have, {len(requirements.get('nice_to_have', []))} nice-to-have")
            return requirements
            
        except Exception as e:
            logger.error(f"❌ Error determining data requirements: {e}")
            # Fallback to domain defaults
            return domain_requirements
    
    
    def _get_domain_requirements(self, domain_id: str) -> Dict[str, Any]:
        """
        Domain-specific data requirements (knowledge base)
        """
        domain_configs = {
            "portfolio": {
                "must_have": [
                    {
                        "data_type": "stock_prices",
                        "reason": "Current prices needed for valuation",
                        "api_source": "polygon"
                    },
                    {
                        "data_type": "volatility",
                        "reason": "Risk metrics for optimization",
                        "api_source": "polygon"
                    }
                ],
                "nice_to_have": [
                    {
                        "data_type": "economic_indicators",
                        "reason": "Macro context for risk assessment",
                        "api_source": "fred"
                    },
                    {
                        "data_type": "correlations",
                        "reason": "Diversification analysis",
                        "api_source": "polygon"
                    }
                ]
            },
            "trading": {
                "must_have": [
                    {
                        "data_type": "stock_prices",
                        "reason": "Historical prices for strategy backtesting",
                        "api_source": "polygon"
                    }
                ],
                "nice_to_have": [
                    {
                        "data_type": "volume",
                        "reason": "Liquidity analysis",
                        "api_source": "polygon"
                    }
                ]
            },
            "retail_layout": {
                "must_have": [],
                "nice_to_have": []
            },
            "vrp": {
                "must_have": [],
                "nice_to_have": []
            }
        }
        
        return domain_configs.get(domain_id, {"must_have": [], "nice_to_have": []})
    
    
    async def _fetch_external_data(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch data from external APIs based on requirements
        """
        external_data = {}
        
        # Combine must-have and nice-to-have (prioritize must-have)
        all_requirements = requirements.get("must_have", []) + requirements.get("nice_to_have", [])
        
        for req in all_requirements:
            data_type = req.get("data_type")
            entities = req.get("entities", [])
            api_source = req.get("api_source", "polygon")
            
            try:
                if data_type == "stock_prices" and entities:
                    logger.info(f"📊 Fetching stock prices for {entities} from {api_source}")
                    portfolio_data = self.adapter.get_portfolio_data(entities, days=90)
                    external_data["stock_prices"] = portfolio_data
                
                elif data_type == "economic_indicators":
                    logger.info(f"📊 Fetching economic indicators from FRED")
                    econ_data = self.adapter.get_economic_indicators()
                    external_data["economic_indicators"] = econ_data
                
                elif data_type == "correlations" and entities:
                    logger.info(f"📊 Calculating correlations for {entities}")
                    corr_data = self.adapter.get_correlation_matrix(entities, days=90)
                    external_data["correlations"] = corr_data
                
                elif data_type == "volatility":
                    # Volatility is included in stock_prices
                    pass
                
                else:
                    logger.warning(f"⚠️  Unknown data type: {data_type}")
            
            except Exception as e:
                logger.error(f"❌ Error fetching {data_type}: {e}")
                continue
        
        logger.info(f"✅ Fetched {len(external_data)} data types from external APIs")
        return external_data
    
    
    def _merge_data(self, user_data: Dict[str, Any], external_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge user-provided and external data
        """
        merged = user_data.copy()
        
        # Add external data with clear provenance
        if "stock_prices" in external_data:
            merged["market_data"] = external_data["stock_prices"]
        
        if "economic_indicators" in external_data:
            merged["macro_context"] = external_data["economic_indicators"]
        
        if "correlations" in external_data:
            merged["correlations"] = external_data["correlations"]
        
        return merged
    
    
    def _create_provenance(
        self,
        user_data: Dict[str, Any],
        external_data: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create detailed data provenance trail
        """
        return {
            "user_provided": {
                "fields": list(user_data.keys()),
                "count": len(user_data),
                "quality": "direct_input"
            },
            "external_augmentation": {
                "sources": {
                    "polygon.io": "stock_prices" in external_data,
                    "fred": "economic_indicators" in external_data
                },
                "data_types": list(external_data.keys()),
                "count": len(external_data),
                "timestamp": external_data.get("economic_indicators", {}).get("timestamp", "N/A")
            },
            "requirements_summary": {
                "must_have_count": len(requirements.get("must_have", [])),
                "nice_to_have_count": len(requirements.get("nice_to_have", [])),
                "data_gaps": requirements.get("data_gaps", [])
            },
            "data_quality": {
                "completeness": self._calculate_completeness(requirements, external_data),
                "freshness": "real-time" if external_data else "N/A",
                "confidence": "high" if external_data else "medium"
            }
        }
    
    
    def _calculate_completeness(self, requirements: Dict, external_data: Dict) -> str:
        """
        Calculate what % of required data was fetched
        """
        must_have = requirements.get("must_have", [])
        if not must_have:
            return "100% (no external data required)"
        
        fetched = len(external_data)
        required = len(must_have)
        
        if fetched >= required:
            return "100% (all required data fetched)"
        elif fetched > 0:
            pct = (fetched / required) * 100
            return f"{pct:.0f}% (partial data)"
        else:
            return "0% (no external data fetched)"
    
    
    def _estimate_api_costs(self, requirements: Dict, external_data: Dict) -> Dict[str, Any]:
        """
        Estimate API costs incurred
        """
        # Polygon.io pricing: ~$0.0003 per API call (at $29/mo for 100 calls/min)
        # FRED: Free
        
        polygon_calls = 0
        if "stock_prices" in external_data:
            tickers = len(external_data["stock_prices"])
            polygon_calls += tickers  # 1 call per ticker
        
        if "correlations" in external_data:
            polygon_calls += len(requirements.get("must_have", []))  # Additional calls for correlations
        
        fred_calls = 1 if "economic_indicators" in external_data else 0
        
        return {
            "polygon_calls": polygon_calls,
            "polygon_cost_usd": round(polygon_calls * 0.0003, 4),
            "fred_calls": fred_calls,
            "fred_cost_usd": 0.0,  # Free
            "total_cost_usd": round(polygon_calls * 0.0003, 4),
            "cost_per_optimization": f"${round(polygon_calls * 0.0003, 4)}"
        }


# ===========================
# CONVENIENCE FUNCTION
# ===========================

async def augment_with_market_data(
    problem_description: str,
    intent_data: Dict[str, Any],
    user_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Convenience function to augment data with market data
    
    This is the main entry point for the data augmentation flow.
    """
    tool = MarketDataTool()
    return await tool.augment_with_market_data(
        problem_description,
        intent_data,
        user_data
    )

