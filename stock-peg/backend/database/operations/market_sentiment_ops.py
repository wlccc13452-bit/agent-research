"""Market Sentiment Operations - 市场情绪数据操作

提供市场情绪数据相关的数据库操作：
- 查询最新市场情绪
- 查询历史市场情绪
- 保存市场情绪数据
- 检查缓存有效性
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import MarketSentimentCache

logger = logging.getLogger(__name__)


async def get_latest_sentiment(db: AsyncSession) -> Optional[Dict]:
    """
    获取最新的市场情绪数据
    
    Args:
        db: 数据库会话
        
    Returns:
        市场情绪数据字典，如果不存在则返回None
    """
    try:
        query = select(MarketSentimentCache).order_by(desc(MarketSentimentCache.trade_date)).limit(1)
        result = await db.execute(query)
        cache = result.scalar_one_or_none()
        
        if cache:
            return {
                'trade_date': cache.trade_date.isoformat() if cache.trade_date else None,
                'total_count': cache.total_count,
                'up_count': cache.up_count,
                'down_count': cache.down_count,
                'flat_count': cache.flat_count,
                'limit_up': cache.limit_up,
                'limit_down': cache.limit_down,
                'market_breadth': float(cache.market_breadth) if cache.market_breadth else 0.0,
                'avg_change_pct': float(cache.avg_change_pct) if cache.avg_change_pct else None,
                'sh_index_close': float(cache.sh_index_close) if cache.sh_index_close else None,
                'sh_index_change_pct': float(cache.sh_index_change_pct) if cache.sh_index_change_pct else None,
                'data_source': cache.data_source,
                'data_quality': cache.data_quality,
                'timestamp': cache.trade_date.isoformat() if cache.trade_date else None,
            }
        
        return None
        
    except Exception as e:
        logger.error(f"获取市场情绪缓存失败: {str(e)}")
        return None


async def get_sentiment_by_date(db: AsyncSession, trade_date: date) -> Optional[Dict]:
    """
    获取指定日期的市场情绪数据
    
    Args:
        db: 数据库会话
        trade_date: 交易日期
        
    Returns:
        市场情绪数据字典，如果不存在则返回None
    """
    try:
        query = select(MarketSentimentCache).where(
            MarketSentimentCache.trade_date == trade_date
        )
        result = await db.execute(query)
        cache = result.scalar_one_or_none()
        
        if cache:
            return {
                'trade_date': cache.trade_date,
                'total_count': cache.total_count,
                'up_count': cache.up_count,
                'down_count': cache.down_count,
                'flat_count': cache.flat_count,
                'limit_up': cache.limit_up,
                'limit_down': cache.limit_down,
                'market_breadth': float(cache.market_breadth) if cache.market_breadth else 0.0,
                'avg_change_pct': float(cache.avg_change_pct) if cache.avg_change_pct else None,
                'sh_index_close': float(cache.sh_index_close) if cache.sh_index_close else None,
                'sh_index_change_pct': float(cache.sh_index_change_pct) if cache.sh_index_change_pct else None,
                'data_source': cache.data_source,
            }
        return None
        
    except Exception as e:
        logger.error(f"获取指定日期市场情绪数据失败: {str(e)}")
        return None


async def get_sentiment_history(db: AsyncSession, days: int = 30) -> List[Dict]:
    """
    获取历史市场情绪数据
    
    Args:
        db: 数据库会话
        days: 获取最近多少天的数据
        
    Returns:
        历史市场情绪数据列表
    """
    try:
        start_date = date.today() - timedelta(days=days)
        
        query = select(MarketSentimentCache).where(
            MarketSentimentCache.trade_date >= start_date
        ).order_by(MarketSentimentCache.trade_date)
        
        result = await db.execute(query)
        caches = result.scalars().all()
        
        history = []
        for cache in caches:
            history.append({
                'date': cache.trade_date.isoformat(),
                'total_count': cache.total_count,
                'up_count': cache.up_count,
                'down_count': cache.down_count,
                'flat_count': cache.flat_count,
                'limit_up': cache.limit_up,
                'limit_down': cache.limit_down,
                'market_breadth': float(cache.market_breadth) if cache.market_breadth else 0.0,
                'sh_index_close': float(cache.sh_index_close) if cache.sh_index_close else None,
            })
        
        return history
        
    except Exception as e:
        logger.error(f"获取历史市场情绪数据失败: {str(e)}")
        return []


async def save_sentiment(
    db: AsyncSession,
    sentiment_data: Dict,
    trade_date: Optional[date] = None
) -> bool:
    """
    保存市场情绪数据到缓存
    
    Args:
        db: 数据库会话
        sentiment_data: 市场情绪数据字典
        trade_date: 交易日期，默认为今天
        
    Returns:
        是否保存成功
    """
    try:
        if trade_date is None:
            trade_date = date.today()
        
        # 检查是否已存在
        query = select(MarketSentimentCache).where(
            MarketSentimentCache.trade_date == trade_date
        )
        result = await db.execute(query)
        cache = result.scalar_one_or_none()
        
        if cache:
            # 更新现有记录
            cache.total_count = sentiment_data.get('total_count', 0)
            cache.up_count = sentiment_data.get('up_count', 0)
            cache.down_count = sentiment_data.get('down_count', 0)
            cache.flat_count = sentiment_data.get('flat_count', 0)
            cache.limit_up = sentiment_data.get('limit_up', 0)
            cache.limit_down = sentiment_data.get('limit_down', 0)
            cache.market_breadth = sentiment_data.get('market_breadth', 0.0)
            cache.avg_change_pct = sentiment_data.get('avg_change_pct')
            cache.sh_index_close = sentiment_data.get('sh_index_close')
            cache.sh_index_change_pct = sentiment_data.get('sh_index_change_pct')
            cache.data_source = sentiment_data.get('data_source', 'unknown')
            cache.data_quality = sentiment_data.get('data_quality', 'partial')
            cache.updated_at = datetime.now()
            
            logger.info(f"更新市场情绪缓存: {trade_date}")
        else:
            # 创建新记录
            cache = MarketSentimentCache(
                trade_date=trade_date,
                total_count=sentiment_data.get('total_count', 0),
                up_count=sentiment_data.get('up_count', 0),
                down_count=sentiment_data.get('down_count', 0),
                flat_count=sentiment_data.get('flat_count', 0),
                limit_up=sentiment_data.get('limit_up', 0),
                limit_down=sentiment_data.get('limit_down', 0),
                market_breadth=sentiment_data.get('market_breadth', 0.0),
                avg_change_pct=sentiment_data.get('avg_change_pct'),
                sh_index_close=sentiment_data.get('sh_index_close'),
                sh_index_change_pct=sentiment_data.get('sh_index_change_pct'),
                data_source=sentiment_data.get('data_source', 'unknown'),
                data_quality=sentiment_data.get('data_quality', 'partial'),
            )
            db.add(cache)
            
            logger.info(f"创建市场情绪缓存: {trade_date}")
        
        await db.commit()
        return True
        
    except Exception as e:
        logger.error(f"保存市场情绪缓存失败: {str(e)}")
        await db.rollback()
        return False


async def is_cache_valid(db: AsyncSession) -> bool:
    """
    检查缓存是否有效（今天是否有完整数据，必须>=5000只股票）
    
    Args:
        db: 数据库会话
        
    Returns:
        缓存是否有效
    """
    try:
        today = date.today()
        query = select(MarketSentimentCache).where(
            MarketSentimentCache.trade_date == today
        )
        result = await db.execute(query)
        cache = result.scalar_one_or_none()
        
        # 检查数据质量：必须有>=5000只股票
        if cache and cache.total_count >= 5000:
            return True
        
        return False

    except Exception as e:
        logger.error(f"检查市场情绪缓存有效性失败: {str(e)}")
        return False


async def get_stored_trade_dates(db: AsyncSession, start_date: date) -> List[date]:
    """
    获取已存储的交易日期列表

    Args:
        db: 数据库会话
        start_date: 起始日期

    Returns:
        已存储的交易日期列表
    """
    try:
        query = select(MarketSentimentCache.trade_date).where(
            MarketSentimentCache.trade_date >= start_date
        )
        result = await db.execute(query)
        stored_dates_raw = result.scalars().all()
        # 兼容 date 对象和字符串
        stored_dates = []
        for d in stored_dates_raw:
            if isinstance(d, date):
                stored_dates.append(d)
            elif isinstance(d, str):
                stored_dates.append(datetime.strptime(d, '%Y-%m-%d').date())
        return stored_dates
    except Exception as e:
        logger.error(f"获取已存储交易日期失败: {str(e)}")
        return []


__all__ = [
    'get_latest_sentiment',
    'get_sentiment_history',
    'get_sentiment_by_date',
    'save_sentiment',
    'is_cache_valid',
    'get_stored_trade_dates',
]
