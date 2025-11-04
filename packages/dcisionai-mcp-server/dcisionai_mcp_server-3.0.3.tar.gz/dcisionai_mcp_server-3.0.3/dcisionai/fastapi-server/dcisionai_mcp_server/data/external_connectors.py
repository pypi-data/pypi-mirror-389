"""
External data connectors for optimization problems
Integrates with real-world data sources like Polygon, Alpha Vantage, etc.

Adapted from model-builder for DcisionAI platform integration
"""

import asyncio
import aiohttp
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import os
from enum import Enum

from .exceptions import DataIntegrationError, ExternalDataError


class DataSourceType(Enum):
    """Types of external data sources"""
    MARKET_DATA = "market_data"
    ECONOMIC_DATA = "economic_data"
    COMMODITY_DATA = "commodity_data"
    WEATHER_DATA = "weather_data"
    SUPPLY_CHAIN_DATA = "supply_chain_data"


@dataclass
class DataSourceConfig:
    """Configuration for external data source"""
    source_type: DataSourceType
    api_key: str
    base_url: str
    rate_limit: int = 5  # requests per second
    timeout: int = 30  # seconds
    retry_attempts: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_type": self.source_type.value,
            "base_url": self.base_url,
            "rate_limit": self.rate_limit,
            "timeout": self.timeout,
            "retry_attempts": self.retry_attempts
        }


@dataclass
class MarketDataRequest:
    """Request for market data"""
    symbols: List[str]
    start_date: datetime
    end_date: datetime
    frequency: str = "daily"  # daily, weekly, monthly
    data_types: List[str] = field(default_factory=lambda: ["price", "volume"])
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbols": self.symbols,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "frequency": self.frequency,
            "data_types": self.data_types
        }


@dataclass
class ExternalDataResult:
    """Result from external data source"""
    data: pd.DataFrame
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    quality_score: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "data": self.data.to_dict() if not self.data.empty else {},
            "metadata": self.metadata,
            "source": self.source,
            "quality_score": self.quality_score,
            "timestamp": self.timestamp.isoformat()
        }


class PolygonConnector:
    """Connector for Polygon.io market data API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.polygon.io"
        self.logger = logging.getLogger(__name__)
        self.session = None
        
        # Rate limiting
        self.rate_limit = 5  # requests per second for free tier
        self.last_request_time = 0
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _rate_limit(self):
        """Implement rate limiting"""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time
        min_interval = 1.0 / self.rate_limit
        
        if time_since_last < min_interval:
            await asyncio.sleep(min_interval - time_since_last)
        
        self.last_request_time = asyncio.get_event_loop().time()
    
    async def get_stock_data(self, symbols: List[str], 
                           start_date: datetime, 
                           end_date: datetime,
                           frequency: str = "daily") -> ExternalDataResult:
        """Get stock price data from Polygon"""
        
        try:
            all_data = []
            
            for symbol in symbols:
                await self._rate_limit()
                
                # Format dates for API
                start_str = start_date.strftime("%Y-%m-%d")
                end_str = end_date.strftime("%Y-%m-%d")
                
                # Determine timespan based on frequency
                timespan_map = {
                    "daily": "day",
                    "weekly": "week", 
                    "monthly": "month"
                }
                timespan = timespan_map.get(frequency, "day")
                
                url = f"{self.base_url}/v2/aggs/ticker/{symbol}/range/1/{timespan}/{start_str}/{end_str}"
                params = {
                    "adjusted": "true",
                    "sort": "asc",
                    "limit": 50000
                }
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if "results" in data and data["results"]:
                            for result in data["results"]:
                                all_data.append({
                                    "symbol": symbol,
                                    "date": pd.to_datetime(result["t"], unit="ms"),
                                    "open": result.get("o", 0),
                                    "high": result.get("h", 0),
                                    "low": result.get("l", 0),
                                    "close": result.get("c", 0),
                                    "volume": result.get("v", 0),
                                    "vwap": result.get("vw", 0),
                                    "transactions": result.get("n", 0)
                                })
                    else:
                        self.logger.warning(f"Failed to get data for {symbol}: {response.status}")
            
            if all_data:
                df = pd.DataFrame(all_data)
                df = df.sort_values(["symbol", "date"])
                
                # Calculate additional metrics
                df = self._calculate_financial_metrics(df)
                
                return ExternalDataResult(
                    data=df,
                    metadata={
                        "source": "polygon",
                        "symbols": symbols,
                        "frequency": frequency,
                        "data_points": len(df)
                    },
                    source="polygon",
                    quality_score=0.95  # High quality for Polygon data
                )
            else:
                return ExternalDataResult(
                    data=pd.DataFrame(),
                    metadata={"error": "No data retrieved"},
                    source="polygon",
                    quality_score=0.0
                )
                
        except Exception as e:
            self.logger.error(f"Polygon API error: {e}")
            raise DataIntegrationError(f"Failed to retrieve Polygon data: {e}")
    
    async def get_market_indices(self, start_date: datetime, end_date: datetime) -> ExternalDataResult:
        """Get major market indices data"""
        
        # Major market indices
        indices = ["SPY", "QQQ", "IWM", "VTI", "DIA"]  # ETFs representing major indices
        
        return await self.get_stock_data(indices, start_date, end_date)
    
    async def get_sector_data(self, start_date: datetime, end_date: datetime) -> ExternalDataResult:
        """Get sector ETF data for diversification analysis"""
        
        # Sector ETFs
        sectors = [
            "XLK",  # Technology
            "XLF",  # Financial
            "XLV",  # Healthcare
            "XLE",  # Energy
            "XLI",  # Industrial
            "XLP",  # Consumer Staples
            "XLY",  # Consumer Discretionary
            "XLB",  # Materials
            "XLU",  # Utilities
            "XLRE"  # Real Estate
        ]
        
        return await self.get_stock_data(sectors, start_date, end_date)
    
    def _calculate_financial_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate additional financial metrics"""
        
        # Calculate returns
        df = df.sort_values(["symbol", "date"])
        df["daily_return"] = df.groupby("symbol")["close"].pct_change()
        
        # Calculate volatility (rolling 30-day)
        df["volatility_30d"] = df.groupby("symbol")["daily_return"].rolling(30).std().reset_index(0, drop=True)
        
        # Calculate moving averages
        df["ma_20"] = df.groupby("symbol")["close"].rolling(20).mean().reset_index(0, drop=True)
        df["ma_50"] = df.groupby("symbol")["close"].rolling(50).mean().reset_index(0, drop=True)
        
        # Calculate RSI (Relative Strength Index) - skip if insufficient data
        try:
            df["rsi"] = df.groupby("symbol", group_keys=False)["close"].apply(lambda x: self._calculate_rsi_series(x)).reset_index(0, drop=True)
        except Exception:
            df["rsi"] = np.nan
        
        return df
    
    def _calculate_rsi(self, group: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate RSI for a group of data"""
        
        delta = group["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_rsi_series(self, close_prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI for a price series"""
        
        if len(close_prices) < period + 1:
            return pd.Series([np.nan] * len(close_prices), index=close_prices.index)
        
        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi


class AlphaVantageConnector:
    """Connector for Alpha Vantage API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.logger = logging.getLogger(__name__)
        self.session = None
        
        # Rate limiting (5 requests per minute for free tier)
        self.rate_limit = 5 / 60  # requests per second
        self.last_request_time = 0
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _rate_limit(self):
        """Implement rate limiting"""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time
        min_interval = 1.0 / self.rate_limit
        
        if time_since_last < min_interval:
            await asyncio.sleep(min_interval - time_since_last)
        
        self.last_request_time = asyncio.get_event_loop().time()
    
    async def get_economic_indicators(self) -> ExternalDataResult:
        """Get economic indicators (GDP, inflation, unemployment, etc.)"""
        
        try:
            indicators_data = []
            
            # List of economic indicators
            indicators = [
                ("REAL_GDP", "Real GDP"),
                ("INFLATION", "Inflation Rate"),
                ("UNEMPLOYMENT", "Unemployment Rate"),
                ("FEDERAL_FUNDS_RATE", "Federal Funds Rate"),
                ("CPI", "Consumer Price Index"),
                ("TREASURY_YIELD", "10-Year Treasury Yield")
            ]
            
            for indicator_code, indicator_name in indicators:
                await self._rate_limit()
                
                params = {
                    "function": "ECONOMIC_INDICATORS",
                    "name": indicator_code,
                    "apikey": self.api_key
                }
                
                async with self.session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if "data" in data:
                            for point in data["data"]:
                                indicators_data.append({
                                    "indicator": indicator_name,
                                    "date": pd.to_datetime(point.get("date")),
                                    "value": float(point.get("value", 0))
                                })
            
            if indicators_data:
                df = pd.DataFrame(indicators_data)
                df = df.sort_values(["indicator", "date"])
                
                return ExternalDataResult(
                    data=df,
                    metadata={
                        "source": "alpha_vantage",
                        "data_type": "economic_indicators",
                        "indicators": [ind[1] for ind in indicators]
                    },
                    source="alpha_vantage",
                    quality_score=0.9
                )
            else:
                return ExternalDataResult(
                    data=pd.DataFrame(),
                    metadata={"error": "No economic data retrieved"},
                    source="alpha_vantage",
                    quality_score=0.0
                )
                
        except Exception as e:
            self.logger.error(f"Alpha Vantage API error: {e}")
            raise DataIntegrationError(f"Failed to retrieve Alpha Vantage data: {e}")
    
    async def get_forex_data(self, currency_pairs: List[str], 
                           start_date: datetime, 
                           end_date: datetime) -> ExternalDataResult:
        """Get foreign exchange data"""
        
        try:
            forex_data = []
            
            for pair in currency_pairs:
                await self._rate_limit()
                
                # Parse currency pair (e.g., "EURUSD" -> from="EUR", to="USD")
                from_currency = pair[:3]
                to_currency = pair[3:]
                
                params = {
                    "function": "FX_DAILY",
                    "from_symbol": from_currency,
                    "to_symbol": to_currency,
                    "apikey": self.api_key,
                    "outputsize": "full"
                }
                
                async with self.session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        time_series_key = "Time Series (FX)"
                        if time_series_key in data:
                            for date_str, values in data[time_series_key].items():
                                date = pd.to_datetime(date_str)
                                
                                # Filter by date range
                                if start_date <= date <= end_date:
                                    forex_data.append({
                                        "currency_pair": pair,
                                        "date": date,
                                        "open": float(values.get("1. open", 0)),
                                        "high": float(values.get("2. high", 0)),
                                        "low": float(values.get("3. low", 0)),
                                        "close": float(values.get("4. close", 0))
                                    })
            
            if forex_data:
                df = pd.DataFrame(forex_data)
                df = df.sort_values(["currency_pair", "date"])
                
                # Calculate additional metrics
                df["daily_return"] = df.groupby("currency_pair")["close"].pct_change()
                df["volatility"] = df.groupby("currency_pair")["daily_return"].rolling(30).std().reset_index(0, drop=True)
                
                return ExternalDataResult(
                    data=df,
                    metadata={
                        "source": "alpha_vantage",
                        "data_type": "forex",
                        "currency_pairs": currency_pairs
                    },
                    source="alpha_vantage",
                    quality_score=0.9
                )
            else:
                return ExternalDataResult(
                    data=pd.DataFrame(),
                    metadata={"error": "No forex data retrieved"},
                    source="alpha_vantage",
                    quality_score=0.0
                )
                
        except Exception as e:
            self.logger.error(f"Alpha Vantage forex API error: {e}")
            raise DataIntegrationError(f"Failed to retrieve forex data: {e}")
    
    async def get_commodity_data(self, commodities: List[str]) -> ExternalDataResult:
        """Get commodity price data"""
        
        try:
            commodity_data = []
            
            # Commodity mapping
            commodity_functions = {
                "crude_oil": "WTI",
                "brent_oil": "BRENT",
                "natural_gas": "NATURAL_GAS",
                "gold": "GOLD",
                "silver": "SILVER",
                "copper": "COPPER",
                "wheat": "WHEAT",
                "corn": "CORN"
            }
            
            for commodity in commodities:
                if commodity.lower() in commodity_functions:
                    await self._rate_limit()
                    
                    params = {
                        "function": commodity_functions[commodity.lower()],
                        "interval": "monthly",
                        "apikey": self.api_key
                    }
                    
                    async with self.session.get(self.base_url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if "data" in data:
                                for point in data["data"]:
                                    commodity_data.append({
                                        "commodity": commodity,
                                        "date": pd.to_datetime(point.get("date")),
                                        "price": float(point.get("value", 0))
                                    })
            
            if commodity_data:
                df = pd.DataFrame(commodity_data)
                df = df.sort_values(["commodity", "date"])
                
                # Calculate returns and volatility
                df["monthly_return"] = df.groupby("commodity")["price"].pct_change()
                df["volatility"] = df.groupby("commodity")["monthly_return"].rolling(12).std().reset_index(0, drop=True)
                
                return ExternalDataResult(
                    data=df,
                    metadata={
                        "source": "alpha_vantage",
                        "data_type": "commodities",
                        "commodities": commodities
                    },
                    source="alpha_vantage",
                    quality_score=0.85
                )
            else:
                return ExternalDataResult(
                    data=pd.DataFrame(),
                    metadata={"error": "No commodity data retrieved"},
                    source="alpha_vantage",
                    quality_score=0.0
                )
                
        except Exception as e:
            self.logger.error(f"Alpha Vantage commodity API error: {e}")
            raise DataIntegrationError(f"Failed to retrieve commodity data: {e}")


class ExternalDataManager:
    """Manages external data connections and integration"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.connectors = {}
        
        # Initialize connectors based on available API keys
        self._initialize_connectors()
    
    def _initialize_connectors(self):
        """Initialize available data connectors"""
        
        # Polygon connector
        polygon_key = os.getenv("POLYGON_API_KEY")
        if polygon_key:
            self.connectors["polygon"] = {
                "class": PolygonConnector,
                "api_key": polygon_key,
                "capabilities": ["stock_data", "market_indices", "sector_data"]
            }
            self.logger.info("Polygon connector initialized")
        
        # Alpha Vantage connector
        alpha_key = os.getenv("ALPHAADVANTAGE_API_KEY")
        if alpha_key:
            self.connectors["alpha_vantage"] = {
                "class": AlphaVantageConnector,
                "api_key": alpha_key,
                "capabilities": ["economic_indicators", "forex_data", "commodity_data"]
            }
            self.logger.info("Alpha Vantage connector initialized")
    
    def get_available_sources(self) -> Dict[str, List[str]]:
        """Get available data sources and their capabilities"""
        
        return {
            source: info["capabilities"] 
            for source, info in self.connectors.items()
        }
    
    async def get_market_data_for_optimization(self, 
                                             symbols: List[str],
                                             lookback_days: int = 252,
                                             include_indices: bool = True,
                                             include_sectors: bool = True) -> Dict[str, ExternalDataResult]:
        """Get comprehensive market data for portfolio optimization"""
        
        results = {}
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        
        if "polygon" in self.connectors:
            try:
                connector_class = self.connectors["polygon"]["class"]
                api_key = self.connectors["polygon"]["api_key"]
                
                async with connector_class(api_key) as connector:
                    # Get stock data
                    if symbols:
                        stock_data = await connector.get_stock_data(symbols, start_date, end_date)
                        results["stocks"] = stock_data
                    
                    # Get market indices
                    if include_indices:
                        indices_data = await connector.get_market_indices(start_date, end_date)
                        results["indices"] = indices_data
                    
                    # Get sector data
                    if include_sectors:
                        sector_data = await connector.get_sector_data(start_date, end_date)
                        results["sectors"] = sector_data
                        
            except Exception as e:
                self.logger.error(f"Failed to get Polygon data: {e}")
                results["polygon_error"] = str(e)
        
        return results
    
    async def get_economic_context_data(self) -> Dict[str, ExternalDataResult]:
        """Get economic context data for optimization"""
        
        results = {}
        
        if "alpha_vantage" in self.connectors:
            try:
                connector_class = self.connectors["alpha_vantage"]["class"]
                api_key = self.connectors["alpha_vantage"]["api_key"]
                
                async with connector_class(api_key) as connector:
                    # Get economic indicators
                    economic_data = await connector.get_economic_indicators()
                    results["economic_indicators"] = economic_data
                    
                    # Get major forex pairs
                    major_pairs = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD"]
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=365)  # 1 year of forex data
                    
                    forex_data = await connector.get_forex_data(major_pairs, start_date, end_date)
                    results["forex"] = forex_data
                    
                    # Get commodity data
                    commodities = ["crude_oil", "gold", "silver", "copper", "wheat"]
                    commodity_data = await connector.get_commodity_data(commodities)
                    results["commodities"] = commodity_data
                    
            except Exception as e:
                self.logger.error(f"Failed to get Alpha Vantage data: {e}")
                results["alpha_vantage_error"] = str(e)
        
        return results
    
    async def get_correlation_matrix(self, symbols: List[str], 
                                   lookback_days: int = 252) -> Optional[pd.DataFrame]:
        """Calculate correlation matrix from real market data"""
        
        try:
            market_data = await self.get_market_data_for_optimization(
                symbols, lookback_days, include_indices=False, include_sectors=False
            )
            
            if "stocks" in market_data and not market_data["stocks"].data.empty:
                df = market_data["stocks"].data
                
                # Pivot to get returns by symbol
                returns_df = df.pivot(index="date", columns="symbol", values="daily_return")
                
                # Calculate correlation matrix
                correlation_matrix = returns_df.corr()
                
                return correlation_matrix
            
        except Exception as e:
            self.logger.error(f"Failed to calculate correlation matrix: {e}")
        
        return None
    
    async def get_risk_metrics(self, symbols: List[str], 
                             lookback_days: int = 252) -> Optional[pd.DataFrame]:
        """Calculate risk metrics from real market data"""
        
        try:
            market_data = await self.get_market_data_for_optimization(
                symbols, lookback_days, include_indices=False, include_sectors=False
            )
            
            if "stocks" in market_data and not market_data["stocks"].data.empty:
                df = market_data["stocks"].data
                
                # Calculate risk metrics by symbol
                risk_metrics = []
                
                for symbol in symbols:
                    symbol_data = df[df["symbol"] == symbol].copy()
                    
                    if not symbol_data.empty:
                        returns = symbol_data["daily_return"].dropna()
                        
                        if len(returns) > 30:  # Need sufficient data
                            metrics = {
                                "symbol": symbol,
                                "expected_return": returns.mean() * 252,  # Annualized
                                "volatility": returns.std() * np.sqrt(252),  # Annualized
                                "sharpe_ratio": (returns.mean() * 252) / (returns.std() * np.sqrt(252)),
                                "max_drawdown": self._calculate_max_drawdown(symbol_data["close"]),
                                "var_95": returns.quantile(0.05),  # 95% VaR
                                "skewness": returns.skew(),
                                "kurtosis": returns.kurtosis()
                            }
                            risk_metrics.append(metrics)
                
                if risk_metrics:
                    return pd.DataFrame(risk_metrics)
            
        except Exception as e:
            self.logger.error(f"Failed to calculate risk metrics: {e}")
        
        return None
    
    def _calculate_max_drawdown(self, prices: pd.Series) -> float:
        """Calculate maximum drawdown from price series"""
        
        try:
            # Calculate cumulative returns
            cumulative = (1 + prices.pct_change()).cumprod()
            
            # Calculate running maximum
            running_max = cumulative.expanding().max()
            
            # Calculate drawdown
            drawdown = (cumulative - running_max) / running_max
            
            return drawdown.min()
            
        except Exception:
            return 0.0
    
    def is_available(self) -> bool:
        """Check if any external data sources are available"""
        return len(self.connectors) > 0
    
    def get_connector_status(self) -> Dict[str, bool]:
        """Get status of all connectors"""
        return {
            "polygon": "polygon" in self.connectors,
            "alpha_vantage": "alpha_vantage" in self.connectors,
            "total_connectors": len(self.connectors)
        }


# Utility functions for data processing
def merge_external_with_synthetic(external_data: ExternalDataResult, 
                                synthetic_data: Dict[str, Any]) -> Dict[str, Any]:
    """Merge external data with synthetic data for optimization"""
    
    merged_data = synthetic_data.copy()
    
    if not external_data.data.empty:
        # Add external data as additional parameters
        merged_data["external_market_data"] = external_data.data.to_dict("records")
        merged_data["external_metadata"] = external_data.metadata
        
        # Extract key metrics for optimization
        if "daily_return" in external_data.data.columns:
            returns = external_data.data.groupby("symbol")["daily_return"].agg([
                "mean", "std", "min", "max"
            ]).reset_index()
            
            merged_data["return_statistics"] = returns.to_dict("records")
        
        if "volatility_30d" in external_data.data.columns:
            volatility = external_data.data.groupby("symbol")["volatility_30d"].last().reset_index()
            merged_data["volatility_data"] = volatility.to_dict("records")
    
    return merged_data


def calculate_portfolio_metrics(returns_data: pd.DataFrame, 
                              weights: Optional[List[float]] = None) -> Dict[str, float]:
    """Calculate portfolio-level metrics from returns data"""
    
    if returns_data.empty:
        return {}
    
    # Equal weights if not provided
    if weights is None:
        n_assets = len(returns_data.columns)
        weights = [1.0 / n_assets] * n_assets
    
    # Calculate portfolio returns
    portfolio_returns = (returns_data * weights).sum(axis=1)
    
    # Calculate metrics
    metrics = {
        "expected_return": portfolio_returns.mean() * 252,  # Annualized
        "volatility": portfolio_returns.std() * np.sqrt(252),  # Annualized
        "sharpe_ratio": (portfolio_returns.mean() * 252) / (portfolio_returns.std() * np.sqrt(252)),
        "max_drawdown": portfolio_returns.min(),
        "var_95": portfolio_returns.quantile(0.05),
        "skewness": portfolio_returns.skew(),
        "kurtosis": portfolio_returns.kurtosis()
    }
    
    return metrics