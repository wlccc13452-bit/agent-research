"""数据更新管理API"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from database.operations import (
    get_update_logs,
    get_latest_successful_update,
)
from services.data_update_manager import data_update_manager
from services.background_updater import background_updater
from services.fundamental_analyzer import FundamentalAnalyzer
from routers.holding import holding_manager

logger = logging.getLogger(__name__)

router = APIRouter()
fundamental_analyzer = FundamentalAnalyzer()


async def _collect_holding_stock_codes():
    holdings = await holding_manager.load_holdings()
    stock_codes = []
    if holdings and holdings.sectors:
        for sector in holdings.sectors:
            for stock in sector.stocks:
                if stock.code and not stock.code.startswith('UNKNOWN'):
                    stock_codes.append(stock.code)
    return stock_codes


async def _update_financial_data(stock_code: str, force: bool = False) -> bool:
    if not force:
        check_result = await data_update_manager.check_update_necessity(stock_code, 'financial')
        if not check_result.get('needs_update'):
            return False
    log_id = await data_update_manager.record_update_start(
        stock_code,
        'financial',
        'force' if force else 'auto'
    )
    try:
        annual_report = await fundamental_analyzer.get_annual_report(stock_code)
        fundamental_result = await fundamental_analyzer.analyze_fundamental(stock_code)
        success = bool(annual_report) or bool(fundamental_result)
        await data_update_manager.record_update_complete(
            log_id,
            1 if success else 0,
            None if success else '财务数据更新未返回有效结果'
        )
        return success
    except Exception as e:
        await data_update_manager.record_update_complete(log_id, 0, str(e))
        logger.error(f"更新财务数据失败 {stock_code}: {str(e)}")
        return False


@router.get("/status-all")
async def get_all_update_status():
    """获取所有股票和指数的数据更新状态
    
    Returns:
        {
            'needs_update_count': int,
            'last_global_update': str,
            'stocks': [...],
            'us_indices': [...]
        }
    """
    try:
        # 1. 收集持仓股票代码
        stock_codes = await _collect_holding_stock_codes()
        
        # 2. 并行检查股票状态 (使用 asyncio.gather 提高效率)
        import asyncio
        
        async def check_stock_status(stock_code):
            kline_status = await data_update_manager.check_update_necessity(stock_code, 'kline')
            financial_status = await data_update_manager.check_update_necessity(stock_code, 'financial')
            
            needs_update = kline_status['needs_update'] or financial_status['needs_update']
            
            kline_last = kline_status.get('last_update')
            financial_last = financial_status.get('last_update')
            latest_update = max(
                [d for d in [kline_last, financial_last] if d is not None],
                default=None
            )
            
            reasons = []
            if kline_status['needs_update']:
                reasons.append(f"K线: {kline_status['reason']}")
            if financial_status['needs_update']:
                reasons.append(f"财务: {financial_status['reason']}")
            
            if not reasons:
                reasons.append("数据均为最新")
                
            return {
                'stock_code': stock_code,
                'needs_update': needs_update,
                'last_update': latest_update,
                'reason': "；".join(reasons)
            }

        # 3. 并行检查美股指数状态
        us_indices_list = ['^GSPC', '^IXIC', '^DJI', '^VIX']
        
        async def check_us_index_status(symbol):
            status = await data_update_manager.check_update_necessity(symbol, 'us_index')
            return {
                'symbol': symbol,
                'needs_update': status['needs_update'],
                'last_update': status.get('last_update'),
                'reason': status.get('reason', '需要更新')
            }

        # 4. 执行并行任务
        stock_tasks = [check_stock_status(code) for code in stock_codes]
        us_index_tasks = [check_us_index_status(symbol) for symbol in us_indices_list]
        
        all_results = await asyncio.gather(*stock_tasks, *us_index_tasks)
        
        # 5. 处理结果
        stocks = all_results[:len(stock_codes)]
        us_indices_status = all_results[len(stock_codes):]
        
        needs_update_count = sum(1 for item in all_results if item['needs_update'])
        
        # 提取最后更新时间
        all_updates = [item.get('last_update') for item in all_results if item.get('last_update')]
        last_global_update = max(all_updates) if all_updates else None
                
        return {
            'needs_update_count': needs_update_count,
            'last_global_update': last_global_update,
            'stocks': stocks,
            'us_indices': us_indices_status
        }
        
    except Exception as e:
        logger.error(f"获取所有更新状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{stock_code}")
async def get_stock_update_status(stock_code: str):
    """获取单个股票的更新状态"""
    try:
        status = await data_update_manager.check_update_necessity(stock_code, 'kline')
        return {
            'stock_code': stock_code,
            **status
        }
    except Exception as e:
        logger.error(f"获取股票更新状态失败 {stock_code}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/force-update")
async def force_update(data: dict):
    """强制更新股票和指数数据 (已禁用客户端主动触发)
    
    由服务器在数据缺失时自动触发后台更新。
    """
    logger.warning("客户端尝试触发强制更新，该操作已被禁用。所有更新由服务器后台自动处理。")
    return {
        'success': False,
        'message': "手动更新已禁用。服务器将根据需要自动在后台同步数据并通过WebSocket推送。",
        'financial_updated_count': 0,
        'financial_skipped_count': 0,
        'kline_submitted_count': 0,
        'us_index_submitted_count': 0
    }


@router.post("/force-update/{stock_code}")
async def force_update_single(stock_code: str, period: str = Query('day')):
    """强制更新单个股票数据 (已禁用客户端主动触发)"""
    logger.warning(f"客户端尝试触发单股强制更新({stock_code})，该操作已被禁用。")
    return {
        'success': False,
        'message': "手动更新已禁用。服务器将自动处理数据同步。",
        'financial_updated': False
    }


@router.get("/tasks")
async def get_all_tasks():
    """获取所有后台任务状态"""
    try:
        tasks = background_updater.get_all_tasks()
        running_count = background_updater.get_running_tasks_count()
        
        return {
            'total_count': len(tasks),
            'running_count': running_count,
            'tasks': [
                {
                    'task_id': tid,
                    **status
                }
                for tid, status in tasks.items()
            ]
        }
        
    except Exception as e:
        logger.error(f"获取任务状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """获取指定任务状态"""
    try:
        status = background_updater.get_task_status(task_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return {
            'task_id': task_id,
            **status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态失败 {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tasks/{task_id}")
async def cancel_task(task_id: str):
    """取消任务"""
    try:
        success = await background_updater.cancel_task(task_id)
        
        return {
            'success': success,
            'message': '任务已取消' if success else '任务无法取消'
        }
        
    except Exception as e:
        logger.error(f"取消任务失败 {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs")
async def get_update_logs(
    stock_code: Optional[str] = Query(None, description="股票代码"),
    data_type: Optional[str] = Query(None, description="数据类型"),
    limit: int = Query(20, description="返回数量", ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取更新日志"""
    try:
        # Get logs using ops layer
        logs = await get_update_logs(db, stock_code, data_type, limit)
        
        return {
            'total': len(logs),
            'logs': [
                {
                    'id': log.id,
                    'stock_code': log.stock_code,
                    'data_type': log.data_type,
                    'update_type': log.update_type,
                    'started_at': log.started_at.isoformat() if log.started_at else None,
                    'completed_at': log.completed_at.isoformat() if log.completed_at else None,
                    'status': log.status,
                    'records_updated': log.records_updated,
                    'error_message': log.error_message
                }
                for log in logs
            ]
        }
        
    except Exception as e:
        logger.error(f"获取更新日志失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/latest")
async def get_latest_update_time(db: AsyncSession = Depends(get_db)):
    """获取最后更新时间"""
    try:
        # Get latest successful update using ops layer
        latest_log = await get_latest_successful_update(db)
        
        if latest_log:
            return {
                'last_update': latest_log.completed_at.isoformat(),
                'stock_code': latest_log.stock_code,
                'data_type': latest_log.data_type
            }
        else:
            return {
                'last_update': None,
                'stock_code': None,
                'data_type': None
            }
        
    except Exception as e:
        logger.error(f"获取最后更新时间失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
