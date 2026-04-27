"""市场情绪数据缓存服务"""
import logging
from typing import Optional, List, Dict
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from database.operations import (
    get_latest_sentiment as ops_get_latest_sentiment,
    get_sentiment_history as ops_get_sentiment_history,
    save_sentiment as ops_save_sentiment,
    is_cache_valid as ops_is_cache_valid,
)

logger = logging.getLogger(__name__)


class MarketSentimentCacheService:
    """市场情绪数据缓存服务"""
    
    async def get_latest_sentiment(self, db: AsyncSession) -> Optional[Dict]:
        """获取最新的市场情绪数据 - 委托给 ops 层"""
        return await ops_get_latest_sentiment(db)
    
    async def get_sentiment_history(self, db: AsyncSession, days: int = 30) -> List[Dict]:
        """获取历史市场情绪数据 - 委托给 ops 层"""
        return await ops_get_sentiment_history(db, days)
    
    async def save_sentiment(self, db: AsyncSession, sentiment_data: Dict, trade_date: Optional[date] = None) -> bool:
        """保存市场情绪数据到缓存 - 委托给 ops 层"""
        return await ops_save_sentiment(db, sentiment_data, trade_date)
    
    async def is_cache_valid(self, db: AsyncSession) -> bool:
        """检查缓存是否有效 - 委托给 ops 层"""
        return await ops_is_cache_valid(db)


# 单例实例
market_sentiment_cache_service = MarketSentimentCacheService()
