"""Force Index Operations - Force Index 缓存数据操作

提供Force Index缓存相关的数据库操作：
- 获取缓存
- 保存缓存
- 检查缓存有效性
"""

import logging
import json
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Dict

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import ForceIndexCache

logger = logging.getLogger(__name__)


async def get_force_index_cache(
    db: AsyncSession,
    stock_code: str,
    period: str = "day",
    ema_short: int = 2,
    ema_long: int = 13
) -> Optional[Dict]:
    """
    从数据库获取缓存的Force Index结果
    
    只返回今天的缓存结果（交易日有效）
    
    Args:
        db: 数据库会话
        stock_code: 股票代码
        period: K线周期
        ema_short: 短期EMA周期
        ema_long: 长期EMA周期
        
    Returns:
        Force Index分析结果字典，如果不存在或已过期则返回None
    """
    try:
        # 查询今天的缓存
        today = datetime.now().date()
        
        stmt = select(ForceIndexCache).where(
            ForceIndexCache.stock_code == stock_code,
            ForceIndexCache.period == period,
            ForceIndexCache.ema_short == ema_short,
            ForceIndexCache.ema_long == ema_long,
            ForceIndexCache.calculation_date >= today
        ).order_by(desc(ForceIndexCache.calculation_date)).limit(1)
        
        result = await db.execute(stmt)
        cache_record = result.scalar_one_or_none()
        
        if not cache_record:
            return None
        
        # 从缓存记录构建返回结果
        return {
            'stock_code': cache_record.stock_code,
            'stock_name': cache_record.stock_name or cache_record.stock_code,
            'period': cache_record.period,
            'calculation_date': cache_record.calculation_date.isoformat(),
            'parameters': {
                'ema_short': cache_record.ema_short,
                'ema_long': cache_record.ema_long
            },
            'current_values': {
                'raw_force_index': float(cache_record.raw_force_index) if cache_record.raw_force_index else 0,
                'fi_short_ema': float(cache_record.fi_short_ema) if cache_record.fi_short_ema else 0,
                'fi_long_ema': float(cache_record.fi_long_ema) if cache_record.fi_long_ema else 0,
                'price_change': float(cache_record.price_change) if cache_record.price_change else 0,
                'volume': cache_record.volume or 0
            },
            'signals': {
                'current_signal': cache_record.current_signal or '中性',
                'signal_strength': cache_record.signal_strength or 0,
                'buy_signals': json.loads(cache_record.buy_signals) if cache_record.buy_signals else [],
                'sell_signals': json.loads(cache_record.sell_signals) if cache_record.sell_signals else [],
                'trend_based_strategy': cache_record.trend_based_strategy or ''
            },
            'trend_analysis': {
                'trend_direction': cache_record.trend_direction or '横盘',
                'trend_strength': cache_record.trend_strength or '弱',
                'description': cache_record.trend_description or ''
            },
            'trend_change': {
                'trend_type': cache_record.trend_type or '横盘',
                'fi2_trend': cache_record.fi2_trend or '平稳',
                'fi13_trend': cache_record.fi13_trend or '平稳',
                'trend_strength_change': cache_record.trend_strength_change or '无变化',
                'trend_days': cache_record.trend_days or 0,
                'description': cache_record.trend_change_description or ''
            },
            'strength_analysis': {
                'buying_power': cache_record.buying_power or 0,
                'selling_power': cache_record.selling_power or 0,
                'power_balance': cache_record.power_balance or '买卖平衡',
                'divergence': bool(cache_record.divergence)
            },
            'recent_data': json.loads(cache_record.recent_data) if cache_record.recent_data else []
        }
        
    except Exception as e:
        logger.warning(f"获取Force Index缓存失败 {stock_code}: {str(e)}")
        return None


async def save_force_index_cache(
    db: AsyncSession,
    stock_code: str,
    stock_name: str,
    result: Dict,
    period: str = "day",
    ema_short: int = 2,
    ema_long: int = 13
) -> bool:
    """
    保存Force Index结果到数据库缓存
    
    Args:
        db: 数据库会话
        stock_code: 股票代码
        stock_name: 股票名称
        result: Force Index分析结果
        period: K线周期
        ema_short: 短期EMA周期
        ema_long: 长期EMA周期
        
    Returns:
        是否保存成功
    """
    try:
        # 检查是否已存在记录（同一参数组合）
        stmt = select(ForceIndexCache).where(
            ForceIndexCache.stock_code == stock_code,
            ForceIndexCache.period == period,
            ForceIndexCache.ema_short == ema_short,
            ForceIndexCache.ema_long == ema_long
        )
        
        query_result = await db.execute(stmt)
        existing_record = query_result.scalar_one_or_none()
        
        if existing_record:
            # 更新现有记录
            existing_record.stock_name = stock_name
            existing_record.raw_force_index = Decimal(str(result['current_values']['raw_force_index']))
            existing_record.fi_short_ema = Decimal(str(result['current_values']['fi_short_ema']))
            existing_record.fi_long_ema = Decimal(str(result['current_values']['fi_long_ema']))
            existing_record.price_change = Decimal(str(result['current_values']['price_change']))
            existing_record.volume = result['current_values']['volume']
            existing_record.current_signal = result['signals']['current_signal']
            existing_record.signal_strength = result['signals']['signal_strength']
            existing_record.buy_signals = json.dumps(result['signals']['buy_signals'], ensure_ascii=False)
            existing_record.sell_signals = json.dumps(result['signals']['sell_signals'], ensure_ascii=False)
            existing_record.trend_based_strategy = result['signals'].get('trend_based_strategy', '')
            existing_record.trend_direction = result['trend_analysis']['trend_direction']
            existing_record.trend_strength = result['trend_analysis']['trend_strength']
            existing_record.trend_description = result['trend_analysis']['description']
            existing_record.trend_type = result['trend_change']['trend_type']
            existing_record.fi2_trend = result['trend_change']['fi2_trend']
            existing_record.fi13_trend = result['trend_change']['fi13_trend']
            existing_record.trend_strength_change = result['trend_change']['trend_strength_change']
            existing_record.trend_days = result['trend_change']['trend_days']
            existing_record.trend_change_description = result['trend_change']['description']
            existing_record.buying_power = result['strength_analysis']['buying_power']
            existing_record.selling_power = result['strength_analysis']['selling_power']
            existing_record.power_balance = result['strength_analysis']['power_balance']
            existing_record.divergence = 1 if result['strength_analysis']['divergence'] else 0
            existing_record.recent_data = json.dumps(result['recent_data'], ensure_ascii=False)
            existing_record.calculation_date = datetime.now()
            
            logger.info(f"更新Force Index缓存: {stock_code}")
        else:
            # 创建新记录
            new_record = ForceIndexCache(
                stock_code=stock_code,
                stock_name=stock_name,
                period=period,
                ema_short=ema_short,
                ema_long=ema_long,
                raw_force_index=Decimal(str(result['current_values']['raw_force_index'])),
                fi_short_ema=Decimal(str(result['current_values']['fi_short_ema'])),
                fi_long_ema=Decimal(str(result['current_values']['fi_long_ema'])),
                price_change=Decimal(str(result['current_values']['price_change'])),
                volume=result['current_values']['volume'],
                current_signal=result['signals']['current_signal'],
                signal_strength=result['signals']['signal_strength'],
                buy_signals=json.dumps(result['signals']['buy_signals'], ensure_ascii=False),
                sell_signals=json.dumps(result['signals']['sell_signals'], ensure_ascii=False),
                trend_based_strategy=result['signals'].get('trend_based_strategy', ''),
                trend_direction=result['trend_analysis']['trend_direction'],
                trend_strength=result['trend_analysis']['trend_strength'],
                trend_description=result['trend_analysis']['description'],
                trend_type=result['trend_change']['trend_type'],
                fi2_trend=result['trend_change']['fi2_trend'],
                fi13_trend=result['trend_change']['fi13_trend'],
                trend_strength_change=result['trend_change']['trend_strength_change'],
                trend_days=result['trend_change']['trend_days'],
                trend_change_description=result['trend_change']['description'],
                buying_power=result['strength_analysis']['buying_power'],
                selling_power=result['strength_analysis']['selling_power'],
                power_balance=result['strength_analysis']['power_balance'],
                divergence=1 if result['strength_analysis']['divergence'] else 0,
                recent_data=json.dumps(result['recent_data'], ensure_ascii=False),
                calculation_date=datetime.now()
            )
            db.add(new_record)
            logger.info(f"创建Force Index缓存: {stock_code}")
        
        await db.commit()
        return True
        
    except Exception as e:
        logger.error(f"保存Force Index缓存失败 {stock_code}: {str(e)}")
        await db.rollback()
        return False


__all__ = [
    'get_force_index_cache',
    'save_force_index_cache',
]
