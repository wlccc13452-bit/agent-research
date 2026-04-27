"""Report Operations - 报告数据操作

提供报告相关的数据库操作：
- 保存报告
- 查询报告
- 更新预测验证
"""

import logging
from datetime import date
from typing import Optional, List, Dict

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import DailyReport

logger = logging.getLogger(__name__)


async def get_daily_report(
    db: AsyncSession,
    stock_code: str,
    report_date: date
) -> Optional[DailyReport]:
    """
    获取单个报告
    
    Args:
        db: 数据库会话
        stock_code: 股票代码
        report_date: 报告日期
        
    Returns:
        报告对象或None
    """
    stmt = select(DailyReport).where(
        and_(
            DailyReport.stock_code == stock_code,
            DailyReport.report_date == report_date
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_daily_reports(
    db: AsyncSession,
    start_date: date,
    end_date: date,
    stock_code: Optional[str] = None
) -> List[DailyReport]:
    """
    获取报告列表
    
    Args:
        db: 数据库会话
        start_date: 开始日期
        end_date: 结束日期
        stock_code: 股票代码（可选）
        
    Returns:
        报告列表
    """
    stmt = select(DailyReport).where(
        DailyReport.report_date >= start_date,
        DailyReport.report_date <= end_date
    )
    
    if stock_code:
        stmt = stmt.where(DailyReport.stock_code == stock_code)
    
    stmt = stmt.order_by(DailyReport.report_date.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


async def update_prediction_verification(
    db: AsyncSession,
    stock_code: str,
    report_date: date,
    actual_direction: str,
    actual_change_pct: float,
    is_correct: int
) -> bool:
    """
    更新预测验证结果
    
    Args:
        db: 数据库会话
        stock_code: 股票代码
        report_date: 报告日期
        actual_direction: 实际方向
        actual_change_pct: 实际涨跌幅
        is_correct: 是否预测正确 (1/0)
        
    Returns:
        是否更新成功
    """
    # 查询报告
    report = await get_daily_report(db, stock_code, report_date)
    
    if not report:
        logger.warning(f"报告不存在: {stock_code} {report_date}")
        return False
    
    # 更新验证字段
    report.actual_direction = actual_direction
    report.actual_change_pct = actual_change_pct
    report.is_correct = is_correct
    
    await db.commit()
    logger.info(f"更新预测验证: {stock_code} {report_date} - {actual_direction}")
    return True


async def save_daily_report(
    db: AsyncSession,
    report_data: Dict
) -> DailyReport:
    """
    保存报告到数据库
    
    Args:
        db: 数据库会话
        report_data: 报告数据字典
        
    Returns:
        创建的报告对象
    """
    report = DailyReport(**report_data)
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    logger.info(f"保存报告: {report_data.get('stock_code')} {report_data.get('report_date')}")
    return report


async def get_reports_for_training(
    db: AsyncSession,
    days: int = 365
) -> List[DailyReport]:
    """
    获取用于模型训练的报告数据（必须有验证结果）
    
    Args:
        db: 数据库会话
        days: 使用最近多少天的数据
        
    Returns:
        带验证结果的报告列表
    """
    try:
        from datetime import timedelta
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        stmt = select(DailyReport).where(
            DailyReport.report_date >= start_date,
            DailyReport.report_date <= end_date,
            DailyReport.actual_direction.isnot(None)  # 只使用有验证结果的数据
        ).order_by(DailyReport.report_date)
        
        result = await db.execute(stmt)
        return result.scalars().all()
        
    except Exception as e:
        logger.error(f"获取训练数据失败: {str(e)}")
        return []


__all__ = [
    'get_daily_report',
    'get_daily_reports',
    'update_prediction_verification',
    'save_daily_report',
    'get_reports_for_training',
]
