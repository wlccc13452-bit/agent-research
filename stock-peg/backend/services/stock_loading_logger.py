"""股票加载过程日志跟踪服务"""
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from collections import defaultdict
import time
import threading

# 主日志
logger = logging.getLogger(__name__)


class StockLoadingLogger:
    """股票加载过程日志跟踪器
    
    用于记录股票切换时前后端的完整加载过程，帮助定位性能瓶颈
    
    日志文件位置: backend/logs/loading-stock/{stock_code}_{timestamp}.log
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(StockLoadingLogger, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.logs_dir = Path(__file__).parent.parent / "logs" / "loading-stock"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # 当前活跃的跟踪会话 {session_id: {stock_code, events, start_time}}
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_lock = threading.Lock()
        
        self._initialized = True
        logger.info(f"股票加载日志跟踪服务已初始化，日志目录: {self.logs_dir}")
    
    def start_session(self, stock_code: str, source: str = "unknown") -> str:
        """
        开始一个新的加载跟踪会话
        
        Args:
            stock_code: 股票代码
            source: 触发源（如 'frontend_click', 'keyboard_nav'）
            
        Returns:
            session_id: 会话ID，用于后续事件记录
        """
        session_id = f"{stock_code}_{int(time.time() * 1000)}"
        
        with self.session_lock:
            self.active_sessions[session_id] = {
                'stock_code': stock_code,
                'source': source,
                'start_time': time.time(),
                'events': [],
                'metadata': {}
            }
        
        # 记录会话开始事件
        self.log_event(
            session_id,
            'session_start',
            'backend',
            {
                'stock_code': stock_code,
                'source': source
            }
        )
        
        logger.info(f"[{session_id}] 开始跟踪股票加载: {stock_code} (来源: {source})")
        return session_id
    
    def log_event(
        self, 
        session_id: str, 
        event_type: str, 
        location: str, 
        data: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None
    ):
        """
        记录一个事件
        
        Args:
            session_id: 会话ID
            event_type: 事件类型（如 'frontend_request_start', 'backend_api_call'）
            location: 事件位置（'frontend' 或 'backend'）
            data: 事件数据
            duration_ms: 事件耗时（毫秒）
        """
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'location': location,
            'data': data or {},
            'duration_ms': duration_ms,
            'elapsed_ms': None  # 相对于会话开始的耗时
        }
        
        with self.session_lock:
            if session_id not in self.active_sessions:
                logger.warning(f"[{session_id}] 会话不存在，跳过事件: {event_type}")
                return
            
            session = self.active_sessions[session_id]
            event['elapsed_ms'] = (time.time() - session['start_time']) * 1000
            session['events'].append(event)
        
        # 简化日志输出
        elapsed = event['elapsed_ms']
        duration_str = f" [{duration_ms:.1f}ms]" if duration_ms else ""
        logger.info(f"[{session_id}] [{location}] {event_type}{duration_str} @{elapsed:.1f}ms")
    
    def end_session(self, session_id: str, success: bool = True, error: Optional[str] = None):
        """
        结束跟踪会话并保存日志
        
        Args:
            session_id: 会话ID
            success: 是否成功
            error: 错误信息（如果失败）
        """
        with self.session_lock:
            if session_id not in self.active_sessions:
                logger.warning(f"[{session_id}] 会话不存在，无法结束")
                return
            
            session = self.active_sessions.pop(session_id)
        
        # 计算总耗时
        total_duration_ms = (time.time() - session['start_time']) * 1000
        
        # 记录结束事件
        end_event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'session_end',
            'location': 'backend',
            'data': {
                'success': success,
                'error': error,
                'total_events': len(session['events'])
            },
            'duration_ms': total_duration_ms,
            'elapsed_ms': total_duration_ms
        }
        session['events'].append(end_event)
        
        # 生成日志文件
        self._save_log_file(session_id, session, total_duration_ms, success, error)
        
        logger.info(
            f"[{session_id}] 会话结束: {session['stock_code']} "
            f"总耗时: {total_duration_ms:.1f}ms "
            f"事件数: {len(session['events'])} "
            f"成功: {success}"
        )
    
    def _save_log_file(
        self, 
        session_id: str, 
        session: Dict[str, Any], 
        total_duration_ms: float,
        success: bool,
        error: Optional[str]
    ):
        """保存日志文件"""
        try:
            stock_code = session['stock_code']
            
            # 创建股票代码子目录
            stock_dir = self.logs_dir / stock_code
            stock_dir.mkdir(parents=True, exist_ok=True)
            
            # 使用时间戳作为文件名（更简洁）
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            log_filename = f"{timestamp}.log"
            json_filename = f"{timestamp}.json"
            
            log_path = stock_dir / log_filename
            json_path = stock_dir / json_filename
            
            # 分析性能瓶颈
            performance_analysis = self._analyze_performance(session['events'])
            
            # 构建日志内容
            log_data = {
                'session_id': session_id,
                'stock_code': session['stock_code'],
                'source': session['source'],
                'start_time': datetime.fromtimestamp(session['start_time']).isoformat(),
                'total_duration_ms': round(total_duration_ms, 2),
                'success': success,
                'error': error,
                'events_count': len(session['events']),
                'performance_analysis': performance_analysis,
                'events': session['events']
            }
            
            # 写入JSON格式（方便解析）
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
            
            # 写入可读的文本格式
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(f"{'='*80}\n")
                f.write(f"股票加载过程日志\n")
                f.write(f"{'='*80}\n\n")
                
                f.write(f"会话ID: {session_id}\n")
                f.write(f"股票代码: {session['stock_code']}\n")
                f.write(f"触发源: {session['source']}\n")
                f.write(f"开始时间: {log_data['start_time']}\n")
                f.write(f"总耗时: {total_duration_ms:.2f}ms\n")
                f.write(f"状态: {'成功' if success else '失败'}\n")
                if error:
                    f.write(f"错误: {error}\n")
                f.write(f"\n{'='*80}\n")
                f.write(f"性能分析\n")
                f.write(f"{'='*80}\n\n")
                
                for analysis in performance_analysis:
                    f.write(f"{analysis}\n")
                
                f.write(f"\n{'='*80}\n")
                f.write(f"详细事件时间线\n")
                f.write(f"{'='*80}\n\n")
                
                for event in session['events']:
                    elapsed = event.get('elapsed_ms', 0)
                    duration = event.get('duration_ms')
                    duration_str = f" (耗时: {duration:.2f}ms)" if duration else ""
                    
                    f.write(f"[{event['timestamp']}]\n")
                    f.write(f"  [{event['location']}] {event['event_type']}{duration_str}\n")
                    f.write(f"  相对时间: {elapsed:.2f}ms\n")
                    
                    if event['data']:
                        f.write(f"  数据: {json.dumps(event['data'], ensure_ascii=False)}\n")
                    
                    f.write("\n")
                
                f.write(f"\n{'='*80}\n")
                f.write(f"JSON数据文件: {json_path.name}\n")
                f.write(f"{'='*80}\n")
            
            logger.info(f"日志已保存: {log_path} (目录: {stock_code}/)")
            
        except Exception as e:
            logger.error(f"保存日志文件失败: {str(e)}", exc_info=True)
    
    def _analyze_performance(self, events: list) -> list:
        """分析性能瓶颈"""
        analysis = []
        
        # 按位置分组统计耗时
        location_stats = defaultdict(lambda: {'count': 0, 'total_ms': 0})
        
        for event in events:
            if event.get('duration_ms'):
                location = event['location']
                location_stats[location]['count'] += 1
                location_stats[location]['total_ms'] += event['duration_ms']
        
        # 找出耗时最长的事件
        longest_events = sorted(
            [e for e in events if e.get('duration_ms')],
            key=lambda x: x['duration_ms'],
            reverse=True
        )[:5]
        
        analysis.append(f"各位置总耗时:")
        for location, stats in location_stats.items():
            analysis.append(
                f"  {location}: {stats['count']}次调用, 总计 {stats['total_ms']:.2f}ms"
            )
        
        analysis.append(f"\n耗时最长的5个事件:")
        for i, event in enumerate(longest_events, 1):
            analysis.append(
                f"  {i}. {event['event_type']} ({event['location']}): "
                f"{event['duration_ms']:.2f}ms @{event['elapsed_ms']:.2f}ms"
            )
        
        # 识别性能瓶颈
        analysis.append(f"\n性能建议:")
        if longest_events:
            slowest = longest_events[0]
            if slowest['duration_ms'] > 500:
                analysis.append(
                    f"  [WARN]️  主要瓶颈: {slowest['event_type']} 耗时 {slowest['duration_ms']:.2f}ms"
                )
                
                # 给出具体建议
                if 'api' in slowest['event_type'].lower():
                    analysis.append(f"     建议: 检查API响应时间，考虑使用缓存或预加载")
                elif 'db' in slowest['event_type'].lower():
                    analysis.append(f"     建议: 检查数据库查询，添加索引或优化查询")
                elif 'render' in slowest['event_type'].lower():
                    analysis.append(f"     建议: 优化前端渲染，考虑虚拟滚动或延迟加载")
        
        return analysis
    
    def get_active_sessions(self) -> Dict[str, Any]:
        """获取所有活跃会话"""
        with self.session_lock:
            return {
                sid: {
                    'stock_code': session['stock_code'],
                    'elapsed_ms': (time.time() - session['start_time']) * 1000,
                    'events_count': len(session['events'])
                }
                for sid, session in self.active_sessions.items()
            }


# 单例实例
stock_loading_logger = StockLoadingLogger()
