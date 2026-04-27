"""
客户端日志处理器
接收并保存客户端日志到文件
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import aiofiles
import asyncio

logger = logging.getLogger(__name__)

class ClientLogHandler:
    """客户端日志处理器"""
    
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.session_log_files: Dict[str, Path] = {}
        
        # 当前会话的日志文件
        self.current_session_file = None
        self.current_session_date = None
        
        # 日志队列（异步写入）
        self.log_queue: List[Dict[str, Any]] = []
        self.flush_interval = 2
        self.max_queue_size = 20
        
        # 启动后台刷新任务
        self._flush_task = None
        
    async def start(self):
        """启动日志处理器"""
        logger.info("[OK] Client log handler started")
        logger.info(f"   日志目录: {self.log_dir}")
        
        # 启动定时刷新任务
        self._flush_task = asyncio.create_task(self._periodic_flush())
        
    async def stop(self):
        """停止日志处理器"""
        if self._flush_task:
            self._flush_task.cancel()
            
        # 最后一次刷新
        await self._flush_logs()
        logger.info("[OK] Client log handler stopped")
        
    async def handle_client_logs(self, logs: List[Dict[str, Any]]):
        """
        处理客户端日志
        
        Args:
            logs: 客户端日志列表
        """
        try:
            normalized_logs = [self._normalize_log_entry(log_entry) for log_entry in logs]

            # 添加到队列
            self.log_queue.extend(normalized_logs)
            
            # 输出到后端控制台（仅warning和error级别）
            for log_entry in normalized_logs:
                if log_entry.get('level') in ['warning', 'error']:
                    self._log_to_backend_console(log_entry)
            
            should_flush_immediately = any(
                log_entry.get('category') == 'loading' for log_entry in normalized_logs
            )

            if should_flush_immediately or len(self.log_queue) >= self.max_queue_size:
                await self._flush_logs()
                
        except Exception as e:
            logger.error(f"处理客户端日志失败: {str(e)}", exc_info=True)

    def _normalize_log_entry(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        normalized = dict(log_entry)
        if 'session_id' not in normalized and 'sessionId' in normalized:
            normalized['session_id'] = normalized['sessionId']
        if 'stock_code' not in normalized and 'stockCode' in normalized:
            normalized['stock_code'] = normalized['stockCode']
        if 'user_agent' not in normalized and 'userAgent' in normalized:
            normalized['user_agent'] = normalized['userAgent']
        return normalized
            
    def _log_to_backend_console(self, log_entry: Dict[str, Any]):
        """将重要日志输出到后端控制台"""
        level = log_entry.get('level', 'info')
        category = log_entry.get('category', 'unknown')
        message = log_entry.get('message', '')
        stock_code = log_entry.get('stock_code', '')
        session_id = log_entry.get('session_id', '')[:8]
        
        prefix = f"[CLIENT][{session_id}][{category.upper()}]"
        stock_prefix = f"[{stock_code}]" if stock_code else ""
        
        full_message = f"{prefix}{stock_prefix} {message}"
        
        if level == 'error':
            logger.error(full_message)
        elif level == 'warning':
            logger.warning(full_message)
            
    async def _periodic_flush(self):
        """定时刷新日志到文件"""
        while True:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush_logs()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"定时刷新日志失败: {str(e)}", exc_info=True)
                
    async def _flush_logs(self):
        """将队列中的日志写入文件"""
        if not self.log_queue:
            return
            
        try:
            # 获取当前日志
            logs = self.log_queue
            self.log_queue = []
            
            # 按会话ID分组
            session_groups: Dict[str, List[Dict]] = {}
            for log_entry in logs:
                session_id = log_entry.get('session_id', 'unknown')
                if session_id not in session_groups:
                    session_groups[session_id] = []
                session_groups[session_id].append(log_entry)
            
            # 为每个会话写入日志文件
            for session_id, session_logs in session_groups.items():
                await self._write_session_logs(session_id, session_logs)
                
            logger.info(f"[OK] 已保存 {len(logs)} 条客户端日志")
            
        except Exception as e:
            logger.error(f"刷新日志失败: {str(e)}", exc_info=True)
            
    async def _write_session_logs(self, session_id: str, logs: List[Dict]):
        """写入会话日志文件"""
        try:
            log_file = self._resolve_session_log_file(session_id, logs)
            
            # 异步写入日志（追加模式）
            async with aiofiles.open(log_file, mode='a', encoding='utf-8') as f:
                for log_entry in logs:
                    # 添加服务器接收时间
                    log_entry['server_received_at'] = datetime.now().isoformat()
                    
                    # 写入一行JSON
                    await f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
                    
        except Exception as e:
            logger.error(f"写入会话日志失败: session={session_id}, error={str(e)}", exc_info=True)

    def _resolve_session_log_file(self, session_id: str, logs: List[Dict]) -> Path:
        if session_id in self.session_log_files:
            return self.session_log_files[session_id]

        safe_session_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in session_id)
        if not safe_session_id:
            safe_session_id = "unknown"

        startup_time = datetime.now()
        for log_entry in logs:
            timestamp = log_entry.get('timestamp')
            if not timestamp:
                continue
            try:
                startup_time = datetime.fromisoformat(str(timestamp).replace('Z', '+00:00'))
                break
            except ValueError:
                continue

        day = startup_time.strftime('%Y-%m-%d')
        startup_suffix = startup_time.strftime('%H%M%S%f')
        log_file = self.log_dir / f"client-{day}-{startup_suffix}-{safe_session_id}.jsonl"
        self.session_log_files[session_id] = log_file
        return log_file
            
    async def get_session_logs(self, session_id: str, limit: int = 100) -> List[Dict]:
        """
        获取指定会话的日志
        
        Args:
            session_id: 会话ID
            limit: 最大返回数量
            
        Returns:
            日志列表
        """
        logs = []
        
        try:
            safe_session_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in session_id)
            candidate_files = sorted(
                self.log_dir.glob(f"client-*-*-{safe_session_id}.jsonl"),
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )
            candidate_files.append(self.log_dir / f"client-{datetime.now().strftime('%Y-%m-%d')}.jsonl")

            for log_file in candidate_files:
                if not log_file.exists():
                    continue

                async with aiofiles.open(log_file, mode='r', encoding='utf-8') as f:
                    lines = await f.readlines()

                for line in reversed(lines):
                    try:
                        log_entry = json.loads(line.strip())
                        entry_session = log_entry.get('session_id') or log_entry.get('sessionId')
                        if entry_session == session_id:
                            logs.insert(0, log_entry)
                            if len(logs) >= limit:
                                return logs
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            logger.error(f"读取会话日志失败: session={session_id}, error={str(e)}", exc_info=True)
            
        return logs
        
    async def get_stats(self) -> Dict[str, Any]:
        """获取日志统计信息"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            log_files = list(self.log_dir.glob(f"client-{today}-*.jsonl"))
            legacy_today_file = self.log_dir / f"client-{today}.jsonl"
            if legacy_today_file.exists():
                log_files.append(legacy_today_file)
            
            total_size = sum(f.stat().st_size for f in log_files if f.exists())
            
            today_count = 0
            for log_file in log_files:
                if not log_file.exists():
                    continue
                async with aiofiles.open(log_file, mode='r', encoding='utf-8') as f:
                    today_count += len(await f.readlines())
            
            return {
                'total_files': len(log_files),
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'today_count': today_count,
                'queue_size': len(self.log_queue),
                'log_dir': str(self.log_dir),
            }
            
        except Exception as e:
            logger.error(f"获取日志统计失败: {str(e)}", exc_info=True)
            return {}
