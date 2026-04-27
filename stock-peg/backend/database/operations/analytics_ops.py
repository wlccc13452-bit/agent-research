"""Analytics Operations - 分析指标数据操作

提供分析指标相关的数据库操作：
- Force Index 缓存
- PMR K线数据查询
- 市场情绪缓存
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import ForceIndexCache, StockKLineData, MarketSentimentCache

logger = logging.getLogger(__name__)


# ============== Force Index Cache Operations ==============

async def get_force_index_cache(
    db: AsyncSession,
    stock_code: str,
    period: str = "day",
    ema_short: int = 2,
    ema_long: int = 13
) -> Optional[ForceIndexCache]:
    """
    获取 Force Index 缓存
    
    只返回今天的缓存结果（交易日有效）
    """
    try:
        today = datetime.now().date()
        
        stmt = select(ForceIndexCache).where(
            and_(
                ForceIndexCache.stock_code == stock_code,
                ForceIndexCache.period == period,
                ForceIndexCache.ema_short == ema_short,
                ForceIndexCache.ema_long == ema_long,
                ForceIndexCache.calculation_date >= today
            )
        ).order_by(desc(ForceIndexCache.calculation_date)).limit(1)
        
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
        
    except Exception as e:
        logger.warning(f"获取 Force Index 缓存失败 {stock_code}: {str(e)}")
        return None


async def save_force_index_cache(
    db: AsyncSession,
    stock_code: str,
    stock_name: str,
    result: Dict,
    period: str,
    ema_short: int,
    ema_long: int
) -> None:
    """
    保存 Force Index 结果到数据库缓存
    """
    try:
        # 检查是否已存在记录（同一参数组合）
        stmt = select(ForceIndexCache).where(
            and_(
                ForceIndexCache.stock_code == stock_code,
                ForceIndexCache.period == period,
                ForceIndexCache.ema_short == ema_short,
                ForceIndexCache.ema_long == ema_long
            )
        )
        
        query_result = await db.execute(stmt)
        existing_record = query_result.scalar_one_or_none()
        
        current_values = result.get('current_values', {})
        signals = result.get('signals', {})
        trend_analysis = result.get('trend_analysis', {})
        trend_change = result.get('trend_change', {})
        strength_analysis = result.get('strength_analysis', {})
        
        if existing_record:
            # 更新现有记录
            existing_record.stock_name = stock_name
            existing_record.raw_force_index = Decimal(str(current_values.get('raw_force_index', 0)))
            existing_record.fi_short_ema = Decimal(str(current_values.get('fi_short_ema', 0)))
            existing_record.fi_long_ema = Decimal(str(current_values.get('fi_long_ema', 0)))
            existing_record.price_change = Decimal(str(current_values.get('price_change', 0)))
            existing_record.volume = current_values.get('volume', 0)
            existing_record.current_signal = signals.get('current_signal', '中性')
            existing_record.signal_strength = signals.get('signal_strength', 0)
            existing_record.buy_signals = signals.get('buy_signals', [])
            existing_record.sell_signals = signals.get('sell_signals', [])
            existing_record.trend_based_strategy = signals.get('trend_based_strategy', '')
            existing_record.trend_direction = trend_analysis.get('trend_direction', '横盘')
            existing_record.trend_strength = trend_analysis.get('trend_strength', '弱')
            existing_record.trend_description = trend_analysis.get('description', '')
            existing_record.trend_type = trend_change.get('trend_type', '横盘')
            existing_record.fi2_trend = trend_change.get('fi2_trend', '平稳')
            existing_record.fi13_trend = trend_change.get('fi13_trend', '平稳')
            existing_record.trend_strength_change = trend_change.get('trend_strength_change', '无变化')
            existing_record.trend_days = trend_change.get('trend_days', 0)
            existing_record.trend_change_description = trend_change.get('description', '')
            existing_record.buying_power = strength_analysis.get('buying_power', 0)
            existing_record.selling_power = strength_analysis.get('selling_power', 0)
            existing_record.power_balance = strength_analysis.get('power_balance', '买卖平衡')
            existing_record.divergence = 1 if strength_analysis.get('divergence') else 0
            existing_record.recent_data = result.get('recent_data', [])
            existing_record.calculation_date = datetime.now()
        else:
            # 创建新记录
            import json
            new_record = ForceIndexCache(
                stock_code=stock_code,
                stock_name=stock_name,
                period=period,
                ema_short=ema_short,
                ema_long=ema_long,
                raw_force_index=Decimal(str(current_values.get('raw_force_index', 0))),
                fi_short_ema=Decimal(str(current_values.get('fi_short_ema', 0))),
                fi_long_ema=Decimal(str(current_values.get('fi_long_ema', 0))),
                price_change=Decimal(str(current_values.get('price_change', 0))),
                volume=current_values.get('volume', 0),
                current_signal=signals.get('current_signal', '中性'),
                signal_strength=signals.get('signal_strength', 0),
                buy_signals=json.dumps(signals.get('buy_signals', []), ensure_ascii=False),
                sell_signals=json.dumps(signals.get('sell_signals', []), ensure_ascii=False),
                trend_based_strategy=signals.get('trend_based_strategy', ''),
                trend_direction=trend_analysis.get('trend_direction', '横盘'),
                trend_strength=trend_analysis.get('trend_strength', '弱'),
                trend_description=trend_analysis.get('description', ''),
                trend_type=trend_change.get('trend_type', '横盘'),
                fi2_trend=trend_change.get('fi2_trend', '平稳'),
                fi13_trend=trend_change.get('fi13_trend', '平稳'),
                trend_strength_change=trend_change.get('trend_strength_change', '无变化'),
                trend_days=trend_change.get('trend_days', 0),
                trend_change_description=trend_change.get('description', ''),
                buying_power=strength_analysis.get('buying_power', 0),
                selling_power=strength_analysis.get('selling_power', 0),
                power_balance=strength_analysis.get('power_balance', '买卖平衡'),
                divergence=1 if strength_analysis.get('divergence') else 0,
                recent_data=json.dumps(result.get('recent_data', []), ensure_ascii=False),
                calculation_date=datetime.now()
            )
            db.add(new_record)
        
        await db.commit()
        logger.info(f"Force Index 缓存已保存: {stock_code}")
        
    except Exception as e:
        logger.error(f"保存 Force Index 缓存失败 {stock_code}: {str(e)}", exc_info=True)
        raise


# ============== KLine Data Operations (for PMR) ==============

async def get_klines_data(
    db: AsyncSession,
    stock_code: str,
    period: str,
    end_date: date,
    limit: int
) -> List[StockKLineData]:
    """
    获取股票 K 线数据
    
    Args:
        db: 数据库会话
        stock_code: 股票代码
        period: 周期 (day/week/month)
        end_date: 结束日期
        limit: 获取数量
        
    Returns:
        K线数据列表（按时间正序）
    """
    try:
        stmt = select(StockKLineData).where(
            and_(
                StockKLineData.stock_code == stock_code,
                StockKLineData.period == period,
                StockKLineData.trade_date <= end_date
            )
        ).order_by(StockKLineData.trade_date.desc()).limit(limit)
        
        result = await db.execute(stmt)
        klines = result.scalars().all()
        
        # 按时间正序排列
        return list(reversed(klines))
        
    except Exception as e:
        logger.error(f"获取 K 线数据失败 {stock_code}: {str(e)}")
        return []


# ============== Market Sentiment Cache Operations ==============

async def get_latest_market_sentiment(db: AsyncSession) -> Optional[Dict]:
    """
    获取最新的市场情绪数据
    
    Returns:
        市场情绪数据字典，如果不存在则返回None
    """
    try:
        query = select(MarketSentimentCache).order_by(
            desc(MarketSentimentCache.trade_date)
        ).limit(1)
        result = await db.execute(query)
        cache = result.scalar_one_or_none()
        
        if cache:
            return {
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


async def get_market_sentiment_history(
    db: AsyncSession,
    days: int = 30
) -> List[Dict]:
    """
    获取历史市场情绪数据
    
    Args:
        db: 数据库会话
        days: 获取最近多少天的数据
        
    Returns:
        历史市场情绪数据列表
    """
    try:
        from datetime import timedelta
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


async def save_market_sentiment(
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


async def is_market_sentiment_cache_valid(db: AsyncSession) -> bool:
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
