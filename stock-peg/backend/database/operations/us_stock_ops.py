"""US Stock Operations - 美股数据操作

提供美股数据相关的数据库操作：
- 保存美股日线数据
- 查询美股日线数据
"""

import logging
from datetime import date, datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import USDailyData

logger = logging.getLogger(__name__)


async def get_us_daily_data(
    db: AsyncSession,
    symbol: str,
    limit: int = 1
) -> List[Dict[str, Any]]:
    """
    获取美股日线数据
    
    Args:
        db: 数据库会话
        symbol: 美股代码
        limit: 返回记录数
        
    Returns:
        日线数据列表
    """
    try:
        stmt = select(USDailyData).where(
            USDailyData.us_stock_code == symbol
        ).order_by(desc(USDailyData.trade_date)).limit(limit)
        
        result = await db.execute(stmt)
        records = result.scalars().all()
        
        return [{
            'symbol': r.us_stock_code,
            'trade_date': r.trade_date,
            'open': float(r.open_price) if r.open_price else None,
            'close': float(r.close_price) if r.close_price else None,
            'high': float(r.high_price) if r.high_price else None,
            'low': float(r.low_price) if r.low_price else None,
            'volume': r.volume,
            'change_pct': float(r.change_pct) if r.change_pct else None,
            'ma5': float(r.ma5) if r.ma5 else None,
            'ma10': float(r.ma10) if r.ma10 else None,
            'ma20': float(r.ma20) if r.ma20 else None,
            'rsi': float(r.rsi) if r.rsi else None,
            'macd': float(r.macd) if r.macd else None
        } for r in records]
        
    except Exception as e:
        logger.error(f"获取美股数据失败 {symbol}: {str(e)}")
        return []


async def save_us_daily_data(
    db: AsyncSession,
    data: Dict[str, Any]
) -> USDailyData:
    """
    保存美股日线数据（upsert）
    
    Args:
        db: 数据库会话
        data: 美股数据字典，包含：
            - symbol: 美股代码
            - timestamp: 时间戳
            - open, high, low, previous_close: 价格数据
            - volume: 成交量
            - change_pct: 涨跌幅
            - ma_5, ma_10, ma_20: 均线
            - rsi, macd: 技术指标
        
    Returns:
        创建或更新的 USDailyData 对象
    """
    try:
        symbol = data['symbol']
        trade_date = data.get('timestamp', datetime.now()).date()
        
        # 检查是否已存在
        stmt = select(USDailyData).where(
            and_(
                USDailyData.us_stock_code == symbol,
                USDailyData.trade_date == trade_date
            )
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            # 更新
            existing.open_price = data.get('open')
            existing.close_price = data.get('previous_close')
            existing.high_price = data.get('high')
            existing.low_price = data.get('low')
            existing.volume = data.get('volume')
            existing.change_pct = data.get('change_pct')
            existing.ma5 = data.get('ma_5')
            existing.ma10 = data.get('ma_10')
            existing.ma20 = data.get('ma_20')
            existing.rsi = data.get('rsi')
            existing.macd = data.get('macd')
            
            await db.commit()
            await db.refresh(existing)
            
            logger.debug(f"更新美股数据: {symbol} {trade_date}")
            return existing
        else:
            # 新增
            new_record = USDailyData(
                us_stock_code=symbol,
                trade_date=trade_date,
                open_price=data.get('open'),
                close_price=data.get('previous_close'),
                high_price=data.get('high'),
                low_price=data.get('low'),
                volume=data.get('volume'),
                change_pct=data.get('change_pct'),
                ma5=data.get('ma_5'),
                ma10=data.get('ma_10'),
                ma20=data.get('ma_20'),
                rsi=data.get('rsi'),
                macd=data.get('macd')
            )
            
            db.add(new_record)
            await db.commit()
            await db.refresh(new_record)
            
            logger.debug(f"保存美股数据: {symbol} {trade_date}")
            return new_record
            
    except Exception as e:
        logger.error(f"保存美股数据失败: {str(e)}")
        await db.rollback()
        raise


async def get_latest_us_data_date(
    db: AsyncSession,
    symbol: str
) -> Optional[date]:
    """
    获取美股最新数据日期
    
    Args:
        db: 数据库会话
        symbol: 美股代码
        
    Returns:
        最新数据日期或None
    """
    try:
        stmt = select(USDailyData.trade_date).where(
            USDailyData.us_stock_code == symbol
        ).order_by(desc(USDailyData.trade_date)).limit(1)
        
        result = await db.execute(stmt)
        row = result.scalar_one_or_none()
        return row
        
    except Exception as e:
        logger.error(f"获取美股最新日期失败 {symbol}: {str(e)}")
        return None


__all__ = [
    'get_us_daily_data',
    'save_us_daily_data',
    'get_latest_us_data_date',
]
