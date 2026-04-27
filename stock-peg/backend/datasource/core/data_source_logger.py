"""数据源日志记录器 - 集成到现有log系统"""
import logging

from datasource.core.constants import FunctionType, DataSourceType
from datasource.core.statistics import CallStatus

logger = logging.getLogger(__name__)


class DataSourceLogger:
    """数据源日志记录器 — 集成 debug_log_manager + log_service"""

    def start_call(self, function_type, source_type, method, args=None, kwargs=None) -> str:
        try:
            from services.debug_log_manager import debug_log_manager
            return debug_log_manager.start_task(
                task_type='data_source_call',
                task_name=f"{source_type.value}.{method}",
                metadata={
                    'function_type': function_type.name,
                    'source_type': source_type.value,
                    'method': method,
                },
            )
        except Exception:
            return f"ds_{function_type.name}_{source_type.value}_{id(self)}"

    def log_success(self, task_id, result, duration_ms):
        try:
            from services.debug_log_manager import debug_log_manager
            result_info = {}
            if result is not None and hasattr(result, '__len__'):
                result_info['result_count'] = len(result)
            debug_log_manager.log_event(task_id, 'call_success', {**result_info, 'duration_ms': round(duration_ms, 2)})
            debug_log_manager.end_task(task_id, success=True)
        except Exception:
            pass

    def log_failure(self, task_id, error, status, duration_ms):
        try:
            from services.debug_log_manager import debug_log_manager
            debug_log_manager.log_event(task_id, 'call_failure', {'error': error, 'status': status.value, 'duration_ms': round(duration_ms, 2)})
            debug_log_manager.end_task(task_id, success=False, error=error)
        except Exception:
            pass

    def log_retry(self, task_id, from_source, to_source, reason):
        try:
            from services.debug_log_manager import debug_log_manager
            debug_log_manager.log_event(task_id, 'source_retry', {
                'from_source': from_source.value, 'to_source': to_source.value, 'reason': reason,
            })
        except Exception:
            pass


data_source_logger = DataSourceLogger()
