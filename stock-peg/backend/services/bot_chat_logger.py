"""
飞书机器人对话日志服务
记录所有对话消息到日志文件
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional


class BotChatLogger:
    """对话日志记录器"""
    
    def __init__(self, log_dir: Optional[str] = None):
        """
        初始化日志记录器
        
        Args:
            log_dir: 日志文件目录，默认为 backend/logs/bot-chat
        """
        if log_dir is None:
            # 使用绝对路径
            backend_dir = Path(__file__).resolve().parent.parent
            log_dir = backend_dir / "logs" / "bot-chat"
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建按日期分类的日志文件
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.log_file = self.log_dir / f"chat-{self.current_date}.log"
        
        # 配置日志格式
        self.logger = logging.getLogger("bot-chat")
        self.logger.setLevel(logging.INFO)
        
        # 避免重复添加 handler
        if not self.logger.handlers:
            # 文件 handler
            file_handler = logging.FileHandler(
                self.log_file,
                encoding='utf-8',
                mode='a'  # 追加模式
            )
            file_handler.setLevel(logging.INFO)
            
            # 日志格式
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            
            self.logger.addHandler(file_handler)
    
    def _check_date_change(self):
        """检查日期是否变化，如果变化则创建新的日志文件"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        if current_date != self.current_date:
            self.current_date = current_date
            self.log_file = self.log_dir / f"chat-{self.current_date}.log"
            
            # 更新 handler
            for handler in self.logger.handlers[:]:
                handler.close()
                self.logger.removeHandler(handler)
            
            file_handler = logging.FileHandler(
                self.log_file,
                encoding='utf-8',
                mode='a'
            )
            file_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def log_message(
        self,
        message_id: str,
        sender_type: str,
        sender_id: Optional[str],
        content: str,
        chat_id: Optional[str] = None
    ):
        """
        记录对话消息
        
        Args:
            message_id: 消息 ID
            sender_type: 发送者类型 (user/bot)
            sender_id: 发送者 ID
            content: 消息内容
            chat_id: 会话 ID
        """
        self._check_date_change()
        
        # 构建日志数据
        log_data = {
            "message_id": message_id,
            "sender_type": sender_type,
            "sender_id": sender_id or "unknown",
            "content": content,
            "chat_id": chat_id or "unknown",
            "timestamp": datetime.now().isoformat()
        }
        
        # 格式化日志消息
        sender_label = "[BOT] BOT" if sender_type == "bot" else "👤 USER"
        log_message = f"{sender_label} | {sender_id or 'unknown'} | {content}"
        
        # 记录到日志文件
        self.logger.info(log_message)
        
        # 同时记录 JSON 格式（用于数据分析）
        self._log_json(log_data)
    
    def _log_json(self, data: dict):
        """记录 JSON 格式的日志数据"""
        json_file = self.log_dir / f"chat-{self.current_date}.json"
        
        try:
            # 追加 JSON 行
            with open(json_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
        except Exception as e:
            self.logger.error(f"Failed to write JSON log: {e}")
    
    def log_error(self, error_msg: str, context: Optional[dict] = None):
        """
        记录错误信息
        
        Args:
            error_msg: 错误消息
            context: 上下文信息
        """
        self._check_date_change()
        
        context_str = f" | {json.dumps(context, ensure_ascii=False)}" if context else ""
        self.logger.error(f"[ERROR] ERROR | {error_msg}{context_str}")
    
    def log_command(self, command: str, result: str, sender_id: Optional[str] = None):
        """
        记录命令执行
        
        Args:
            command: 执行的命令
            result: 执行结果
            sender_id: 发送者 ID
        """
        self._check_date_change()
        
        self.logger.info(f"⚡ CMD | {sender_id or 'unknown'} | {command} | {result}")
    
    def get_recent_logs(self, date: Optional[str] = None, limit: int = 100) -> list[dict]:
        """
        获取最近的日志记录
        
        Args:
            date: 日期 (YYYY-MM-DD)，默认今天
            limit: 返回记录数量限制
            
        Returns:
            日志记录列表
        """
        target_date = date or datetime.now().strftime("%Y-%m-%d")
        json_file = self.log_dir / f"chat-{target_date}.json"
        
        if not json_file.exists():
            return []
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # 从后往前读取
            logs = []
            for line in reversed(lines[-limit:]):
                try:
                    log_data = json.loads(line.strip())
                    logs.append(log_data)
                except:
                    continue
            
            return logs
        except Exception as e:
            self.logger.error(f"Failed to read logs: {e}")
            return []


# 全局实例
bot_chat_logger = BotChatLogger()
