"""快速K线API - 优先返回数据库数据，后台异步更新"""
from fastapi import APIRouter, HTTPException, Query, Depends
import logging
import time
from sqlalchemy.ext.asyncio import AsyncSession

from services.stock_data_service import stock_data_service
from services.data_update_manager import data_update_manager
from services.background_updater import background_updater
from services.stock_loading_logger import stock_loading_logger
from database.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/kline-db-fast/{stock_code}")
async def get_kline_fast(
    stock_code: str,
    period: str = Query("day", description="K线周期: day/week/month"),
    count: int = Query(100, description="K线数量", ge=1, le=500),
    quick_load: bool = Query(False, description="快速加载模式：只返回最近60条数据"),
    local_only: bool = Query(False, description="仅返回本地可用数据，不等待更新检查"),
    session_id: str = Query(None, description="前端传递的会话ID"),
    db: AsyncSession = Depends(get_db)
):
    """快速获取K线数据
    
    优先返回数据库数据，如果需要更新则后台异步更新
    
    快速加载模式（quick_load=true）：
    - 优先返回最近60条数据（约3个月）
    - 后台继续更新更多历史数据
    - 适合首次加载，快速响应用户
    
    Returns:
        {
            'data': [...],  # K线数据
            'local_data_available': bool,  # 是否有本地数据可直接返回
            'is_updating': bool,  # 是否正在后台更新
            'task_id': str | None,  # 任务ID
            'last_update': str | None,  # 数据库更新时间
            'last_data_date': str | None,  # 最新数据日期
            'update_reason': str | None,  # 更新原因
            'session_id': str,  # 会话ID
            'quick_load': bool,  # 是否快速加载模式
            'actual_count': int  # 实际返回的数据数量
        }
    """
    # 快速加载模式：优先返回最近数据
    actual_count = 100 if quick_load else count
    
    # 如果没有session_id，创建一个新的会话
    if not session_id:
        session_id = stock_loading_logger.start_session(stock_code, "api_direct")
    else:
        # 记录API接收事件
        stock_loading_logger.log_event(
            session_id,
            'backend_api_received',
            'backend',
            {'stock_code': stock_code, 'period': period, 'count': actual_count, 'quick_load': quick_load}
        )
    
    try:
        # 1. 直接从数据库获取数据 (核心优化：先取数据，后查更新)
        step_start = time.time()
        klines = await stock_data_service.get_kline_from_db(db, stock_code, period, actual_count)
        db_query_duration = (time.time() - step_start) * 1000
        
        stock_loading_logger.log_event(
            session_id,
            'backend_db_query',
            'backend',
            {'count': len(klines), 'period': period, 'actual_count': actual_count},
            duration_ms=db_query_duration
        )
        
        # 2. 准备响应数据
        response = {
            'data': [],
            'local_data_available': False,
            'is_updating': False,
            'task_id': None,
            'last_update': None,
            'last_data_date': None,
            'update_reason': None,
            'session_id': session_id,
            'quick_load': quick_load,
            'actual_count': actual_count
        }

        if klines:
            response['local_data_available'] = True
            response['data'] = [
                {
                    'code': k.code,
                    'date': k.date,
                    'open': float(k.open),
                    'close': float(k.close),
                    'high': float(k.high),
                    'low': float(k.low),
                    'volume': int(k.volume) if k.volume else 0,
                    'amount': float(k.amount) if k.amount else 0.0
                }
                for k in klines
            ]
            response['last_data_date'] = klines[-1].date if klines else None

        if local_only:
            stock_loading_logger.log_event(
                session_id,
                'backend_api_response',
                'backend',
                {
                    'local_data_available': response['local_data_available'],
                    'data_count': len(response['data']),
                    'is_updating': False
                }
            )
            stock_loading_logger.end_session(
                session_id,
                success=True,
                error=None
            )
            return response
        
        # 3. 检查更新必要性 (核心优化：不阻塞主流程，直接异步检查)
        # 注意：这里我们不再调用 await check_update_necessity，而是直接启动异步任务
        # 如果数据库有数据，我们直接返回现有数据，并在后台检查/更新
        # 如果数据库无数据，我们在后台启动更新任务
        
        if klines:
            # 数据库有数据，异步检查是否需要更新
            import asyncio
            asyncio.create_task(background_updater.submit_kline_update_task(stock_code, period, force=False))
            
            # 填充响应中关于更新的信息（因为是异步，所以这里设为 False/None）
            response['is_updating'] = False # 实际上可能正在更新，但为了让前端不等待，我们返回 False
            response['update_reason'] = "后台自动检查更新"
            
            stock_loading_logger.log_event(
                session_id,
                'backend_async_update_triggered',
                'backend',
                {'stock_code': stock_code, 'reason': '有数据，异步检查更新'}
            )
        else:
            # 数据库无数据，提交后台任务
            task_start = time.time()
            task_result = await background_updater.submit_kline_update_task(
                stock_code, period, force=False
            )
            task_duration = (time.time() - task_start) * 1000

            if task_result['success']:
                response['is_updating'] = True
                response['task_id'] = task_result['task_id']
                response['update_reason'] = '数据库无数据，已提交后台异步更新任务'
                stock_loading_logger.log_event(
                    session_id,
                    'backend_background_task_submitted',
                    'backend',
                    {
                        'task_id': task_result['task_id'],
                        'reason': response['update_reason']
                    },
                    duration_ms=task_duration
                )
            else:
                response['update_reason'] = task_result.get('message') or '后台更新任务提交失败'
                stock_loading_logger.log_event(
                    session_id,
                    'backend_background_task_failed',
                    'backend',
                    {'error': response['update_reason']},
                    duration_ms=task_duration
                )
        
        # 记录API响应事件
        stock_loading_logger.log_event(
            session_id,
            'backend_api_response',
            'backend',
            {
                'local_data_available': response['local_data_available'],
                'data_count': len(response['data']),
                'is_updating': response['is_updating']
            }
        )
        
        # 结束会话并保存日志
        stock_loading_logger.end_session(
            session_id, 
            success=True, 
            error=None
        )
        
        return response
        
    except Exception as e:
        logger.error(f"获取快速K线数据失败 {stock_code}: {str(e)}", exc_info=True)
        stock_loading_logger.log_event(
            session_id,
            'backend_error',
            'backend',
            {'error': str(e)}
        )
        
        # 结束会话（标记为失败）
        stock_loading_logger.end_session(
            session_id, 
            success=False, 
            error=str(e)
        )
        
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/kline-status/{stock_code}")
async def get_kline_update_status(stock_code: str):
    """获取K线数据更新状态"""
    try:
        # 检查是否有正在运行的任务
        running_tasks = [
            tid for tid, status in background_updater.task_status.items()
            if status.get('stock_code') == stock_code and status.get('status') == 'running'
        ]
        
        # 检查更新必要性
        check_result = await data_update_manager.check_update_necessity(stock_code, 'kline')
        
        return {
            'stock_code': stock_code,
            'needs_update': check_result['needs_update'],
            'is_updating': len(running_tasks) > 0,
            'task_ids': running_tasks,
            'last_update': check_result.get('last_update'),
            'reason': check_result['reason']
        }
        
    except Exception as e:
        logger.error(f"获取K线更新状态失败 {stock_code}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/end")
async def end_session(
    session_id: str = Query(..., description="会话ID"),
    success: bool = Query(True, description="是否成功"),
    error: str = Query(None, description="错误信息")
):
    """结束会话并保存日志
    
    前端可以调用此API通知后端结束会话并保存日志
    """
    try:
        stock_loading_logger.end_session(session_id, success, error)
        return {
            'status': 'ok', 
            'session_id': session_id,
            'message': '会话已结束并保存'
        }
    except Exception as e:
        logger.error(f"结束会话失败: {str(e)}")
        return {
            'status': 'error', 
            'message': str(e)
        }
