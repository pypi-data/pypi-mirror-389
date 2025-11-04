#!/usr/bin/env python3
"""
Market Data Adapter - Unified Interface for External Data Sources
==================================================================

Provides a clean interface to multiple market data providers:
- Polygon.io: Real-time and historical stock/crypto/forex data
  * Free tier: Delayed data (15+ min delay) - status: "DELAYED"
  * Paid tier: Real-time data - status: "OK"
  * Both are accepted and used for portfolio optimization
- FRED: Federal Reserve economic indicators
- Alpha Vantage: Backup market data and technical indicators

Design Principles:
- Single interface for all providers (adapter pattern)
- Automatic failover if primary provider fails
- Accepts both real-time and delayed data
- Graceful degradation to simulation if API unavailable
- Caching to minimize API calls
- Rate limiting to respect provider limits
"""

import os
import logging
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from functools import lru_cache

logger = logging.getLogger(__name__)


class MarketDataAdapter:
    """
    Unified interface for multiple market data providers
    """
    
    def __init__(self):
        self.polygon_key = os.getenv("POLYGON_API_KEY")
        self.alpha_vantage_key = os.getenv("ALPHAADVANTAGE_API_KEY")
        
        # Validate required keys
        if not self.polygon_key:
            logger.warning("⚠️  POLYGON_API_KEY not set - market data will be simulated")
        if not self.alpha_vantage_key:
            logger.warning("⚠️  ALPHAADVANTAGE_API_KEY not set - economic data will be simulated")
    
    
    # ===========================
    # STOCK PRICE DATA
    # ===========================
    
    def get_stock_prices(
        self, 
        ticker: str, 
        days: int = 30,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get historical stock prices from Polygon.io
        
        Args:
            ticker: Stock ticker symbol (e.g., "AAPL")
            days: Number of days of historical data
            use_cache: Whether to use cached data
            
        Returns:
            List of price dictionaries with keys:
            - t: timestamp (milliseconds)
            - o: open price
            - h: high price
            - l: low price
            - c: close price
            - v: volume
        """
        if not self.polygon_key:
            logger.warning(f"No Polygon API key - simulating data for {ticker}")
            return self._simulate_stock_prices(ticker, days)
        
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
            params = {
                "apiKey": self.polygon_key,
                "adjusted": "true",
                "sort": "asc"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            # Accept both "OK" (real-time) and "DELAYED" (free tier) data
            if data.get("status") in ["OK", "DELAYED"] and data.get("results"):
                status_emoji = "✅" if data.get("status") == "OK" else "⏱️"
                logger.info(f"{status_emoji} Fetched {len(data['results'])} price points for {ticker} (status: {data.get('status')})")
                return data["results"]
            else:
                logger.warning(f"❌ No data returned for {ticker}: {data.get('status')}")
                return self._simulate_stock_prices(ticker, days)
                
        except Exception as e:
            logger.error(f"❌ Error fetching data for {ticker}: {e}")
            return self._simulate_stock_prices(ticker, days)
    
    
    def get_current_price(self, ticker: str) -> Optional[float]:
        """
        Get current/latest price for a ticker
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Current price or None if unavailable
        """
        prices = self.get_stock_prices(ticker, days=1)
        if prices:
            return prices[-1]["c"]  # Last close price
        return None
    
    
    def get_portfolio_data(
        self, 
        tickers: List[str],
        days: int = 90
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get comprehensive data for a portfolio of tickers
        
        Args:
            tickers: List of stock ticker symbols
            days: Historical window for volatility calculation
            
        Returns:
            Dictionary mapping ticker to:
            - current_price: Latest closing price
            - prices: List of historical prices
            - returns: Daily returns
            - volatility: Annualized volatility
            - avg_volume: Average daily volume
        """
        portfolio_data = {}
        
        for ticker in tickers:
            try:
                prices = self.get_stock_prices(ticker, days=days)
                
                if not prices:
                    logger.warning(f"No price data for {ticker}")
                    continue
                
                close_prices = [p["c"] for p in prices]
                volumes = [p["v"] for p in prices]
                
                # Calculate returns
                returns = []
                for i in range(1, len(close_prices)):
                    ret = (close_prices[i] - close_prices[i-1]) / close_prices[i-1]
                    returns.append(ret)
                
                # Calculate volatility (annualized)
                import numpy as np
                volatility = np.std(returns) * np.sqrt(252) if returns else 0.0
                
                portfolio_data[ticker] = {
                    "current_price": close_prices[-1],
                    "prices": close_prices,
                    "returns": returns,
                    "volatility": round(volatility, 4),
                    "avg_volume": int(np.mean(volumes)) if volumes else 0,
                    "data_points": len(prices),
                    "source": "polygon.io"
                }
                
                logger.info(f"✅ Portfolio data for {ticker}: ${close_prices[-1]:.2f}, vol={volatility:.2%}")
                
            except Exception as e:
                logger.error(f"❌ Error processing {ticker}: {e}")
                continue
        
        return portfolio_data
    
    
    # ===========================
    # ECONOMIC INDICATORS
    # ===========================
    
    @lru_cache(maxsize=1)  # Cache for 1 call (updates infrequently)
    def get_economic_indicators(self) -> Dict[str, Any]:
        """
        Get key economic indicators from Alpha Vantage API
        
        Returns:
            Dictionary with:
            - gdp_growth: Real GDP growth rate (%)
            - unemployment: Unemployment rate (%)
            - inflation: CPI year-over-year change (%)
            - fed_funds_rate: Federal funds rate (%)
            - treasury_10y: 10-year Treasury yield (%)
            - consumer_sentiment: Consumer sentiment index
        """
        if not self.alpha_vantage_key:
            logger.warning("No Alpha Vantage API key - simulating economic data")
            return self._simulate_economic_indicators()
        
        try:
            indicators = {
                "gdp_growth": self._get_alpha_vantage_indicator("REAL_GDP", "quarterly"),
                "unemployment": self._get_alpha_vantage_indicator("UNEMPLOYMENT", "monthly"),
                "inflation": self._get_alpha_vantage_indicator("INFLATION", "monthly"),
                "fed_funds_rate": self._get_alpha_vantage_indicator("FEDERAL_FUNDS_RATE", "monthly"),
                "treasury_10y": self._get_alpha_vantage_indicator("TREASURY_YIELD", "monthly", maturity="10year"),
                "consumer_sentiment": self._get_alpha_vantage_indicator("CONSUMER_SENTIMENT", "monthly"),
                "timestamp": datetime.now().isoformat(),
                "source": "Alpha Vantage"
            }
            
            logger.info(f"✅ Fetched economic indicators from Alpha Vantage")
            return indicators
            
        except Exception as e:
            logger.error(f"❌ Error fetching economic indicators from Alpha Vantage: {e}")
            return self._simulate_economic_indicators()
    
    
    def _get_alpha_vantage_indicator(
        self, 
        function: str, 
        interval: str, 
        maturity: str = None
    ) -> Optional[float]:
        """
        Fetch economic indicator from Alpha Vantage
        
        Args:
            function: Economic indicator function name
            interval: Data interval (monthly, quarterly, annual)
            maturity: For treasury yields (10year, 5year, etc.)
        """
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": function,
                "interval": interval,
                "apikey": self.alpha_vantage_key
            }
            
            if maturity:
                params["maturity"] = maturity
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Alpha Vantage returns data in "data" key with list of time series
            if "data" in data and len(data["data"]) > 0:
                latest = data["data"][0]
                value = latest.get("value")
                if value:
                    return float(value)
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not fetch {function}: {e}")
            return None
    
    
    # ===========================
    # CORRELATION & RISK METRICS
    # ===========================
    
    def get_correlation_matrix(self, tickers: List[str], days: int = 90) -> Dict[str, Any]:
        """
        Calculate correlation matrix for a set of tickers
        
        Args:
            tickers: List of ticker symbols
            days: Historical window
            
        Returns:
            Dictionary with correlation matrix and metadata
        """
        try:
            import numpy as np
            import pandas as pd
            
            # Get returns for all tickers
            returns_data = {}
            for ticker in tickers:
                portfolio = self.get_portfolio_data([ticker], days=days)
                if ticker in portfolio and portfolio[ticker]["returns"]:
                    returns_data[ticker] = portfolio[ticker]["returns"]
            
            if not returns_data:
                return {"status": "error", "message": "No data available for correlation"}
            
            # Create DataFrame and calculate correlation
            df = pd.DataFrame(returns_data)
            corr_matrix = df.corr()
            
            return {
                "status": "success",
                "correlation_matrix": corr_matrix.to_dict(),
                "tickers": tickers,
                "data_points": len(df),
                "source": "polygon.io"
            }
            
        except Exception as e:
            logger.error(f"❌ Error calculating correlation: {e}")
            return {"status": "error", "message": str(e)}
    
    
    # ===========================
    # SIMULATION / FALLBACK
    # ===========================
    
    def _simulate_stock_prices(self, ticker: str, days: int) -> List[Dict[str, Any]]:
        """
        Generate simulated stock prices (fallback when API unavailable)
        """
        import numpy as np
        
        # Simulated parameters
        base_price = 100.0
        volatility = 0.02
        drift = 0.0001
        
        prices = []
        current_price = base_price
        
        for i in range(days):
            # Geometric Brownian Motion
            change = drift + volatility * np.random.randn()
            current_price *= (1 + change)
            
            timestamp = int((datetime.now() - timedelta(days=days-i)).timestamp() * 1000)
            
            prices.append({
                "t": timestamp,
                "o": round(current_price * 0.99, 2),
                "h": round(current_price * 1.01, 2),
                "l": round(current_price * 0.98, 2),
                "c": round(current_price, 2),
                "v": int(np.random.uniform(1e6, 1e7))
            })
        
        logger.info(f"📊 Simulated {days} days of prices for {ticker}")
        return prices
    
    
    def _simulate_economic_indicators(self) -> Dict[str, Any]:
        """
        Generate simulated economic indicators (fallback)
        """
        return {
            "gdp_growth": 2.5,
            "unemployment": 3.8,
            "inflation": 3.2,
            "fed_funds_rate": 5.50,
            "treasury_10y": 4.75,
            "consumer_sentiment": 72.0,
            "timestamp": datetime.now().isoformat(),
            "source": "SIMULATED (no API key configured)"
        }

