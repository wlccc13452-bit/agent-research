"""Watchlist Operations - 关注列表数据操作

提供关注列表相关的数据库操作：
- 添加股票
- 删除股票
- 更新股票
- 查询关注列表
- 检查是否存在
- 归档/取消归档
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Sequence

from sqlalchemy import select, and_, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import DailyWatchlist

logger = logging.getLogger(__name__)


async def add_to_watchlist(
    db: AsyncSession,
    watch_date: date,
    stock_code: str,
    stock_name: str,
    target_price: Optional[Decimal] = None,
    stop_loss_price: Optional[Decimal] = None,
    reason: Optional[str] = None,
) -> DailyWatchlist:
    """
    添加股票到关注列表
    
    Args:
        db: 数据库会话
        watch_date: 关注日期
        stock_code: 股票代码
        stock_name: 股票名称
        target_price: 目标价（可选）
        stop_loss_price: 止损价（可选）
        reason: 理由（可选）
        
    Returns:
        创建的 DailyWatchlist 对象
    """
    new_watch = DailyWatchlist(
        watch_date=watch_date,
        stock_code=stock_code,
        stock_name=stock_name,
        target_price=target_price,
        stop_loss_price=stop_loss_price,
        reason=reason
    )
    
    db.add(new_watch)
    await db.commit()
    await db.refresh(new_watch)
    
    logger.info(f"[OK] 已添加到关注列表: {stock_name} ({stock_code})")
    return new_watch


async def remove_from_watchlist(
    db: AsyncSession,
    stock_ids: Optional[List[int]] = None,
    watch_date: Optional[date] = None
) -> int:
    """
    从关注列表删除股票

    Args:
        db: 数据库会话
        stock_ids: 股票ID列表(可选)
        watch_date: 删除该日期的所有股票(可选,如果stock_ids为None则使用)

    Returns:
        删除的记录数
    """
    # 构建删除条件
    if stock_ids:
        delete_stmt = delete(DailyWatchlist).where(DailyWatchlist.id.in_(stock_ids))
        logger.info(f"删除关注股票: IDs={stock_ids}")
    elif watch_date:
        delete_stmt = delete(DailyWatchlist).where(DailyWatchlist.watch_date == watch_date)
        logger.info(f"删除关注股票: watch_date={watch_date}")
    else:
        return 0

    result = await db.execute(delete_stmt)
    await db.commit()

    return result.rowcount


async def check_watchlist_exists(
    db: AsyncSession,
    watch_date: date,
    stock_code: str
) -> bool:
    """
    检查股票是否已在关注列表中
    
    Args:
        db: 数据库会话
        watch_date: 关注日期
        stock_code: 股票代码
        
    Returns:
        True 如果存在
    """
    stmt = select(DailyWatchlist).where(
        and_(
            DailyWatchlist.watch_date == watch_date,
            DailyWatchlist.stock_code == stock_code
        )
    )
    
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def get_watchlist_by_date(
    db: AsyncSession,
    watch_date: date,
    include_archived: bool = False
) -> List[DailyWatchlist]:
    """
    获取指定日期的关注列表
    
    Args:
        db: 数据库会话
        watch_date: 关注日期
        include_archived: 是否包含已归档
        
    Returns:
        关注列表
    """
    stmt = select(DailyWatchlist).where(DailyWatchlist.watch_date == watch_date)
    
    if not include_archived:
        stmt = stmt.where(DailyWatchlist.is_archived == False)
    
    stmt = stmt.order_by(DailyWatchlist.created_at.desc())
    
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_all_dates(
    db: AsyncSession,
    include_archived: bool = False
) -> List[date]:
    """
    获取所有关注日期
    
    Args:
        db: 数据库会话
        include_archived: 是否包含已归档
        
    Returns:
        日期列表
    """
    logger.info(f"[WATCHLIST_OPS] Getting all dates, include_archived={include_archived}")
    
    stmt = select(DailyWatchlist.watch_date).distinct()

    if not include_archived:
        stmt = stmt.where(DailyWatchlist.is_archived == False)

    stmt = stmt.order_by(DailyWatchlist.watch_date.desc())
    
    result = await db.execute(stmt)
    dates = [row[0] for row in result.all()]
    
    logger.info(f"[WATCHLIST_OPS] Found {len(dates)} distinct dates: {dates[:5] if dates else 'none'}")
    return dates


async def get_recent_watchlist_stocks(
    db: AsyncSession,
    days: int = 7,
    limit: int = 20
) -> Sequence[DailyWatchlist]:
    """
    获取最近几天的关注股票
    
    Args:
        db: 数据库会话
        days: 天数
        limit: 返回记录数
        
    Returns:
        关注股票列表
    """
    from datetime import timedelta
    
    cutoff_date = date.today() - timedelta(days=days)
    
    stmt = select(DailyWatchlist) \
        .where(DailyWatchlist.watch_date >= cutoff_date) \
        .where(DailyWatchlist.is_archived == False) \
        .order_by(DailyWatchlist.watch_date.desc()) \
        .limit(limit)
    
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_watchlist_by_stock(
    db: AsyncSession,
    stock_code: str,
    stock_name: Optional[str] = None
) -> List[DailyWatchlist]:
    """
    根据股票代码查询关注列表
    
    Args:
        db: 数据库会话
        stock_code: 股票代码
        stock_name: 股票名称（可选，用于进一步筛选）
        
    Returns:
        关注列表记录
    """
    conditions = [DailyWatchlist.stock_code == stock_code]
    
    if stock_name:
        conditions.append(DailyWatchlist.stock_name == stock_name)
    
    stmt = select(DailyWatchlist).where(and_(*conditions))
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_stock_by_id(
    db: AsyncSession,
    stock_id: int
) -> Optional[DailyWatchlist]:
    """
    根据ID获取关注股票
    
    Args:
        db: 数据库会话
        stock_id: 股票ID
        
    Returns:
        关注股票对象或None
    """
    stmt = select(DailyWatchlist).where(DailyWatchlist.id == stock_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_watchlist_stock(
    db: AsyncSession,
    stock_id: int,
    stock_code: Optional[str] = None,
    reason: Optional[str] = None,
    target_price: Optional[Decimal] = None,
    change_up_pct: Optional[Decimal] = None,
    change_down_pct: Optional[Decimal] = None,
    stop_loss_price: Optional[Decimal] = None,
    notes: Optional[str] = None
) -> Optional[DailyWatchlist]:
    """
    更新关注股票信息
    
    Args:
        db: 数据库会话
        stock_id: 股票ID
        stock_code: 股票代码（可选）
        reason: 理由（可选）
        target_price: 目标价（可选）
        change_up_pct: 上涨控制比例（可选）
        change_down_pct: 下跌控制比例（可选）
        stop_loss_price: 止损价（可选）
        notes: 备注（可选）
        
    Returns:
        更新后的关注股票对象或None
    """
    stmt = select(DailyWatchlist).where(DailyWatchlist.id == stock_id)
    result = await db.execute(stmt)
    stock = result.scalar_one_or_none()
    
    if not stock:
        return None
    
    # 更新字段
    if stock_code is not None:
        stock.stock_code = stock_code
    if reason is not None:
        stock.reason = reason
    if target_price is not None:
        stock.target_price = target_price
    if change_up_pct is not None:
        stock.change_up_pct = change_up_pct
    if change_down_pct is not None:
        stock.change_down_pct = change_down_pct
    if stop_loss_price is not None:
        stock.stop_loss_price = stop_loss_price
    if notes is not None:
        stock.notes = notes
    
    stock.updated_at = datetime.now()
    await db.commit()
    await db.refresh(stock)
    
    logger.info(f"更新关注股票: ID={stock_id}")
    return stock


async def archive_watchlist_stocks(
    db: AsyncSession,
    stock_ids: Optional[List[int]] = None,
    watch_date: Optional[date] = None
) -> int:
    """
    归档关注股票
    
    Args:
        db: 数据库会话
        stock_ids: 股票ID列表（可选）
        watch_date: 关注日期（可选，如果未提供stock_ids则使用）
        
    Returns:
        归档的记录数
    """
    if stock_ids:
        stmt = select(DailyWatchlist).where(DailyWatchlist.id.in_(stock_ids))
    elif watch_date:
        stmt = select(DailyWatchlist).where(DailyWatchlist.watch_date == watch_date)
    else:
        return 0
    
    result = await db.execute(stmt)
    stocks = result.scalars().all()
    
    archived_count = 0
    for stock in stocks:
        if stock.is_archived == 0:
            stock.is_archived = 1
            stock.archived_at = datetime.now()
            stock.updated_at = datetime.now()
            archived_count += 1
    
    await db.commit()
    logger.info(f"归档了 {archived_count} 个关注股票")
    return archived_count


async def unarchive_watchlist_stocks(
    db: AsyncSession,
    stock_ids: List[int]
) -> int:
    """
    取消归档关注股票
    
    Args:
        db: 数据库会话
        stock_ids: 股票ID列表
        
    Returns:
        取消归档的记录数
    """
    stmt = select(DailyWatchlist).where(DailyWatchlist.id.in_(stock_ids))
    result = await db.execute(stmt)
    stocks = result.scalars().all()
    
    unarchived_count = 0
    for stock in stocks:
        if stock.is_archived == 1:
            stock.is_archived = 0
            stock.archived_at = None
            stock.updated_at = datetime.now()
            unarchived_count += 1
    
    await db.commit()
    logger.info(f"取消归档了 {unarchived_count} 个关注股票")
    return unarchived_count


async def upsert_watchlist_stock(
    db: AsyncSession,
    watch_date: date,
    stock_code: str,
    stock_name: str,
    target_price: Optional[Decimal] = None,
    stop_loss_price: Optional[Decimal] = None,
    reason: Optional[str] = None,
    notes: Optional[str] = None
) -> DailyWatchlist:
    """
    添加或更新关注股票（如果已存在则更新）
    
    Args:
        db: 数据库会话
        watch_date: 关注日期
        stock_code: 股票代码
        stock_name: 股票名称
        target_price: 目标价（可选）
        stop_loss_price: 止损价（可选）
        reason: 理由（可选）
        notes: 备注（可选）
        
    Returns:
        创建或更新的 DailyWatchlist 对象
    """
    # 检查是否已存在
    stmt = select(DailyWatchlist).where(
        and_(
            DailyWatchlist.stock_code == stock_code,
            DailyWatchlist.watch_date == watch_date
        )
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        # 更新已存在的记录
        existing.reason = reason
        existing.target_price = target_price
        existing.stop_loss_price = stop_loss_price
        existing.notes = notes
        existing.updated_at = datetime.now()
        existing.is_archived = 0
        existing.archived_at = None
        
        await db.commit()
        await db.refresh(existing)
        
        logger.info(f"更新关注股票: {stock_name} ({stock_code})")
        return existing
    else:
        # 创建新记录
        new_watch = DailyWatchlist(
            watch_date=watch_date,
            stock_code=stock_code,
            stock_name=stock_name,
            target_price=target_price,
            stop_loss_price=stop_loss_price,
            reason=reason,
            notes=notes,
            is_archived=0
        )
        
        db.add(new_watch)
        await db.commit()
        await db.refresh(new_watch)
        
        logger.info(f"添加关注股票: {stock_name} ({stock_code})")
        return new_watch


__all__ = [
    'add_to_watchlist',
    'remove_from_watchlist',
    'check_watchlist_exists',
    'get_watchlist_by_date',
    'get_all_dates',
    'get_recent_watchlist_stocks',
    'get_watchlist_by_stock',
    'get_stock_by_id',
    'update_watchlist_stock',
    'archive_watchlist_stocks',
    'unarchive_watchlist_stocks',
    'upsert_watchlist_stock',
]
