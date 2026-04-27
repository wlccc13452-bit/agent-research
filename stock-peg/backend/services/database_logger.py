"""数据库操作日志记录器"""
import logging
import time
from typing import Optional, Dict, Any, Callable
from functools import wraps
from contextlib import asynccontextmanager

from services.debug_log_manager import debug_log_manager

logger = logging.getLogger(__name__)


class DatabaseLogger:
    """数据库操作日志记录器
    
    将数据库操作记录到 debug-log 目录，而不是输出到控制台
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseLogger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        logger.info("数据库日志记录器已初始化")
    
    def start_db_operation(
        self,
        operation_type: str,
        operation_name: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        silent: bool = True
    ) -> str:
        """
        开始数据库操作日志记录
        
        Args:
            operation_type: 操作类型（如 'query', 'insert', 'update', 'delete'）
            operation_name: 操作名称（可选）
            metadata: 操作元数据（可选）
            silent: 是否不输出到控制台（默认True，数据库操作较多，默认静默）
            
        Returns:
            task_id: 任务ID
        """
        task_id = debug_log_manager.start_task(
            task_type=f'db_{operation_type}',
            task_name=operation_name or operation_type,
            metadata=metadata,
            silent=silent
        )
        return task_id
    
    def log_db_event(
        self,
        task_id: str,
        event_type: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """记录数据库事件"""
        debug_log_manager.log_event(task_id, event_type, data)
    
    def log_db_query(
        self,
        task_id: str,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None
    ):
        """记录数据库查询"""
        debug_log_manager.log_event(
            task_id,
            'db_query',
            {
                'query': query,
                'params': params,
                'duration_ms': duration_ms
            }
        )
    
    def log_db_result(
        self,
        task_id: str,
        affected_rows: int = 0,
        duration_ms: Optional[float] = None
    ):
        """记录数据库操作结果"""
        debug_log_manager.log_event(
            task_id,
            'db_result',
            {
                'affected_rows': affected_rows,
                'duration_ms': duration_ms
            }
        )
    
    def end_db_operation(
        self,
        task_id: str,
        success: bool = True,
        error: Optional[str] = None
    ):
        """结束数据库操作"""
        debug_log_manager.end_task(task_id, success=success, error=error)
    
    @asynccontextmanager
    async def db_operation_context(
        self,
        operation_type: str,
        operation_name: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        silent: bool = True
    ):
        """
        数据库操作上下文管理器
        """
        task_id = self.start_db_operation(operation_type, operation_name, metadata, silent=silent)
        start_time = time.time()
        try:
            yield task_id
            duration_ms = (time.time() - start_time) * 1000
            self.log_db_event(task_id, 'operation_complete', {'duration_ms': duration_ms})
            self.end_db_operation(task_id, success=True)
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.log_db_event(task_id, 'operation_error', {
                'error': str(e),
                'duration_ms': duration_ms
            })
            self.end_db_operation(task_id, success=False, error=str(e))
            raise


def log_db_operation(operation_type: str, operation_name: str = "", silent: bool = True):
    """
    数据库操作日志装饰器
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            task_id = debug_log_manager.start_task(
                task_type=f'db_{operation_type}',
                task_name=operation_name or func.__name__,
                metadata={
                    'function': func.__name__,
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys())
                },
                silent=silent
            )
            
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                # 记录结果信息
                result_info = {}
                if hasattr(result, '__len__'):
                    result_info['result_count'] = len(result)
                elif result is not None:
                    result_info['result_type'] = type(result).__name__
                
                debug_log_manager.log_event(
                    task_id,
                    'operation_complete',
                    {
                        'duration_ms': duration_ms,
                        **result_info
                    }
                )
                
                debug_log_manager.end_task(task_id, success=True)
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                debug_log_manager.log_event(
                    task_id,
                    'operation_error',
                    {
                        'error': str(e),
                        'error_type': type(e).__name__,
                        'duration_ms': duration_ms
                    }
                )
                debug_log_manager.end_task(task_id, success=False, error=str(e))
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            task_id = debug_log_manager.start_task(
                task_type=f'db_{operation_type}',
                task_name=operation_name or func.__name__,
                metadata={
                    'function': func.__name__,
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys())
                },
                silent=silent
            )
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                # 记录结果信息
                result_info = {}
                if hasattr(result, '__len__'):
                    result_info['result_count'] = len(result)
                elif result is not None:
                    result_info['result_type'] = type(result).__name__
                
                debug_log_manager.log_event(
                    task_id,
                    'operation_complete',
                    {
                        'duration_ms': duration_ms,
                        **result_info
                    }
                )
                
                debug_log_manager.end_task(task_id, success=True)
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                debug_log_manager.log_event(
                    task_id,
                    'operation_error',
                    {
                        'error': str(e),
                        'error_type': type(e).__name__,
                        'duration_ms': duration_ms
                    }
                )
                debug_log_manager.end_task(task_id, success=False, error=str(e))
                raise
        
        # 根据函数类型返回不同的wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# 全局单例
db_logger = DatabaseLogger()
