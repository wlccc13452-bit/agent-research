"""任务级别日志管理器 - 将详细日志输出到文件而非控制台"""
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import threading
from contextlib import contextmanager


class DebugLogManager:
    """任务级别日志管理器
    
    将每个任务的详细日志输出到独立文件，减少控制台噪音
    日志位置: backend/logs/debug-log/{task_type}_{timestamp}.log
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DebugLogManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.logs_dir = Path(__file__).parent.parent / "logs" / "debug-log"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # 当前活跃任务 {task_id: {task_type, log_file, events, start_time}}
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.task_lock = threading.Lock()
        
        # 简化的控制台日志器
        self.console_logger = logging.getLogger(__name__)
        
        self._initialized = True
        self.console_logger.info(f"任务日志管理器已初始化，日志目录: {self.logs_dir}")
    
    def start_task(
        self, 
        task_type: str, 
        task_name: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        silent: bool = False
    ) -> str:
        """
        开始一个新任务的日志记录
        
        Args:
            task_type: 任务类型（如 'api_request', 'data_update', 'report_gen'）
            task_name: 任务名称（可选）
            metadata: 任务元数据（可选）
            silent: 是否不输出到控制台（默认False）
            
        Returns:
            task_id: 任务ID，用于后续日志记录
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        task_id = f"{task_type}_{timestamp}"
        
        with self.task_lock:
            self.active_tasks[task_id] = {
                'task_type': task_type,
                'task_name': task_name or task_type,
                'start_time': datetime.now(),
                'metadata': metadata or {},
                'events': [],
                'silent': silent
            }
        
        # 记录任务开始
        self.log_event(task_id, 'task_start', {
            'task_type': task_type,
            'task_name': task_name,
            'metadata': metadata
        })
        
        # 控制台只输出简要信息
        if not silent:
            self.console_logger.info(f"[{task_type}] 任务开始: {task_name or task_id}")
        
        return task_id
    
    def log_event(
        self, 
        task_id: str, 
        event_type: str, 
        data: Optional[Dict[str, Any]] = None
    ):
        """
        记录任务事件
        
        Args:
            task_id: 任务ID
            event_type: 事件类型
            data: 事件数据
        """
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'data': data or {}
        }
        
        with self.task_lock:
            if task_id not in self.active_tasks:
                self.console_logger.warning(f"任务不存在: {task_id}")
                return
            
            task = self.active_tasks[task_id]
            event['elapsed_ms'] = (datetime.now() - task['start_time']).total_seconds() * 1000
            task['events'].append(event)
    
    def end_task(
        self, 
        task_id: str, 
        success: bool = True, 
        error: Optional[str] = None
    ):
        """
        结束任务并保存日志文件
        
        Args:
            task_id: 任务ID
            success: 是否成功
            error: 错误信息（如果失败）
        """
        with self.task_lock:
            if task_id not in self.active_tasks:
                self.console_logger.warning(f"任务不存在，无法结束: {task_id}")
                return
            
            task = self.active_tasks.pop(task_id)
        
        # 计算总耗时
        total_duration_ms = (datetime.now() - task['start_time']).total_seconds() * 1000
        
        # 记录结束事件
        end_event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'task_end',
            'data': {
                'success': success,
                'error': error,
                'total_events': len(task['events'])
            },
            'elapsed_ms': total_duration_ms
        }
        task['events'].append(end_event)
        
        # 保存日志文件
        self._save_log_file(task_id, task, total_duration_ms, success, error)
        
        # 控制台只输出简要信息
        if not task.get('silent', False):
            status = "[OK]" if success else "[ERROR]"
            self.console_logger.info(
                f"[{task['task_type']}] 任务结束: {task['task_name']} "
                f"{status} 耗时: {total_duration_ms:.1f}ms"
            )
    
    def _save_log_file(
        self, 
        task_id: str, 
        task: Dict[str, Any], 
        total_duration_ms: float,
        success: bool,
        error: Optional[str]
    ):
        """保存日志文件"""
        import asyncio
        import threading
        
        def save_thread():
            try:
                log_filename = f"{task_id}.log"
                log_path = self.logs_dir / log_filename
                
                # 构建日志数据
                log_data = {
                    'task_id': task_id,
                    'task_type': task['task_type'],
                    'task_name': task['task_name'],
                    'start_time': task['start_time'].isoformat(),
                    'total_duration_ms': round(total_duration_ms, 2),
                    'success': success,
                    'error': error,
                    'events_count': len(task['events']),
                    'metadata': task['metadata'],
                    'events': task['events']
                }
                
                # 写入JSON格式（方便解析）
                json_path = self.logs_dir / f"{task_id}.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(log_data, f, ensure_ascii=False, indent=2)
                
                # 写入可读的文本格式
                with open(log_path, 'w', encoding='utf-8') as f:
                    f.write(f"{'='*80}\n")
                    f.write(f"任务调试日志\n")
                    f.write(f"{'='*80}\n\n")
                    
                    f.write(f"任务ID: {task_id}\n")
                    f.write(f"任务类型: {task['task_type']}\n")
                    f.write(f"任务名称: {task['task_name']}\n")
                    f.write(f"开始时间: {task['start_time'].isoformat()}\n")
                    f.write(f"总耗时: {total_duration_ms:.2f}ms\n")
                    f.write(f"状态: {'成功' if success else '失败'}\n")
                    
                    if error:
                        f.write(f"错误: {error}\n")
                    
                    if task['metadata']:
                        f.write(f"\n元数据:\n")
                        for key, value in task['metadata'].items():
                            f.write(f"  {key}: {value}\n")
                    
                    f.write(f"\n{'='*80}\n")
                    f.write(f"事件时间线\n")
                    f.write(f"{'='*80}\n\n")
                    
                    for event in task['events']:
                        elapsed = event.get('elapsed_ms', 0)
                        f.write(f"[{event['timestamp']}]\n")
                        f.write(f"  事件: {event['event_type']}\n")
                        f.write(f"  相对时间: {elapsed:.2f}ms\n")
                        
                        if event['data']:
                            f.write(f"  数据: {json.dumps(event['data'], ensure_ascii=False, indent=4)}\n")
                        
                        f.write("\n")
                    
                    f.write(f"\n{'='*80}\n")
                    f.write(f"JSON数据文件: {json_path.name}\n")
                    f.write(f"{'='*80}\n")
            except Exception as e:
                self.console_logger.error(f"保存日志文件失败: {str(e)}", exc_info=True)

        # 在后台线程中保存日志，避免阻塞当前流程
        threading.Thread(target=save_thread, daemon=True).start()
    
    @contextmanager
    def task_context(
        self, 
        task_type: str, 
        task_name: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        任务上下文管理器，自动处理开始和结束
        
        Usage:
            with debug_log_manager.task_context('api_request', '获取股票数据', {'code': '600219'}) as task_id:
                debug_log_manager.log_event(task_id, 'db_query', {'query': 'SELECT ...'})
                # ... 业务逻辑
        """
        task_id = self.start_task(task_type, task_name, metadata)
        try:
            yield task_id
            self.end_task(task_id, success=True)
        except Exception as e:
            self.end_task(task_id, success=False, error=str(e))
            raise
    
    def log_debug(self, task_id: str, message: str, data: Optional[Dict[str, Any]] = None):
        """记录调试信息（仅写入文件，不输出到控制台）"""
        self.log_event(task_id, 'debug', {
            'message': message,
            **(data or {})
        })
    
    def log_info(self, task_id: str, message: str, data: Optional[Dict[str, Any]] = None):
        """记录信息（仅写入文件，不输出到控制台）"""
        self.log_event(task_id, 'info', {
            'message': message,
            **(data or {})
        })
    
    def log_warning(self, task_id: str, message: str, data: Optional[Dict[str, Any]] = None):
        """记录警告（写入文件，同时输出到控制台）"""
        self.log_event(task_id, 'warning', {
            'message': message,
            **(data or {})
        })
        self.console_logger.warning(f"[{task_id}] {message}")
    
    def log_error(self, task_id: str, message: str, data: Optional[Dict[str, Any]] = None):
        """记录错误（写入文件，同时输出到控制台）"""
        self.log_event(task_id, 'error', {
            'message': message,
            **(data or {})
        })
        self.console_logger.error(f"[{task_id}] {message}")
    
    def get_active_tasks(self) -> Dict[str, Any]:
        """获取所有活跃任务"""
        with self.task_lock:
            return {
                tid: {
                    'task_type': task['task_type'],
                    'task_name': task['task_name'],
                    'elapsed_ms': (datetime.now() - task['start_time']).total_seconds() * 1000,
                    'events_count': len(task['events'])
                }
                for tid, task in self.active_tasks.items()
            }


# 全局单例
debug_log_manager = DebugLogManager()
