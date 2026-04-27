"""Price Alert Operations - 价格预警数据操作

提供价格预警相关的数据库操作：
- 创建预警
- 查询预警（单个/批量/激活）
- 更新预警（停止监控/触发状态/价格更新）
- 删除预警
- 修改阈值
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import PriceAlert

logger = logging.getLogger(__name__)


async def create_price_alert(
    db: AsyncSession,
    stock_code: str,
    stock_name: str,
    base_price: Decimal,
    current_price: Decimal,
    current_change_pct: Decimal,
    feishu_chat_id: str,
    target_price: Optional[Decimal] = None,
    change_up_pct: Optional[Decimal] = None,
    change_down_pct: Optional[Decimal] = None,
    notes: Optional[str] = None,
) -> PriceAlert:
    """
    创建价格预警记录
    
    Args:
        db: 数据库会话
        stock_code: 股票代码
        stock_name: 股票名称
        base_price: 基准价格
        current_price: 当前价格
        current_change_pct: 当前涨跌幅
        feishu_chat_id: 飞书聊天ID
        target_price: 目标价格（可选）
        change_up_pct: 上涨预警百分比（可选）
        change_down_pct: 下跌预警百分比（可选）
        notes: 备注（可选）
        
    Returns:
        创建的 PriceAlert 对象
    """
    alert = PriceAlert(
        stock_code=stock_code,
        stock_name=stock_name,
        base_price=base_price,
        target_price=target_price,
        change_up_pct=change_up_pct,
        change_down_pct=change_down_pct,
        current_price=current_price,
        current_change_pct=current_change_pct,
        is_active=1,
        is_triggered=0,
        feishu_chat_id=feishu_chat_id,
        notes=notes
    )
    
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    
    logger.info(f"[OK] 价格预警已创建: {stock_name} ({stock_code}), ID={alert.id}")
    return alert


async def stop_alert_monitoring(db: AsyncSession, alert_id: int) -> bool:
    """
    停止价格监控
    
    Args:
        db: 数据库会话
        alert_id: 预警ID
        
    Returns:
        是否成功
    """
    stmt = (
        update(PriceAlert)
        .where(PriceAlert.id == alert_id)
        .values(is_active=0)
    )
    await db.execute(stmt)
    await db.commit()
    
    logger.info(f"[OK] 监控已停止 (ID: {alert_id})")
    return True


async def get_alert_by_id(db: AsyncSession, alert_id: int) -> Optional[PriceAlert]:
    """
    根据ID获取预警记录
    
    Args:
        db: 数据库会话
        alert_id: 预警ID
        
    Returns:
        PriceAlert 对象或 None
    """
    stmt = select(PriceAlert).where(PriceAlert.id == alert_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def adjust_alert_threshold(
    db: AsyncSession,
    alert_id: int,
    adjustment_pct: Decimal
) -> tuple[bool, list[str]]:
    """
    调整预警阈值
    
    Args:
        db: 数据库会话
        alert_id: 预警ID
        adjustment_pct: 调整幅度（百分比）
        
    Returns:
        (是否成功, 更新字段列表)
    """
    alert = await get_alert_by_id(db, alert_id)
    if not alert:
        return False, []
    
    updated_fields = []
    
    # 调整上涨预警
    if alert.change_up_pct:
        new_up = float(alert.change_up_pct) + float(adjustment_pct)
        alert.change_up_pct = Decimal(str(round(new_up, 2)))
        updated_fields.append(f"上涨预警: {alert.change_up_pct:+.2f}%")
    
    # 调整下跌预警
    if alert.change_down_pct:
        new_down = float(alert.change_down_pct) + float(adjustment_pct)
        alert.change_down_pct = Decimal(str(round(new_down, 2)))
        updated_fields.append(f"下跌预警: {alert.change_down_pct:+.2f}%")
    
    # 重置触发状态
    alert.is_triggered = 0
    alert.triggered_at = None
    
    await db.commit()
    
    logger.info(f"[OK] 阈值已调整 (ID: {alert_id}): {', '.join(updated_fields)}")
    return True, updated_fields


async def get_alerts(
    db: AsyncSession,
    active_only: bool = True,
    stock_code: Optional[str] = None
) -> List[PriceAlert]:
    """
    获取预警列表
    
    Args:
        db: 数据库会话
        active_only: 仅返回激活的预警
        stock_code: 按股票代码筛选（可选）
        
    Returns:
        预警列表
    """
    query = select(PriceAlert)
    
    conditions = []
    if active_only:
        conditions.append(PriceAlert.is_active == 1)
    if stock_code:
        conditions.append(PriceAlert.stock_code == stock_code)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(PriceAlert.created_at.desc())
    
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    return list(alerts)


async def get_active_alerts(db: AsyncSession) -> List[PriceAlert]:
    """
    获取所有激活且未触发的预警
    
    Args:
        db: 数据库会话
        
    Returns:
        激活的预警列表
    """
    query = select(PriceAlert).where(
        and_(
            PriceAlert.is_active == 1,
            PriceAlert.is_triggered == 0
        )
    )
    
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    return list(alerts)


async def update_alert_price(
    db: AsyncSession,
    alert_id: int,
    current_price: Decimal,
    current_change_pct: Decimal
) -> bool:
    """
    更新预警的当前价格
    
    Args:
        db: 数据库会话
        alert_id: 预警ID
        current_price: 当前价格
        current_change_pct: 当前涨跌幅
        
    Returns:
        是否成功
    """
    stmt = (
        update(PriceAlert)
        .where(PriceAlert.id == alert_id)
        .values(
            current_price=current_price,
            current_change_pct=current_change_pct
        )
    )
    await db.execute(stmt)
    # 不提交，由调用者决定提交时机
    return True


async def trigger_alert(
    db: AsyncSession,
    alert_id: int,
    trigger_reason: str,
    current_price: Optional[Decimal] = None,
    current_change_pct: Optional[Decimal] = None,
    feishu_notified: int = 1
) -> bool:
    """
    触发预警（标记为已触发状态）
    
    Args:
        db: 数据库会话
        alert_id: 预警ID
        trigger_reason: 触发原因
        current_price: 当前价格（可选，用于更新）
        current_change_pct: 当前涨跌幅（可选，用于更新）
        feishu_notified: 是否已发送飞书通知
        
    Returns:
        是否成功
    """
    now = datetime.now()
    
    values = {
        "is_triggered": 1,
        "triggered_at": now,
        "last_triggered_at": now,
        "trigger_reason": trigger_reason,
        "feishu_notified": feishu_notified
    }
    
    if current_price is not None:
        values["current_price"] = current_price
    if current_change_pct is not None:
        values["current_change_pct"] = current_change_pct
    
    stmt = (
        update(PriceAlert)
        .where(PriceAlert.id == alert_id)
        .values(**values)
    )
    await db.execute(stmt)
    # 不提交，由调用者决定提交时机
    return True


async def increment_trigger_count(db: AsyncSession, alert_id: int) -> bool:
    """
    增加触发次数计数
    
    Args:
        db: 数据库会话
        alert_id: 预警ID
        
    Returns:
        是否成功
    """
    alert = await get_alert_by_id(db, alert_id)
    if not alert:
        return False
    
    alert.triggered_count = (alert.triggered_count or 0) + 1
    alert.last_triggered_at = datetime.now()
    # 不提交，由调用者决定提交时机
    return True


async def deactivate_alert(db: AsyncSession, alert_id: int) -> bool:
    """
    停用预警（软删除）
    
    Args:
        db: 数据库会话
        alert_id: 预警ID
        
    Returns:
        是否成功
    """
    stmt = (
        update(PriceAlert)
        .where(PriceAlert.id == alert_id)
        .values(is_active=0)
    )
    await db.execute(stmt)
    await db.commit()
    
    logger.info(f"[OK] 预警已停用 (ID: {alert_id})")
    return True


async def delete_alert(db: AsyncSession, alert_id: int) -> bool:
    """
    删除预警（硬删除）
    
    Args:
        db: 数据库会话
        alert_id: 预警ID
        
    Returns:
        是否成功
    """
    alert = await get_alert_by_id(db, alert_id)
    if not alert:
        return False
    
    await db.delete(alert)
    await db.commit()
    
    logger.info(f"[OK] 预警已删除 (ID: {alert_id})")
    return True


async def reset_alert_trigger(db: AsyncSession, alert_id: int) -> bool:
    """
    重置预警触发状态（允许再次触发）
    
    Args:
        db: 数据库会话
        alert_id: 预警ID
        
    Returns:
        是否成功
    """
    stmt = (
        update(PriceAlert)
        .where(PriceAlert.id == alert_id)
        .values(is_triggered=0, triggered_at=None)
    )
    await db.execute(stmt)
    await db.commit()
    
    logger.info(f"[OK] 预警触发状态已重置 (ID: {alert_id})")
    return True
