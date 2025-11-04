"""
External Data Integrations for DcisionAI
=========================================

Market data providers, economic APIs, and other external data sources
that augment optimization models with real-world data.
"""

from .market_data_adapter import MarketDataAdapter
from .market_data_tool import augment_with_market_data

__all__ = [
    'MarketDataAdapter',
    'augment_with_market_data'
]

