"""
基于行数限制的日志处理器
当日志文件超过指定行数时，自动保留最新的N行
"""
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional
import threading


class LineLimitedFileHandler(RotatingFileHandler):
    """基于行数限制的文件日志处理器
    
    当日志文件超过max_lines行时，自动删除旧内容，只保留最新的max_lines行
    """
    
    def __init__(
        self, 
        filename: str,
        max_lines: int = 100,
        mode: str = 'a',
        encoding: Optional[str] = None,
        delay: bool = False
    ):
        """
        初始化行数限制的日志处理器
        
        Args:
            filename: 日志文件路径
            max_lines: 最大保留行数，默认100行
            mode: 文件打开模式
            encoding: 文件编码
            delay: 是否延迟打开文件
        """
        super().__init__(
            filename, 
            mode=mode, 
            encoding=encoding,
            delay=delay,
            maxBytes=0,  # 不使用字节大小限制
            backupCount=0  # 不使用备份
        )
        self.max_lines = max_lines
        self.line_count = 0
        self._trim_lock = threading.Lock()
        self._last_trim_line = 0  # 上次裁剪时的行数
        
        # 如果文件已存在，计算当前行数
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            try:
                with open(filename, 'r', encoding=encoding or 'utf-8') as f:
                    self.line_count = sum(1 for _ in f)
            except Exception:
                self.line_count = 0
    
    def emit(self, record):
        """写入日志记录，并检查行数限制"""
        try:
            # 调用父类方法写入日志
            super().emit(record)
            
            # 增加行计数
            self.line_count += 1
            
            # 检查是否超过行数限制（超过5行才裁剪，避免频繁裁剪）
            if self.line_count > self.max_lines + 5:
                self._trim_file()
        except Exception:
            self.handleError(record)
    
    def _trim_file(self):
        """裁剪日志文件，只保留最新的max_lines行"""
        with self._trim_lock:
            try:
                # 避免重复裁剪
                if self.line_count == self._last_trim_line:
                    return
                
                # 读取所有行
                with open(self.baseFilename, 'r', encoding=self.encoding or 'utf-8') as f:
                    lines = f.readlines()
                
                actual_lines = len(lines)
                
                # 只保留最后max_lines行
                if actual_lines > self.max_lines:
                    trimmed_lines = lines[-self.max_lines:]
                    
                    # 重新写入文件
                    with open(self.baseFilename, 'w', encoding=self.encoding or 'utf-8') as f:
                        f.writelines(trimmed_lines)
                    
                    # 更新行计数和上次裁剪行数
                    self.line_count = len(trimmed_lines)
                    self._last_trim_line = self.line_count
                    
                    # 静默裁剪，不输出到控制台
            except Exception:
                # 裁剪失败不影响日志写入，静默处理
                pass
    
    def shouldRollover(self, record):
        """禁用基于文件大小的轮转"""
        return False
    
    def doRollover(self):
        """禁用文件轮转"""
        pass
