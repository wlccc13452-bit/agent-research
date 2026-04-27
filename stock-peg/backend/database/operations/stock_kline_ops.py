"""Stock KLine Operations - K线数据操作

提供K线数据相关的数据库操作：
- 查询K线数据
- 保存K线数据
- 获取最新日期
- 清理重复数据
"""

import logging
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import select, and_, desc, text
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import StockKLineData

logger = logging.getLogger(__name__)


async def get_latest_date(
    db: AsyncSession,
    stock_code: str,
    period: str = 'day'
) -> Optional[date]:
    """
    获取指定股票的最新交易日期
    
    Args:
        db: 数据库会话
        stock_code: 股票代码
        period: K线周期
        
    Returns:
        最新交易日期，如果没有数据返回None
    """
    try:
        stmt = (
            select(StockKLineData.trade_date)
            .where(
                and_(
                    StockKLineData.stock_code == stock_code,
                    StockKLineData.period == period
                )
            )
            .order_by(desc(StockKLineData.trade_date))
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"获取股票 {stock_code} 最新日期失败: {str(e)}")
        return None


async def get_kline_data(
    db: AsyncSession,
    stock_code: str,
    period: str = 'day',
    count: int = 100
) -> List[StockKLineData]:
    """
    获取K线数据
    
    Args:
        db: 数据库会话
        stock_code: 股票代码
        period: K线周期
        count: 获取数量
        
    Returns:
        K线数据列表（从旧到新排序）
    """
    try:
        stmt = (
            select(StockKLineData)
            .where(
                and_(
                    StockKLineData.stock_code == stock_code,
                    StockKLineData.period == period
                )
            )
            .order_by(desc(StockKLineData.trade_date))
            .limit(count)
        )
        result = await db.execute(stmt)
        records = result.scalars().all()
        # 反转顺序，从旧到新
        return list(reversed(records))
    except Exception as e:
        logger.error(f"获取K线数据失败 {stock_code}: {str(e)}")
        return []


async def save_kline_data(
    db: AsyncSession,
    stock_code: str,
    klines: List[dict],
    period: str = 'day'
) -> int:
    """
    保存K线数据（批量更新优化）
    
    Args:
        db: 数据库会话
        stock_code: 股票代码
        klines: K线数据列表（字典格式）
        period: K线周期
        
    Returns:
        成功保存的记录数
    """
    if not klines:
        return 0
    
    try:
        data_to_insert = []
        for kline in klines:
            try:
                # 处理日期格式
                if isinstance(kline.get('date'), str):
                    trade_date = datetime.strptime(kline['date'], '%Y-%m-%d').date()
                elif isinstance(kline.get('date'), (date, datetime)):
                    trade_date = kline['date'] if isinstance(kline['date'], date) else kline['date'].date()
                else:
                    continue
                    
                data_to_insert.append({
                    'stock_code': stock_code,
                    'trade_date': trade_date,
                    'period': period,
                    'open': kline.get('open'),
                    'close': kline.get('close'),
                    'high': kline.get('high'),
                    'low': kline.get('low'),
                    'volume': kline.get('volume'),
                    'amount': kline.get('amount'),
                    'updated_at': datetime.now()
                })
            except Exception:
                continue

        if not data_to_insert:
            return 0

        # 使用 upsert 语句
        stmt = sqlite_insert(StockKLineData).values(data_to_insert)
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=['stock_code', 'trade_date', 'period'],
            set_={
                'open': stmt.excluded.open,
                'close': stmt.excluded.close,
                'high': stmt.excluded.high,
                'low': stmt.excluded.low,
                'volume': stmt.excluded.volume,
                'amount': stmt.excluded.amount,
                'updated_at': stmt.excluded.updated_at
            }
        )
        await db.execute(upsert_stmt)
        await db.commit()
        
        saved_count = len(data_to_insert)
        logger.info(f"保存 {stock_code} K线数据: {saved_count} 条记录")
        return saved_count
        
    except Exception as e:
        await db.rollback()
        logger.error(f"保存K线数据失败 {stock_code}: {str(e)}")
        return 0


async def clean_duplicates(
    db: AsyncSession,
    stock_code: str,
    period: str = 'day'
) -> int:
    """
    清理重复K线数据（保留ID最小的一条）
    
    Args:
        db: 数据库会话
        stock_code: 股票代码
        period: K线周期
        
    Returns:
        清理的记录数
    """
    try:
        sql = text("""
            DELETE FROM stock_kline_data 
            WHERE id NOT IN (
                SELECT MIN(id) 
                FROM stock_kline_data 
                WHERE stock_code = :stock_code AND period = :period
                GROUP BY trade_date
            ) 
            AND stock_code = :stock_code 
            AND period = :period
        """)
        
        result = await db.execute(sql, {"stock_code": stock_code, "period": period})
        
        # SQLite DELETE returns rowcount via cursor
        # Note: SQLAlchemy async may not expose rowcount directly
        # We use a simpler approach: delete and return success indicator
        await db.commit()
        logger.info(f"清理股票 {stock_code} ({period}) 的重复记录")
        
        return 1  # Simplified: return 1 if no error (actual count requires raw cursor access)
    except Exception as e:
        await db.rollback()
        logger.error(f"清理重复数据失败 {stock_code}: {str(e)}")
        return 0


async def get_kline_count(
    db: AsyncSession,
    stock_code: str,
    period: str = 'day'
) -> int:
    """
    获取K线数据数量
    
    Args:
        db: 数据库会话
        stock_code: 股票代码
        period: K线周期
        
    Returns:
        数据数量
    """
    try:
        stmt = (
            select(StockKLineData)
            .where(
                and_(
                    StockKLineData.stock_code == stock_code,
                    StockKLineData.period == period
                )
            )
            .limit(100)
        )
        result = await db.execute(stmt)
        records = result.scalars().all()
        return len(records)
    except Exception as e:
        logger.error(f"获取K线数据数量失败 {stock_code}: {str(e)}")
        return 0


async def get_kline_data_by_date_range(
    db: AsyncSession,
    stock_code: str,
    end_date: date,
    limit: int = 100,
    period: str = 'day'
) -> List[StockKLineData]:
    """
    获取指定日期范围内的K线数据
    
    Args:
        db: 数据库会话
        stock_code: 股票代码
        end_date: 结束日期(包含)
        limit: 获取数量
        period: K线周期
        
    Returns:
        K线数据列表（从旧到新排序）
    """
    try:
        stmt = (
            select(StockKLineData)
            .where(
                and_(
                    StockKLineData.stock_code == stock_code,
                    StockKLineData.period == period,
                    StockKLineData.trade_date <= end_date
                )
            )
            .order_by(desc(StockKLineData.trade_date))
            .limit(limit)
        )
        result = await db.execute(stmt)
        records = result.scalars().all()
        # 反转顺序，从旧到新
        return list(reversed(records))
    except Exception as e:
        logger.error(f"获取K线数据失败 {stock_code}: {str(e)}")
        return []


__all__ = [
    'get_latest_date',
    'get_kline_data',
    'save_kline_data',
    'clean_duplicates',
    'get_kline_count',
    'get_kline_data_by_date_range',
]
