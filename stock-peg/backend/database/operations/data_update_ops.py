"""Data Update Operations - 数据更新日志操作

提供数据更新日志相关的数据库操作：
- 记录更新开始
- 记录更新完成
- 查询更新状态
- 检查数据完整性
"""

import logging
from datetime import datetime
from typing import Dict, Optional, List

from sqlalchemy import select, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import DataUpdateLog, StockKLineData, USDailyData

logger = logging.getLogger(__name__)


async def record_update_start(
    db: AsyncSession,
    stock_code: str,
    data_type: str,
    update_type: str = 'auto'
) -> int:
    """
    记录更新开始
    
    Args:
        db: 数据库会话
        stock_code: 股票代码
        data_type: 数据类型 (kline/financial/us_index)
        update_type: 更新类型 (auto/manual)
        
    Returns:
        log_id: 更新日志ID，失败返回0
    """
    try:
        log = DataUpdateLog(
            stock_code=stock_code,
            data_type=data_type,
            update_type=update_type,
            started_at=datetime.now(),
            status='running'
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        
        logger.info(f"记录更新开始: {stock_code}, data_type={data_type}, log_id={log.id}")
        return log.id
        
    except Exception as e:
        logger.error(f"记录更新开始失败: {str(e)}")
        await db.rollback()
        return 0


async def record_update_complete(
    db: AsyncSession,
    log_id: int,
    records_updated: int,
    error_message: Optional[str] = None
) -> bool:
    """
    记录更新完成
    
    Args:
        db: 数据库会话
        log_id: 更新日志ID
        records_updated: 更新的记录数
        error_message: 错误消息（可选）
        
    Returns:
        是否记录成功
    """
    if log_id == 0:
        return False
    
    try:
        stmt = select(DataUpdateLog).where(DataUpdateLog.id == log_id).limit(1)
        log = (await db.execute(stmt)).scalars().first()
        
        if log:
            log.completed_at = datetime.now()
            log.status = 'completed' if not error_message else 'failed'
            log.records_updated = records_updated
            log.error_message = error_message
            await db.commit()
            
            logger.info(f"记录更新完成: log_id={log_id}, records={records_updated}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"记录更新完成失败: {str(e)}")
        await db.rollback()
        return False


async def get_latest_update_log(
    db: AsyncSession,
    stock_code: str,
    data_type: str
) -> Optional[DataUpdateLog]:
    """
    获取最新的更新日志
    
    Args:
        db: 数据库会话
        stock_code: 股票代码
        data_type: 数据类型
        
    Returns:
        最新的更新日志对象或None
    """
    stmt = select(DataUpdateLog).where(
        and_(
            DataUpdateLog.stock_code == stock_code,
            DataUpdateLog.data_type == data_type
        )
    ).order_by(desc(DataUpdateLog.started_at)).limit(1)
    
    result = await db.execute(stmt)
    return result.scalars().first()


async def check_kline_data_integrity(
    db: AsyncSession,
    stock_code: str
) -> Dict:
    """
    检查K线数据完整性
    
    Args:
        db: 数据库会话
        stock_code: 股票代码
        
    Returns:
        {
            'is_complete': bool,
            'reason': str,
            'last_update': datetime,
            'record_count': int
        }
    """
    try:
        # 使用单条查询获取最新数据和数据量状态
        stmt = (
            select(StockKLineData)
            .where(
                and_(
                    StockKLineData.stock_code == stock_code,
                    StockKLineData.period == 'day'
                )
            )
            .order_by(desc(StockKLineData.trade_date))
            .limit(100)  # 只取前100条判断完整性
        )
        
        result = await db.execute(stmt)
        records = result.scalars().all()
        total_count = len(records)

        if total_count == 0:
            return {
                'is_complete': False,
                'reason': '数据库无K线数据',
                'last_update': None,
                'record_count': 0
            }

        latest_record = records[0]
        
        if total_count < 100:
            return {
                'is_complete': False,
                'reason': f'K线数据不足（仅{total_count}条）',
                'last_update': latest_record.updated_at or latest_record.created_at,
                'record_count': total_count
            }

        # 数据量足够，检查最新记录日期
        if latest_record:
            last_update = latest_record.updated_at or latest_record.created_at
            today = datetime.now().date()
            latest_date = latest_record.trade_date
            days_diff = (today - latest_date).days
            if days_diff > 3:
                return {
                    'is_complete': True,
                    'reason': f'数据已过期{days_diff}天',
                    'last_update': last_update,
                    'record_count': total_count
                }

            return {
                'is_complete': True,
                'reason': '数据完整',
                'last_update': last_update,
                'record_count': total_count
            }

        return {
            'is_complete': False,
            'reason': '无法获取最新数据日期',
            'last_update': None,
            'record_count': total_count
        }

    except Exception as e:
        logger.error(f"检查K线数据完整性失败 {stock_code}: {str(e)}")
        return {
            'is_complete': False,
            'reason': f"数据库检查失败: {str(e)}",
            'last_update': None,
            'record_count': 0
        }


async def check_financial_data_integrity(
    db: AsyncSession,
    stock_code: str
) -> Dict:
    """
    检查财务数据完整性
    
    Args:
        db: 数据库会话
        stock_code: 股票代码
        
    Returns:
        {
            'is_complete': bool,
            'reason': str,
            'last_update': datetime,
            'record_count': int
        }
    """
    try:
        financial_stmt = (
            select(DataUpdateLog)
            .where(
                and_(
                    DataUpdateLog.stock_code == stock_code,
                    DataUpdateLog.data_type == 'financial',
                    DataUpdateLog.status == 'completed'
                )
            )
            .order_by(desc(DataUpdateLog.completed_at))
            .limit(1)
        )
        latest_log = (await db.execute(financial_stmt)).scalars().first()
        
        if latest_log and latest_log.completed_at:
            return {
                'is_complete': True,
                'reason': '财务数据存在',
                'last_update': latest_log.completed_at,
                'record_count': latest_log.records_updated or 0
            }

        return {
            'is_complete': False,
            'reason': '数据库无财务更新记录',
            'last_update': None,
            'record_count': 0
        }

    except Exception as e:
        logger.error(f"检查财务数据完整性失败 {stock_code}: {str(e)}")
        return {
            'is_complete': False,
            'reason': f"数据库检查失败: {str(e)}",
            'last_update': None,
            'record_count': 0
        }


async def check_us_index_data_integrity(
    db: AsyncSession,
    stock_code: str
) -> Dict:
    """
    检查美股指数数据完整性
    
    Args:
        db: 数据库会话
        stock_code: 美股指数代码
        
    Returns:
        {
            'is_complete': bool,
            'reason': str,
            'last_update': datetime,
            'record_count': int
        }
    """
    try:
        stmt = select(USDailyData).where(
            USDailyData.us_stock_code == stock_code
        ).order_by(desc(USDailyData.trade_date)).limit(1)
        
        record = (await db.execute(stmt)).scalars().first()
        
        if record:
            return {
                'is_complete': True,
                'reason': '美股指数存在',
                'last_update': record.created_at,
                'record_count': 1
            }
        
        return {
            'is_complete': False,
            'reason': '数据库无美股指数记录',
            'last_update': None,
            'record_count': 0
        }

    except Exception as e:
        logger.error(f"检查美股指数数据完整性失败 {stock_code}: {str(e)}")
        return {
            'is_complete': False,
            'reason': f"数据库检查失败: {str(e)}",
            'last_update': None,
            'record_count': 0
        }


async def get_update_logs(
    db: AsyncSession,
    stock_code: Optional[str] = None,
    data_type: Optional[str] = None,
    limit: int = 50
) -> List[DataUpdateLog]:
    """
    获取更新日志列表
    
    Args:
        db: 数据库会话
        stock_code: 股票代码（可选）
        data_type: 数据类型（可选）
        limit: 返回记录数限制
        
    Returns:
        更新日志列表
    """
    stmt = select(DataUpdateLog)
    
    if stock_code:
        stmt = stmt.where(DataUpdateLog.stock_code == stock_code)
    
    if data_type:
        stmt = stmt.where(DataUpdateLog.data_type == data_type)
    
    stmt = stmt.order_by(desc(DataUpdateLog.started_at)).limit(limit)
    
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_latest_successful_update(
    db: AsyncSession,
    data_type: Optional[str] = None
) -> Optional[DataUpdateLog]:
    """
    获取最新成功的更新记录
    
    Args:
        db: 数据库会话
        data_type: 数据类型（可选）
        
    Returns:
        最新的成功更新记录或None
    """
    stmt = select(DataUpdateLog).where(
        DataUpdateLog.status == 'completed'
    )
    
    if data_type:
        stmt = stmt.where(DataUpdateLog.data_type == data_type)
    
    stmt = stmt.order_by(desc(DataUpdateLog.completed_at)).limit(1)
    
    result = await db.execute(stmt)
    return result.scalars().first()


async def migrate_stock_code(db: AsyncSession, old_code: str, new_code: str) -> Dict[str, int]:
    """
    Migrate stock code across all related tables (one-time migration operation)

    Args:
        db: Database session
        old_code: Old stock code
        new_code: New stock code

    Returns:
        Dictionary with update counts per table
    """
    from sqlalchemy import text

    results = {}

    # Update K-line data table
    kline_result = await db.execute(
        text("UPDATE stock_kline_data SET stock_code = :new WHERE stock_code = :old"),
        {'new': new_code, 'old': old_code}
    )
    results['kline_count'] = kline_result.rowcount

    # Update fundamental metrics table
    fundamental_result = await db.execute(
        text("UPDATE fundamental_metrics SET stock_code = :new WHERE stock_code = :old"),
        {'new': new_code, 'old': old_code}
    )
    results['fundamental_count'] = fundamental_result.rowcount

    # Update financial history table
    financial_result = await db.execute(
        text("UPDATE financial_history SET stock_code = :new WHERE stock_code = :old"),
        {'new': new_code, 'old': old_code}
    )
    results['financial_count'] = financial_result.rowcount

    # Update stock quotes table
    quote_result = await db.execute(
        text("UPDATE stock_quotes SET stock_code = :new WHERE stock_code = :old"),
        {'new': new_code, 'old': old_code}
    )
    results['quote_count'] = quote_result.rowcount

    # Update force index cache table
    force_result = await db.execute(
        text("UPDATE force_index_cache SET stock_code = :new WHERE stock_code = :old"),
        {'new': new_code, 'old': old_code}
    )
    results['force_count'] = force_result.rowcount

    # Update data update log table
    log_result = await db.execute(
        text("UPDATE data_update_log SET stock_code = :new WHERE stock_code = :old"),
        {'new': new_code, 'old': old_code}
    )
    results['log_count'] = log_result.rowcount

    return results


__all__ = [
    'record_update_start',
    'record_update_complete',
    'get_latest_update_log',
    'check_kline_data_integrity',
    'check_financial_data_integrity',
    'check_us_index_data_integrity',
    'get_update_logs',
    'get_latest_successful_update',
    'migrate_stock_code',
]
