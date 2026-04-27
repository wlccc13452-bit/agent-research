"""日志服务 - 记录所有对话和外部网络调用"""
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import threading
from config.settings import settings

logger = logging.getLogger(__name__)


class LogService:
    """日志服务单例"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(LogService, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.log_dir = settings.data_dir / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 当前启动日期
        self.start_date = datetime.now().strftime("%Y-%m-%d")
        self.start_time = datetime.now().strftime("%H-%M-%S")
        
        # 日志文件路径
        self.conversation_log_file = None
        self.network_log_file = None
        
        # 文件锁
        self.file_lock = threading.Lock()
        
        # 初始化日志文件
        self._init_log_files()
        
        self._initialized = True
        logger.info(f"日志服务已初始化，日志目录: {self.log_dir}")
    
    def _init_log_files(self):
        """初始化日志文件"""
        # 对话日志文件 - 每日一个文件
        conversation_log_name = f"conversation_{self.start_date}.log"
        self.conversation_log_file = self.log_dir / conversation_log_name
        
        # 如果文件不存在，创建并写入文件头
        if not self.conversation_log_file.exists():
            self._write_conversation_header()
        
        # 网络调用日志文件 - 每次启动一个新文件
        network_log_name = f"network_{self.start_date}_{self.start_time}.log"
        self.network_log_file = self.log_dir / network_log_name
        self._write_network_header()
    
    def _write_conversation_header(self):
        """写入对话日志文件头"""
        header = f"""
{'='*80}
股票分析系统 - 客户端/服务端对话日志
启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*80}

"""
        with open(self.conversation_log_file, 'w', encoding='utf-8') as f:
            f.write(header)
    
    def _write_network_header(self):
        """写入网络调用日志文件头"""
        header = f"""
{'='*80}
股票分析系统 - 外部网络调用日志
启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*80}

"""
        with open(self.network_log_file, 'w', encoding='utf-8') as f:
            f.write(header)
    
    def _check_date_rollover(self):
        """检查是否需要滚动日志文件（新的一天）"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        if current_date != self.start_date:
            with self.file_lock:
                self.start_date = current_date
                self.start_time = datetime.now().strftime("%H-%M-%S")
                self._init_log_files()
                logger.info(f"日志文件已滚动到新日期: {current_date}")
    
    def log_http_request(
        self,
        method: str,
        path: str,
        request_data: Optional[Dict] = None,
        response_data: Optional[Any] = None,
        status_code: int = 200,
        duration_ms: Optional[float] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """记录HTTP请求"""
        self._check_date_rollover()
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "HTTP_REQUEST",
            "method": method,
            "path": path,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "request": request_data,
            "response": response_data if not isinstance(response_data, (str, int, float, list, dict, type(None))) else response_data,
            "status_code": status_code,
            "duration_ms": duration_ms
        }
        
        self._write_conversation_log(log_entry)
    
    def log_websocket_message(
        self,
        direction: str,  # "INCOMING" or "OUTGOING"
        message_type: str,
        data: Optional[Dict] = None,
        client_id: Optional[str] = None,
        stock_code: Optional[str] = None
    ):
        """记录WebSocket消息"""
        self._check_date_rollover()
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "WEBSOCKET_MESSAGE",
            "direction": direction,
            "message_type": message_type,
            "client_id": client_id,
            "stock_code": stock_code,
            "data": data
        }
        
        self._write_conversation_log(log_entry)
    
    def log_llm_call(
        self,
        provider: str,
        model: str,
        prompt: str,
        response: Optional[str] = None,
        error: Optional[str] = None,
        duration_ms: Optional[float] = None,
        tokens_used: Optional[Dict] = None
    ):
        """记录LLM调用"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "LLM_CALL",
            "provider": provider,
            "model": model,
            "prompt": prompt[:1000] if len(prompt) > 1000 else prompt,  # 限制prompt长度
            "response": response[:1000] if response and len(response) > 1000 else response,
            "error": error,
            "duration_ms": duration_ms,
            "tokens_used": tokens_used
        }
        
        self._write_network_log(log_entry)
    
    def log_external_api_call(
        self,
        api_name: str,
        url: str,
        method: str = "GET",
        request_params: Optional[Dict] = None,
        request_body: Optional[Any] = None,
        response_status: Optional[int] = None,
        response_data: Optional[Any] = None,
        error: Optional[str] = None,
        duration_ms: Optional[float] = None
    ):
        """记录外部API调用"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "EXTERNAL_API_CALL",
            "api_name": api_name,
            "url": url,
            "method": method,
            "request_params": request_params,
            "request_body": request_body,
            "response_status": response_status,
            "response_data": response_data if not isinstance(response_data, (str, int, float, list, dict, type(None))) else str(response_data)[:500],
            "error": error,
            "duration_ms": duration_ms
        }
        
        self._write_network_log(log_entry)
    
    def _write_conversation_log(self, log_entry: Dict):
        """写入对话日志"""
        def _write():
            try:
                with self.file_lock:
                    with open(self.conversation_log_file, 'a', encoding='utf-8') as f:
                        f.write(json.dumps(log_entry, ensure_ascii=False, indent=2) + "\n\n")
            except Exception as e:
                logger.error(f"写入对话日志失败: {str(e)}")
        
        # 异步环境中使用线程池写入，避免阻塞事件循环
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                loop.run_in_executor(None, _write)
            else:
                _write()
        except RuntimeError:
            _write()

    def _write_network_log(self, log_entry: Dict):
        """写入网络调用日志"""
        def _write():
            try:
                with self.file_lock:
                    with open(self.network_log_file, 'a', encoding='utf-8') as f:
                        f.write(json.dumps(log_entry, ensure_ascii=False, indent=2) + "\n\n")
            except Exception as e:
                logger.error(f"写入网络调用日志失败: {str(e)}")
        
        # 异步环境中使用线程池写入，避免阻塞事件循环
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                loop.run_in_executor(None, _write)
            else:
                _write()
        except RuntimeError:
            _write()


# 全局日志服务实例
log_service = LogService()
