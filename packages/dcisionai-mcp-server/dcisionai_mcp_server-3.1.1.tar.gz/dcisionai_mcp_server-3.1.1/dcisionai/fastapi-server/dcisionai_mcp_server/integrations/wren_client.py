"""
Wren Engine Client for DcisionAI
Provides semantic data access via Wren Engine for customer database connectivity
"""

import httpx
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WrenConfig:
    """Wren Engine connection configuration"""
    wren_url: str = "http://localhost:8001"
    timeout: int = 10
    mdl_model: str = "portfolio_holdings"


class WrenClient:
    """
    Client for querying data through Wren Engine semantic layer
    
    Enables DcisionAI to connect to customer databases (PostgreSQL, MySQL, Snowflake, etc.)
    via Wren's semantic layer, which provides:
    - Business context and terminology
    - Access control and governance
    - Consistent calculations across queries
    """
    
    def __init__(self, config: WrenConfig):
        self.config = config
        self.client = httpx.AsyncClient(timeout=config.timeout)
    
    async def query_semantic(
        self,
        model: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Query Wren semantic model
        
        Args:
            model: Semantic model name (e.g., 'active_holdings', 'high_margin_products')
            filters: Filter conditions (e.g., {'user_id': 'user_001'})
            limit: Maximum rows to return
            
        Returns:
            Dict with 'data', 'columns', 'row_count'
        """
        try:
            logger.info(f"🔍 Querying Wren model: {model}")
            
            payload = {
                "model": model,
                "filters": filters or {},
                "limit": limit or 1000
            }
            
            response = await self.client.post(
                f"{self.config.wren_url}/v1/query",
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ Wren returned {data.get('row_count', 0)} rows")
            
            return data
            
        except httpx.HTTPError as e:
            logger.error(f"❌ Wren query failed: {e}")
            raise Exception(f"Wren Engine query failed: {str(e)}")
    
    async def get_portfolio_data(self, user_id: str) -> Dict[str, Any]:
        """
        Get portfolio holdings for a specific user
        
        Args:
            user_id: User identifier
            
        Returns:
            Portfolio data with holdings, metrics, concentration
        """
        logger.info(f"📊 Fetching portfolio data for {user_id} via Wren")
        
        try:
            # Query active holdings
            holdings = await self.query_semantic(
                model="active_holdings",
                filters={"user_id": user_id}
            )
            
            # Query portfolio metrics
            metrics = await self.query_semantic(
                model="portfolio_metrics",
                filters={"user_id": user_id}
            )
            
            # Query tech concentration
            tech_concentration = await self.query_semantic(
                model="tech_concentration"
            )
            
            return {
                "holdings": holdings["data"],
                "metrics": metrics["data"][0] if metrics["data"] else {},
                "tech_concentration": tech_concentration["data"][0]["tech_weight"] if tech_concentration["data"] else 0,
                "data_provenance": "wren_engine",
                "source": "supabase",
                "quality_score": 0.95,
                "completeness": 1.0
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to fetch portfolio data: {e}")
            raise
    
    async def get_retail_data(self, store_id: str) -> Dict[str, Any]:
        """
        Get product inventory for a specific store
        
        Args:
            store_id: Store identifier
            
        Returns:
            Inventory data with products, categories, metrics
        """
        logger.info(f"🏪 Fetching retail data for {store_id} via Wren")
        
        try:
            # Query high-margin products
            high_margin = await self.query_semantic(
                model="high_margin_products"
            )
            
            # Query revenue by category
            revenue = await self.query_semantic(
                model="revenue_by_category"
            )
            
            # Query all inventory
            inventory = await self.query_semantic(
                model="product_inventory",
                filters={"store_id": store_id}
            )
            
            return {
                "inventory": inventory["data"],
                "high_margin_products": high_margin["data"],
                "revenue_by_category": revenue["data"],
                "data_provenance": "wren_engine",
                "source": "supabase",
                "quality_score": 0.95,
                "completeness": 1.0
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to fetch retail data: {e}")
            raise
    
    async def health_check(self) -> bool:
        """
        Check if Wren Engine is accessible
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = await self.client.get(f"{self.config.wren_url}/health")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"⚠️ Wren health check failed: {e}")
            return False
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Singleton instance
_wren_client: Optional[WrenClient] = None


def get_wren_client(config: Optional[WrenConfig] = None) -> WrenClient:
    """
    Get or create Wren client singleton
    
    Args:
        config: Optional Wren configuration
        
    Returns:
        WrenClient instance
    """
    global _wren_client
    
    if _wren_client is None:
        _wren_client = WrenClient(config or WrenConfig())
    
    return _wren_client

