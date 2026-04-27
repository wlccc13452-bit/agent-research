"""FastAPI主入口"""
# Windows asyncio 修复：避免 ConnectionResetError
import sys
import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any
from collections import defaultdict

# 修复 SSL 证书验证问题 (特别是 Windows 上的 curl error 77)
try:
    import certifi
    os.environ['SSL_CERT_FILE'] = certifi.where()
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
    os.environ['CURL_CA_BUNDLE'] = certifi.where()
except ImportError:
    pass

# Windows 平台设置事件循环策略，避免网络IO死锁
if sys.platform == 'win32':
    # Windows上使用 SelectorEventLoop，增强网络IO稳定性
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import select, and_, desc
from config.settings import settings
from database import init_db
from database.session import async_session_maker
from database.models import StockKLineData
from middleware.logging_middleware import LoggingMiddleware
from middleware.response_middleware import ResponseStandardizationMiddleware, ExceptionHandlerMiddleware

# 导入路由
from routers import stock, fundamental, report, us_market, holding, websocket, status, config
from routers.client_logs import router as client_logs_router
from routers.holdings import router as holdings_router
from routers.daily_watchlist import router as daily_watchlist_router
from routers.price_alerts import router as price_alerts_router
from routers.settings import router as settings_router
from routers.cache import router as cache_router

# 配置日志 - 减少控制台输出，详细信息写入日志文件
# 统一日志格式，避免重复输出
def setup_logging():
    """Setup logging with enhanced file output for server debugging"""
    # 使用增强的日志配置（输出到 logs/server-debug）
    from config.logging_config import setup_logging as enhanced_setup_logging
    enhanced_setup_logging(
        log_dir="logs",
        log_level="INFO" if settings.debug else "WARNING",
        config_path="config/console_output.ini"
    )

    # 为关键模块设置更详细的日志级别
    if not settings.debug:
        # 非调试模式下，减少第三方库的输出
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('httpcore').setLevel(logging.WARNING)
        logging.getLogger('uvicorn').setLevel(logging.WARNING)
        logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
        # 关闭数据库操作日志
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
        logging.getLogger('sqlalchemy.engine.Engine').setLevel(logging.WARNING)
        logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
        logging.getLogger('sqlalchemy.orm').setLevel(logging.WARNING)

# 初始化日志
setup_logging()

logger = logging.getLogger(__name__)


def _install_windows_asyncio_exception_handler() -> None:
    """增强的 Windows 异常处理器，过滤更多干扰性异常"""
    if sys.platform != "win32":
        return
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return

    def _exception_handler(current_loop: asyncio.AbstractEventLoop, context: dict) -> None:
        exception = context.get("exception")
        message = context.get("message", "")
        
        # 过滤 ConnectionResetError (winerror 10054)
        if (
            isinstance(exception, ConnectionResetError)
            and getattr(exception, "winerror", None) == 10054
            and "_ProactorBasePipeTransport._call_connection_lost" in message
        ):
            return
        
        # 过滤 BrokenPipeError (EPIPE) - Windows 调试器频繁断开导致
        if isinstance(exception, BrokenPipeError):
            logger.debug(f"Ignoring BrokenPipeError (EPIPE): {message}")
            return
        
        # 过滤其他常见的 Windows 网络异常
        if isinstance(exception, OSError):
            error_code = getattr(exception, "winerror", None) or getattr(exception, "errno", None)
            # 10053: Software caused connection abort
            # 10054: Connection reset by peer
            # 10038: Socket operation on non-socket
            if error_code in (10053, 10054, 10038):
                logger.debug(f"Ignoring Windows network error {error_code}: {message}")
                return
        
        current_loop.default_exception_handler(context)

    loop.set_exception_handler(_exception_handler)


# 全局初始化状态跟踪
_startup_state = {
    'db_ready': False,
    'websocket_ready': False,
    'services_ready': False
}

_preload_state = {
    'status': 'pending',
    'progress': 0,
    'message': '',
    'error': None,
    'updated_at': None
}


def _derive_sync_status() -> str:
    preload_status = _preload_state.get('status')
    if preload_status == 'ready':
        return 'ready'
    if _startup_state.get('services_ready') or preload_status == 'syncing':
        return 'syncing'
    return 'pending'

# WebSocket 广播节流器
class BroadcastThrottler:
    """WebSocket 广播节流器，防止前端压力过大"""
    
    def __init__(self, max_per_second: int = 5):
        self.max_per_second = max_per_second
        self.last_broadcast_time = 0.0
        self.broadcast_count = 0
        self._lock = asyncio.Lock()
    
    async def should_broadcast(self) -> bool:
        """判断是否应该发送广播（节流控制）"""
        async with self._lock:
            current_time = asyncio.get_event_loop().time()
            
            # 如果距离上次广播超过 1 秒，重置计数器
            if current_time - self.last_broadcast_time >= 1.0:
                self.broadcast_count = 0
                self.last_broadcast_time = current_time
            
            # 检查是否超过速率限制
            if self.broadcast_count >= self.max_per_second:
                return False
            
            self.broadcast_count += 1
            return True

# 全局节流器实例
_broadcast_throttler = BroadcastThrottler(max_per_second=5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理 - 秒级响应 + 后台异步初始化"""
    # 确保在异步上下文中再次配置日志，避免与 uvicorn 的默认配置冲突
    setup_logging()
    _install_windows_asyncio_exception_handler()
    
    # 打印启动横幅（异步 logger，不阻塞）
    logger.info("=" * 70)
    logger.info("🚀 Stock PEG Server Starting...")
    logger.info("=" * 70)
    logger.info(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"🔧 Debug Mode: {settings.debug}")
    logger.info(f"🌐 Host: {settings.server_host}:{settings.server_port}")
    logger.info("=" * 70)
    
    # ========================================
    # 核心服务后台初始化（秒级响应）
    # ========================================
    async def init_core_services():
        """初始化核心服务（数据库 + WebSocket），不阻塞 yield"""
        try:
            # 数据库初始化（带超时保护）
            logger.info("[INIT] Initializing database...")
            try:
                await asyncio.wait_for(init_db(), timeout=5.0)
                _startup_state['db_ready'] = True
                logger.info("[OK] Database initialized")
            except asyncio.TimeoutError:
                logger.error("[ERROR] Database initialization timeout (5s), will retry in background")
                # 超时后继续启动，后续请求会触发重试
            
            # WebSocket 初始化
            logger.info("[INIT] Starting WebSocket service...")
            from services.websocket_manager import manager
            await manager.start()
            _startup_state['websocket_ready'] = True
            logger.info("[OK] WebSocket service started")
            
        except Exception as e:
            logger.error(f"Core services initialization failed: {e}", exc_info=True)
    
    # 立即启动核心服务初始化（不等待）
    core_init_task = asyncio.create_task(init_core_services())
    
    # ========================================
    # 后台服务启动器（非阻塞，在 yield 后异步执行）
    # ========================================
    async def start_all_background_services():
        """统一的后台服务启动函数，不阻塞 HTTP 服务器启动"""
        try:
            # 等待核心服务完成（最多等待 10 秒）
            try:
                await asyncio.wait_for(core_init_task, timeout=10.0)
            except asyncio.TimeoutError:
                logger.error("[ERROR] Core services initialization timeout (10s)")
                return
            
            logger.info("[BACKGROUND] Starting background services...")
            
            # 1. 日志清理服务
            try:
                from services.log_cleanup_service import run_startup_cleanup
                cleanup_stats = run_startup_cleanup()
                
                if cleanup_stats.get('enabled'):
                    logger.info(f"[OK] Log cleanup: deleted {cleanup_stats.get('total_files_deleted', 0)} files, "
                              f"freed {cleanup_stats.get('total_size_freed', 0) / 1024 / 1024:.2f} MB")
                else:
                    logger.debug("Log cleanup disabled")
            except Exception as e:
                logger.warning(f"Log cleanup service failed: {e}")
            
            # 2. 飞书长连接服务
            try:
                from services.feishu_bot.feishu_bot_dependency_setup import setup_feishu_dependencies
                injector = setup_feishu_dependencies()
                feishu_long_connection_service = injector.long_connection_service
                
                # 获取当前事件循环并传递给长连接服务
                main_loop = asyncio.get_running_loop()
                feishu_long_connection_service.start_in_thread(main_loop)
                await asyncio.sleep(1)  # 给服务启动时间
                
                if feishu_long_connection_service._running:
                    logger.info("[OK] Feishu long connection started")
                else:
                    logger.warning("Feishu service not enabled or incomplete config")
            except Exception as e:
                logger.error(f"Feishu startup failed: {e}")
            
            # 3. 文件监听服务
            try:
                from routers.holding import holding_manager
                holding_manager.start_watching()
                logger.info("[OK] File watcher started")
            except Exception as e:
                logger.error(f"File watcher failed: {e}")
            
            # 4. 定时任务调度器
            try:
                from services.scheduler import task_scheduler
                task_scheduler.start()
                logger.info("[OK] Task scheduler started")
            except Exception as e:
                logger.error(f"Scheduler failed: {e}")
            
            # 5. 实时数据推送服务
            try:
                from services.realtime_pusher import realtime_pusher
                await realtime_pusher.start()
                logger.info("[OK] Realtime pusher started")
            except Exception as e:
                logger.error(f"Realtime pusher failed: {e}")
            
            # 6. 后台数据预加载
            try:
                await preload_market_data(wait_for_completion=False, timeout=60)
            except Exception as e:
                logger.error(f"Preload failed: {e}")
            
            # 7. 延迟执行后台扫描
            await asyncio.sleep(5)
            try:
                from services.background_updater import background_updater
                await background_updater.scan_and_update_missing_data()
                logger.info("[OK] Background scan completed")
            except Exception as e:
                logger.error(f"Background scan failed: {e}")
            
            _startup_state['services_ready'] = True
            logger.info("[OK] All background services started")
            
        except Exception as e:
            logger.error(f"Background services startup failed: {str(e)}", exc_info=True)
    
    # 启动后台服务任务（不阻塞）
    asyncio.create_task(start_all_background_services())
    
    # 立即 yield，允许 FastAPI 开始接受请求
    logger.info("[FASTAPI] Server ready to accept requests (sub-second response)")
    yield
    
    # ========================================
    # 关闭时清理
    # ========================================
    logger.info("[SHUTDOWN] Closing application...")
    
    # 1. 停止实时推送服务
    try:
        from services.realtime_pusher import realtime_pusher
        await realtime_pusher.stop()
        logger.info("[OK] Realtime pusher stopped")
    except Exception as e:
        logger.warning(f"Failed to stop realtime pusher: {e}")
    
    # 2. 停止定时任务调度器
    try:
        from services.scheduler import task_scheduler
        task_scheduler.stop()
        logger.info("[OK] Task scheduler stopped")
    except Exception as e:
        logger.warning(f"Failed to stop scheduler: {e}")
    
    # 3. 停止飞书服务
    try:
        from services.feishu_bot.feishu_bot_dependency_setup import setup_feishu_dependencies
        injector = setup_feishu_dependencies()
        feishu_long_connection_service = injector.long_connection_service
        feishu_long_connection_service.stop()
        logger.info("[OK] Feishu service stopped")
    except Exception as e:
        logger.warning(f"Failed to stop Feishu service: {e}")
    
    # 4. 停止 WebSocket manager
    try:
        from services.websocket_manager import manager
        await manager.stop()
        logger.info("[OK] WebSocket manager stopped")
    except Exception as e:
        logger.warning(f"Failed to stop WebSocket manager: {e}")
    
    # 5. 关闭数据库连接池
    try:
        from database import engine
        await engine.dispose()
        logger.info("[OK] Database connection pool closed")
    except Exception as e:
        logger.warning(f"Failed to close database: {e}")
    
    logger.info("[OK] Server shutdown completed")


async def preload_market_data(wait_for_completion: bool = None, timeout: int = None):
    """启动时使用智能更新管理器预加载市场数据（K线、指数、财务数据）
    
    Args:
        wait_for_completion: 是否等待所有更新完成（从配置读取）
        timeout: 等待超时时间（秒，从配置读取）
    """
    # 从配置读取参数
    if wait_for_completion is None:
        wait_for_completion = settings.preload_wait_for_completion
    if timeout is None:
        timeout = settings.preload_timeout_seconds
    
    # 延迟导入避免循环依赖
    from database import get_db
    from services.data_update_manager import data_update_manager
    from services.background_updater import background_updater
    from routers.holding import holding_manager
    from routers.stock import CN_INDICES, SECTOR_INDEX_MAP
    from services.stock_data_service import stock_data_service
    from services.websocket_manager import manager
    import json
    
    _preload_state['status'] = 'syncing'
    _preload_state['progress'] = 0
    _preload_state['message'] = '开始同步市场数据'
    _preload_state['error'] = None
    _preload_state['updated_at'] = datetime.now().isoformat()

    async def broadcast_progress(message: str, progress: dict = None):
        """广播进度消息到WebSocket（带节流和容错处理）"""
        stage = (progress or {}).get('stage')
        if stage == 'complete':
            _preload_state['status'] = 'ready'
            _preload_state['progress'] = 100
        elif stage == 'error':
            _preload_state['status'] = 'pending'
            _preload_state['progress'] = 0
            _preload_state['error'] = (progress or {}).get('error') or message
        else:
            _preload_state['status'] = 'syncing'
            total = (progress or {}).get('total') or 0
            current = (progress or {}).get('current') or 0
            if total > 0:
                _preload_state['progress'] = min(99, int((current / total) * 100))
            else:
                _preload_state['progress'] = min(99, _preload_state.get('progress', 0))
        _preload_state['message'] = message
        _preload_state['updated_at'] = datetime.now().isoformat()

        try:
            # 节流控制：每秒最多 5 次广播
            if not await _broadcast_throttler.should_broadcast():
                # 如果被节流，只记录到日志，不发送
                logger.debug(f"Broadcast throttled: {message}")
                return
            
            # 检查 manager 是否已启动且有活跃连接
            if not hasattr(manager, 'active_connections') or not manager.active_connections:
                logger.debug(f"WebSocket not ready or no connections, skipping broadcast: {message}")
                return
            
            await manager.broadcast({
                'type': 'startup_progress',
                'message': message,
                'progress': progress,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            # 广播失败不应阻塞主流程
            logger.debug(f"Broadcast progress failed (non-blocking): {str(e)}")
    
    try:
        logger.debug("开始智能预加载市场数据...")
        
        await broadcast_progress("开始加载股票数据...", {'stage': 'init'})
        
        # 1. 收集所有需要更新的代码
        stock_codes = []
        index_codes = []
        
        # 1.1 获取自持股票代码
        holdings = await holding_manager.load_holdings()
        if holdings and holdings.sectors:
            for sector in holdings.sectors:
                for stock in sector.stocks:
                    if stock.code and stock.code != 'UNKNOWN':
                        stock_codes.append(stock.code)
        
        # 1.2 获取指数代码（从配置文件和内置列表）
        # 1.2.1 从配置文件读取
        indices_config_path = settings.data_dir / "indices_config.json"
        if indices_config_path.exists():
            try:
                with open(indices_config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    for idx in config.get('indices', []):
                        code = idx.get('full_code') or idx.get('code')
                        index_codes.append(code)
            except Exception as e:
                logger.warning(f"读取指数配置文件失败: {str(e)}")
        
        # 1.2.2 添加内置指数
        for code in CN_INDICES.keys():
            if code not in index_codes:
                index_codes.append(code)
        
        # 1.2.3 添加行业板块指数
        for code in SECTOR_INDEX_MAP.values():
            if code not in index_codes:
                index_codes.append(code)
        
        # 1.3 添加美股指数
        us_indices = ['^GSPC', '^IXIC', '^DJI', '^VIX', '^N225', '^KS11']
        
        all_codes = stock_codes + index_codes
        
        if not all_codes and not us_indices:
            logger.info("没有需要更新的数据，跳过预加载")
            await broadcast_progress("没有需要更新的数据", {'stage': 'complete'})
            return
        
        logger.debug(f"发现 {len(stock_codes)} 只股票, {len(index_codes)} 个国内指数, {len(us_indices)} 个美股指数")
        
        await broadcast_progress(f"检查 {len(all_codes)} 项数据更新状态...", {'stage': 'check', 'total': len(all_codes)})
        
        # 2. 更新 K 线数据 (CN 股票 + 国内指数)
        update_status = await data_update_manager.get_all_update_status(all_codes, 'kline')
        needs_update_count = update_status['needs_update_count']
        
        # 2.1 筛选需要更新的股票并按策略排序
        # 策略：1. 优先更新本地没有数据的股票 (last_update is None)
        #       2. 其他股票按最后更新时间升序排列 (最久未更新的优先)
        items_to_update = [
            item for item in update_status['stocks'] 
            if item['needs_update']
        ]
        
        # 执行排序
        items_to_update.sort(key=lambda x: (
            x['last_update'] is not None,  # None (False) comes first
            x['last_update'] if x['last_update'] is not None else datetime.min
        ))
        
        codes_to_update = [item['stock_code'] for item in items_to_update]
        
        if codes_to_update:
            logger.debug(f"更新队列已排序: 优先更新 {sum(1 for x in items_to_update if x['last_update'] is None)} 只新股票")
        
        # 3. 提交美股指数更新任务 (后台)
        for symbol in us_indices:
            await background_updater.submit_us_index_update_task(symbol)
        
        # 4. 提交财务数据更新任务 (后台)
        for code in stock_codes:
            # 提交基础财务指标更新任务（包含年报和季报）
            await background_updater.submit_fundamental_update_task(code)
        
        if not codes_to_update:
            logger.debug("[OK] K线数据均已是最新")
            await broadcast_progress("K线数据已是最新，已提交其他后台更新", {'stage': 'complete', 'updated': 0})
            if not wait_for_completion:
                return
        
        if not wait_for_completion:
            # 非阻塞模式：提交后台任务后立即返回
            logger.debug("使用后台任务模式更新 K线数据...")
            await broadcast_progress(f"提交 {len(codes_to_update)} 个后台更新任务...", {'stage': 'background'})
            result = await background_updater.submit_batch_update(codes_to_update, 'day', force=False)
            return
        
        # 阻塞模式：同步更新 K 线数据
        logger.info(f"⏳ 正在预加载 {len(codes_to_update)} 项 K线数据...")
        
        start_time = asyncio.get_event_loop().time()
        
        # 进度跟踪变量
        progress_state = {
            'current': 0,
            'success': 0,
            'failed': 0,
            'timeout': 0,
            'current_code': '',
            'lock': asyncio.Lock()
        }
        
        # 并发执行更新，限制并发数以避免 SQLite 锁定
        semaphore = asyncio.Semaphore(3)  # 降低到3，防止 database is locked
        
        async def update_with_semaphore(code):
            async with semaphore:
                # 检查是否超时
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > timeout:
                    return None
                
                # 更新当前正在处理的股票
                async with progress_state['lock']:
                    progress_state['current_code'] = code
                
                async with async_session_maker() as db:
                    try:
                        result = await stock_data_service.update_stock_kline(db, code, 'day', force_full=False)
                        
                        # 更新进度
                        async with progress_state['lock']:
                            progress_state['current'] += 1
                            if result and result.get('success'):
                                progress_state['success'] += 1
                            else:
                                progress_state['failed'] += 1
                            
                            # 使用 logger 记录进度，避免同步 print
                            if progress_state['current'] % 10 == 0 or progress_state['current'] == len(codes_to_update):
                                logger.info(f"进度: {progress_state['current']}/{len(codes_to_update)} "
                                          f"(成功:{progress_state['success']}, 失败:{progress_state['failed']})")
                            
                            # 推送进度更新（异步，不阻塞）
                            await broadcast_progress(
                                f"更新 {code} 完成 ({progress_state['current']}/{len(codes_to_update)})",
                                {
                                    'stage': 'updating',
                                    'total': len(codes_to_update),
                                    'current': progress_state['current'],
                                    'success': progress_state['success'],
                                    'failed': progress_state['failed'],
                                    'current_code': code,
                                    'elapsed': round(asyncio.get_event_loop().time() - start_time, 1)
                                }
                            )
                        
                        return result
                    except Exception as e:
                        logger.error(f"  [ERROR] {code}: 更新失败 - {str(e)}")
                        
                        # 更新失败进度
                        async with progress_state['lock']:
                            progress_state['current'] += 1
                            progress_state['failed'] += 1
                            
                            # 推送进度更新（异步，不阻塞）
                            await broadcast_progress(
                                f"更新 {code} 失败 ({progress_state['current']}/{len(codes_to_update)})",
                                {
                                    'stage': 'updating',
                                    'total': len(codes_to_update),
                                    'current': progress_state['current'],
                                    'success': progress_state['success'],
                                    'failed': progress_state['failed'],
                                    'current_code': code,
                                    'error': str(e),
                                    'elapsed': round(asyncio.get_event_loop().time() - start_time, 1)
                                }
                            )
                        
                        return None

        # 创建任务列表
        tasks = [update_with_semaphore(code) for code in codes_to_update]
        
        # 并发执行
        results = await asyncio.gather(*tasks)
        
        updated_count = progress_state['success']
        failed_count = progress_state['failed']
        timeout_count = sum(1 for r in results if r is None)
        
        if timeout_count > 0:
            logger.warning(f"[WARN] {timeout_count} 项任务超时，将由后台继续处理")
            # 提交超时任务到后台
            timed_out_codes = [code for i, code in enumerate(codes_to_update) if results[i] is None]
            if timed_out_codes:
                await background_updater.submit_batch_update(timed_out_codes, 'day', force=False)

        
        elapsed = asyncio.get_event_loop().time() - start_time
        logger.debug(f"K线数据更新完成: 成功 {updated_count}, 失败 {failed_count}, 耗时 {elapsed:.1f}秒")
        
        # [START] 新增：将K线数据预加载到内存缓存（批量优化）
        logger.debug("开始预热K线内存缓存...")
        
        try:
            from services.kline_cache import kline_cache
            
            # 预热所有自持股票和指数的K线数据
            all_preload_codes = stock_codes + index_codes
            preload_count = 0
            
            # 批量查询优化：一次性查询所有股票的最近 100 根 K 线
            async with async_session_maker() as db:
                try:
                    # 使用快速失败机制：5 秒超时
                    async with asyncio.timeout(5.0):
                        # 批量查询所有股票的最新数据
                        # 策略：按股票代码分组，每组取最新 100 条
                        stmt = (
                            select(StockKLineData)
                            .where(
                                and_(
                                    StockKLineData.stock_code.in_(all_preload_codes),
                                    StockKLineData.period == 'day'
                                )
                            )
                            .order_by(
                                StockKLineData.stock_code,
                                desc(StockKLineData.trade_date)
                            )
                        )
                        
                        result = await db.execute(stmt)
                        all_records = result.scalars().all()
                        
                        # 按股票代码分组
                        records_by_code = defaultdict(list)
                        for record in all_records:
                            records_by_code[record.stock_code].append(record)
                        
                        # 为每只股票只保留最近 100 条
                        for code in all_preload_codes:
                            records = records_by_code.get(code, [])[:100]
                            
                            if records:
                                # 转换为缓存格式
                                cache_data = [
                                    {
                                        'code': r.stock_code,
                                        'date': r.trade_date.strftime('%Y-%m-%d'),
                                        'open': float(r.open),
                                        'close': float(r.close),
                                        'high': float(r.high),
                                        'low': float(r.low),
                                        'volume': int(r.volume) if r.volume else 0,
                                        'amount': float(r.amount) if r.amount else 0.0
                                    }
                                    for r in reversed(records)  # 从旧到新排序
                                ]
                                
                                # 存入内存缓存
                                await kline_cache.set(code, cache_data, 'day', 100)
                                preload_count += 1
                    
                except asyncio.TimeoutError:
                    logger.error("[ERROR] K线缓存预热超时 (5s)，降级为从缓存读取")
                    # 快速失败：不阻塞启动，后续请求会触发缓存加载
                except Exception as e:
                    logger.warning(f"批量查询K线数据失败: {str(e)}")
            
            logger.debug(f"[OK] K线内存缓存预热完成: {preload_count}/{len(all_preload_codes)} 只股票")
        
        except Exception as e:
            logger.warning(f"K线内存缓存预热失败: {str(e)}")
        
        # [START] 新增：预计算自持股票的PMR数据
        logger.debug("开始预计算PMR数据...")
        
        try:
            pmr_result = await background_updater.precompute_pmr_for_holdings()
            
            if pmr_result['success']:
                logger.debug(f"[OK] PMR预计算完成: 成功 {pmr_result['precomputed_count']}, 失败 {pmr_result['failed_count']}")
            else:
                logger.warning(f"PMR预计算失败: {pmr_result.get('error', '未知错误')}")
        except Exception as e:
            logger.warning(f"PMR预计算失败: {str(e)}")
        
        await broadcast_progress("核心数据预加载完成", {
            'stage': 'complete',
            'updated': updated_count,
            'failed': failed_count,
            'elapsed': round(elapsed, 1),
            'cached': preload_count if 'preload_count' in locals() else 0
        })
        
    except Exception as e:
        logger.error(f"智能预加载市场数据失败: {str(e)}", exc_info=True)
        logger.warning("[WARN] 将在后台继续尝试更新...")
        _preload_state['status'] = 'pending'
        _preload_state['progress'] = 0
        _preload_state['message'] = '数据预加载失败'
        _preload_state['error'] = str(e)
        _preload_state['updated_at'] = datetime.now().isoformat()
        await broadcast_progress(f"预加载失败: {str(e)}", {'stage': 'error', 'error': str(e)})
        try:
            if hasattr(manager, 'active_connections') and manager.active_connections:
                await manager.broadcast({
                    'type': 'initial_sync_error',
                    'message': '数据加载失败，请检查数据库连接',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        except Exception:
            pass


# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="以自持股票.md为核心的智能股票分析平台",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加日志记录中间件
app.add_middleware(LoggingMiddleware)

# 添加响应标准化中间件
app.add_middleware(ResponseStandardizationMiddleware)
app.add_middleware(ExceptionHandlerMiddleware)

# 定时任务状态
@app.get("/api/scheduler/jobs")
async def get_scheduler_jobs():
    """获取定时任务列表"""
    from services.scheduler import task_scheduler
    return {
        "is_running": task_scheduler.is_running,
        "jobs": task_scheduler.get_jobs_info()
    }


@app.get("/api/initial_data")
async def get_initial_data():
    from services.stock_data_service import stock_data_service

    sectors = await stock_data_service.get_sectors_from_cache()
    holdings_payload = {
        "sectors": [sector.model_dump() for sector in sectors],
        "last_updated": datetime.now().isoformat() if sectors else None
    }

    sync_status = _derive_sync_status()
    if sectors and sync_status != 'ready':
        sync_status = 'syncing'

    return {
        "holdings": holdings_payload,
        "sync_status": sync_status,
        "sync_progress": int(_preload_state.get('progress') or 0),
        "sync_message": _preload_state.get('message') or "",
        "sync_error": _preload_state.get('error')
    }


# 健康检查端点
@app.get("/health", tags=["健康检查"])
async def health_check():
    """Health check endpoint with database pool and Feishu connection status
    
    Returns:
        Health status including database pool metrics and Feishu long connection heartbeat status
    """
    from services.feishu_bot import feishu_long_connection_service
    from database.operations.db_health import check_database_health
    import time
    
    # Check database health with connection pool details
    db_health = await check_database_health()
    
    # Check Feishu long connection status
    feishu_alive = feishu_long_connection_service.is_alive()
    last_heartbeat = feishu_long_connection_service.get_last_heartbeat()
    current_time = time.time()
    
    # Determine overall status
    overall_healthy = db_health.get("status") == "healthy" and feishu_alive
    
    status = {
        "status": "healthy" if overall_healthy else "degraded",
        "timestamp": datetime.now().isoformat(),
        "app_name": settings.app_name,
        "version": settings.app_version,
        "services": {
            "database": db_health,  # Detailed database pool info
            "websocket": "active",
            "feishu_long_connection": {
                "alive": feishu_alive,
                "last_heartbeat": last_heartbeat,
                "seconds_since_heartbeat": round(current_time - last_heartbeat, 2) if last_heartbeat > 0 else None,
                "running": feishu_long_connection_service._running
            }
        }
    }
    
    if not feishu_alive and feishu_long_connection_service._running:
        status["status"] = "degraded"
        status["warning"] = "Feishu long connection thread is running but heartbeat timeout"
        logger.warning(f"[WARN]️ Feishu long connection heartbeat timeout: {current_time - last_heartbeat:.1f}s")
    
    if db_health.get("status") != "healthy":
        status["status"] = "unhealthy"
        logger.error(f"[ERROR] Database health check failed: {db_health.get('error')}")
    
    return status


# 预加载状态端点（供前端查询同步状态）
@app.get("/api/sync-status", tags=["同步状态"])
async def get_sync_status():
    """获取数据预加载同步状态
    
    Returns:
        sync_status: pending | syncing | ready | error
        progress: 0-100
        message: 状态描述
    """
    return {
        "sync_status": _derive_sync_status(),
        "progress": int(_preload_state.get("progress") or 0),
        "message": _preload_state.get("message") or "",
        "error": _preload_state.get("error"),
        "updated_at": _preload_state.get("updated_at"),
        "timestamp": datetime.now().isoformat()
    }

# 注册所有路由 (按顺序，避免路径覆盖)
from routers.holding import router as holding_router
from routers.stock import router as stock_router
from routers.fundamental import router as fundamental_router
from routers.us_market import router as us_market_router
from routers.prediction import router as prediction_router
from routers.report import router as report_router
from routers.websocket import router as websocket_router
from routers.alert import router as alert_router
from routers.news import router as news_router
from routers.config import router as config_router
from routers.status import router as status_router
from routers.market_data import router as market_data_router
from routers.kline_fast import router as kline_fast_router
from routers.data_update import router as data_update_router
from routers.force_index import router as force_index_router
from routers.mcp import router as mcp_router
from routers.holdings import router as holdings_management_router
from routers.feishu import router as feishu_router
from routers.feishu_chat import router as feishu_chat_router
from routers.console_config import router as console_config_router

# 1. 核心业务路由 (带特定前缀，应优先匹配)
app.include_router(holding_router, prefix="/api/holdings", tags=["持仓管理"])
app.include_router(holdings_management_router, prefix="/api/holdings-management", tags=["持仓管理操作"])
app.include_router(stock_router, prefix="/api/stocks", tags=["股票行情"])
app.include_router(fundamental_router, prefix="/api/fundamental", tags=["基本面分析"])
app.include_router(us_market_router, prefix="/api/us-market", tags=["美股市场分析"])
app.include_router(prediction_router, prefix="/api/predictions", tags=["预测分析"])
app.include_router(report_router, prefix="/api/reports", tags=["每日分析报告"])
app.include_router(alert_router, prefix="/api/alerts", tags=["预警管理"])
app.include_router(news_router, prefix="/api/news", tags=["新闻资讯"])
app.include_router(market_data_router, prefix="/api/market", tags=["市场数据"])
app.include_router(kline_fast_router, prefix="/api/stocks", tags=["快速K线"])
app.include_router(data_update_router, prefix="/api/data", tags=["数据更新"])
app.include_router(client_logs_router, prefix="/api/client-logs", tags=["客户端日志"])
app.include_router(force_index_router, prefix="/api/indicators", tags=["技术指标"])
app.include_router(daily_watchlist_router, prefix="/api/daily-watchlist", tags=["每日关注"])
app.include_router(price_alerts_router, prefix="/api/price-alerts", tags=["价格提醒"])
app.include_router(mcp_router, prefix="/api/mcp", tags=["MCP接口"])
app.include_router(feishu_router, prefix="/api", tags=["飞书机器人"])
app.include_router(feishu_chat_router, prefix="/api", tags=["飞书对话历史"])

# 2. 系统管理和配置路由
app.include_router(websocket_router, tags=["WebSocket"])
app.include_router(config_router, prefix="/api/config", tags=["系统配置"])
app.include_router(status_router, tags=["系统状态"])
app.include_router(console_config_router, prefix="/api/config", tags=["控制台配置"])
app.include_router(settings_router, tags=["系统设置"])
app.include_router(cache_router, prefix="/api", tags=["缓存管理"])

# 3. 兜底路由 (放在最后，避免拦截其他路径)
# fundamental.router 包含 /{stock_code}，应谨慎使用
# 已在上方以 /api/fundamental 前缀注册，如需保持兼容，可按需添加兜底
# app.include_router(fundamental_router, prefix="/api", tags=["基本面分析-兜底"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=False,
        log_level="debug" if settings.debug else "info"
    )
