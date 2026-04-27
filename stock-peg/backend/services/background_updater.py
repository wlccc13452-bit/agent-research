"""后台异步更新服务"""
import logging
import asyncio
from typing import Dict, Optional, List
from datetime import datetime, date, timedelta

from database.session import async_session_maker
from services.data_update_manager import data_update_manager
from services.websocket_manager import manager as websocket_manager
from services.stock_data_service import stock_data_service
from services.quote_data_service import quote_data_service
from services.stock_service import StockService
from services.fundamental_analyzer import FundamentalAnalyzer
from services.us_market_analyzer import USMarketDataService
from services.debug_log_manager import debug_log_manager
from services.force_index_calculator import force_index_calculator
from config.settings import settings

logger = logging.getLogger(__name__)


class BackgroundUpdater:
    """后台异步更新服务"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BackgroundUpdater, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # 后台任务字典
        # 格式：{task_id: asyncio.Task}
        self.background_tasks: Dict[str, asyncio.Task] = {}
        
        # 任务状态字典
        # 格式：{task_id: {'status': str, 'stock_code': str, 'started_at': datetime}}
        self.task_status: Dict[str, Dict] = {}
        
        # 最大并发任务数（从配置读取）
        self.max_concurrent_tasks = settings.max_concurrent_tasks
        
        # 任务超时时间（秒，从配置读取）
        self.task_timeout = settings.task_timeout_seconds
        
        # 并发控制信号量
        self._semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
        
        # 扫描任务锁，防止多个扫描任务并发运行
        self._scan_lock = asyncio.Lock()
        
        self._initialized = True
        # 减少控制台输出
        # logger.info("BackgroundUpdater 初始化完成")
    
    def generate_task_id(self, stock_code: str, data_type: str) -> str:
        """生成任务ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"{stock_code}_{data_type}_{timestamp}"
    
    async def resolve_unknown_stock_code(self, stock_name: str, stock_id: int, old_code: str = None) -> Optional[str]:
        """重新解析UNKNOWN股票代码
        
        Args:
            stock_name: 股票名称
            stock_id: 数据库中的股票ID
            old_code: 原始的UNKNOWN代码（可选，用于推送通知）
            
        Returns:
            解析成功返回股票代码，否则返回None
        """
        try:
            from datasource import get_datasource, DataSourceType
            from database.operations.watchlist_ops import update_watchlist_stock
            
            akshare_source = get_datasource().get_source(DataSourceType.AKSHARE)
            if not akshare_source or not await akshare_source.is_available():
                logger.warning(f"Datasource 服务不可用，无法重新解析股票代码: {stock_name}")
                return None
            
            # 尝试通过名称搜索股票代码
            code = await akshare_source.search_stock_by_name(stock_name)
            
            if code and not code.startswith('UNKNOWN'):
                # 成功解析，更新数据库
                async with async_session_maker() as db:
                    # 1. 更新daily_watchlist表
                    updated = await update_watchlist_stock(
                        db, 
                        stock_id=stock_id,
                        stock_code=code
                    )
                    
                    if updated:
                        logger.info(f"[OK] 成功重新解析并更新股票代码: {stock_name} -> {code}")
                        
                        # 2. 级联更新所有历史数据表
                        if old_code:
                            try:
                                from database.operations import migrate_stock_code

                                # 使用 ops 层进行批量更新
                                update_results = await migrate_stock_code(db, old_code, code)

                                # 提交事务
                                await db.commit()

                                logger.info(
                                    f"[OK] 级联更新完成: K线={update_results['kline_count']}, "
                                    f"基本面={update_results['fundamental_count']}, "
                                    f"财务={update_results['financial_count']}, "
                                    f"行情={update_results['quote_count']}, "
                                    f"ForceIndex={update_results['force_count']}, "
                                    f"日志={update_results['log_count']}"
                                )

                            except Exception as e:
                                logger.error(f"级联更新失败: {str(e)}")
                                # 即使级联更新失败，也继续执行后续流程
                        
                        # 3. 推送代码更新通知
                        if old_code:
                            try:
                                await websocket_manager.broadcast({
                                    'type': 'stock_code_updated',
                                    'old_code': old_code,
                                    'new_code': code,
                                    'stock_name': stock_name,
                                    'stock_id': stock_id,
                                    'timestamp': datetime.now().isoformat()
                                })
                                logger.info(f"[OK] 已推送代码更新通知: {old_code} -> {code}")
                            except Exception as e:
                                logger.error(f"推送代码更新通知失败: {str(e)}")
                        
                        return code
                    else:
                        logger.error(f"更新数据库失败: stock_id={stock_id}")
                        return None
            else:
                logger.debug(f"未能解析股票代码: {stock_name}")
                return None
                
        except Exception as e:
            logger.error(f"重新解析股票代码失败 {stock_name}: {str(e)}")
            return None
    
    async def submit_kline_update_task(self, stock_code: str, period: str = 'day', 
                                       force: bool = False) -> Dict:
        """提交K线更新任务
        
        Returns:
            {
                'success': bool,
                'task_id': str,
                'message': str
            }
        """
        # 验证股票代码
        if not stock_code:
            return {
                'success': False,
                'task_id': None,
                'message': '股票代码为空'
            }
        
        # 如果是UNKNOWN代码，尝试重新解析
        if stock_code.startswith('UNKNOWN'):
            logger.info(f"检测到UNKNOWN代码，尝试重新解析: {stock_code}")
            
            # 查询数据库获取股票名称和ID
            try:
                from database.operations.watchlist_ops import get_watchlist_by_stock
                async with async_session_maker() as db:
                    stocks = await get_watchlist_by_stock(db, stock_code)
                    
                    if stocks:
                        # 取最新的记录
                        stock = stocks[0]
                        stock_name = stock.stock_name
                        stock_id = stock.id
                        
                        # 尝试重新解析
                        resolved_code = await self.resolve_unknown_stock_code(stock_name, stock_id)
                        
                        if resolved_code:
                            # 成功解析，使用新代码继续
                            stock_code = resolved_code
                            logger.info(f"[OK] 已将股票代码从UNKNOWN更新为: {resolved_code}")
                        else:
                            return {
                                'success': False,
                                'task_id': None,
                                'message': f'无法解析股票代码: {stock_name}'
                            }
                    else:
                        return {
                            'success': False,
                            'task_id': None,
                            'message': f'数据库中未找到UNKNOWN股票: {stock_code}'
                        }
            except Exception as e:
                logger.error(f"查询UNKNOWN股票失败: {str(e)}")
                return {
                    'success': False,
                    'task_id': None,
                    'message': f'查询数据库失败: {str(e)}'
                }
            
        try:
            # 检查是否已有该股票的更新任务
            existing_task_id = None
            for tid, status in self.task_status.items():
                if status.get('stock_code') == stock_code and status.get('status') == 'running':
                    existing_task_id = tid
                    break
            
            if existing_task_id:
                # 减少控制台输出，写入任务日志
                # logger.info(f"股票 {stock_code} 已有更新任务运行中: {existing_task_id}")
                return {
                    'success': False,
                    'task_id': existing_task_id,
                    'message': '更新任务已运行中'
                }
            
            # 检查并发任务数限制（仅记录，不再直接拒绝，改为使用信号量排队）
            running_tasks = sum(1 for s in self.task_status.values() if s.get('status') == 'running')
            if running_tasks >= self.max_concurrent_tasks:
                logger.debug(f"当前运行任务数 ({running_tasks}) 已达并发上限，新任务将排队等待")
            
            # 检查更新锁
            if not data_update_manager.acquire_lock(stock_code):
                # 减少控制台输出
                # logger.info(f"股票 {stock_code} 更新锁被占用")
                return {
                    'success': False,
                    'task_id': None,
                    'message': '更新锁被占用'
                }
            
            # 生成任务ID
            task_id = self.generate_task_id(stock_code, 'kline')
            
            # 创建后台任务
            task = asyncio.create_task(
                self._execute_kline_update(task_id, stock_code, period, force)
            )
            
            self.background_tasks[task_id] = task
            self.task_status[task_id] = {
                'status': 'pending',
                'stock_code': stock_code,
                'data_type': 'kline',
                'started_at': datetime.now()
            }
            
            # 减少控制台输出
            # logger.info(f"已提交K线更新任务: {task_id}, stock_code={stock_code}")
            
            return {
                'success': True,
                'task_id': task_id,
                'message': '更新任务已提交'
            }
            
        except Exception as e:
            logger.error(f"提交K线更新任务失败: {str(e)}")
            data_update_manager.release_lock(stock_code)
            return {
                'success': False,
                'task_id': None,
                'message': f'提交任务失败: {str(e)}'
            }

    async def submit_fundamental_update_task(self, stock_code: str) -> Dict:
        """提交财务数据更新任务"""
        # 验证股票代码
        if not stock_code:
            return {
                'success': False,
                'task_id': None,
                'message': '股票代码为空'
            }
        
        # 如果是UNKNOWN代码，尝试重新解析
        if stock_code.startswith('UNKNOWN'):
            logger.info(f"检测到UNKNOWN代码，尝试重新解析: {stock_code}")
            
            # 保存原始代码用于推送通知
            old_code = stock_code
            
            # 查询数据库获取股票名称和ID
            try:
                from database.operations.watchlist_ops import get_watchlist_by_stock
                async with async_session_maker() as db:
                    stocks = await get_watchlist_by_stock(db, stock_code)
                    
                    if stocks:
                        # 取最新的记录
                        stock = stocks[0]
                        stock_name = stock.stock_name
                        stock_id = stock.id
                        
                        # 尝试重新解析（传入原始代码用于推送）
                        resolved_code = await self.resolve_unknown_stock_code(stock_name, stock_id, old_code)
                        
                        if resolved_code:
                            # 成功解析，使用新代码继续
                            stock_code = resolved_code
                            logger.info(f"[OK] 已将股票代码从UNKNOWN更新为: {resolved_code}")
                        else:
                            return {
                                'success': False,
                                'task_id': None,
                                'message': f'无法解析股票代码: {stock_name}'
                            }
                    else:
                        return {
                            'success': False,
                            'task_id': None,
                            'message': f'数据库中未找到UNKNOWN股票: {stock_code}'
                        }
            except Exception as e:
                logger.error(f"查询UNKNOWN股票失败: {str(e)}")
                return {
                    'success': False,
                    'task_id': None,
                    'message': f'查询数据库失败: {str(e)}'
                }
            
        try:
            # 检查是否已有该股票的更新任务
            for tid, status in self.task_status.items():
                if status.get('stock_code') == stock_code and status.get('data_type') == 'financial' and status.get('status') == 'running':
                    return {'success': False, 'task_id': tid, 'message': '财务更新任务已运行中'}
            
            # 检查更新锁
            if not data_update_manager.acquire_lock(stock_code):
                return {'success': False, 'task_id': None, 'message': '更新锁被占用'}
            
            # 生成任务ID
            task_id = self.generate_task_id(stock_code, 'financial')
            
            # 创建后台任务
            task = asyncio.create_task(self._execute_fundamental_update(task_id, stock_code))
            
            self.background_tasks[task_id] = task
            self.task_status[task_id] = {
                'status': 'pending',
                'stock_code': stock_code,
                'data_type': 'financial',
                'started_at': datetime.now()
            }
            
            return {'success': True, 'task_id': task_id, 'message': '财务更新任务已提交'}
            
        except Exception as e:
            logger.error(f"提交财务更新任务失败: {str(e)}")
            data_update_manager.release_lock(stock_code)
            return {'success': False, 'task_id': None, 'message': f'提交任务失败: {str(e)}'}

    async def submit_us_index_update_task(self, symbol: str) -> Dict:
        """提交美股指数更新任务"""
        try:
            # 检查是否已有该指数的更新任务
            for tid, status in self.task_status.items():
                if status.get('stock_code') == symbol and status.get('data_type') == 'us_index' and status.get('status') == 'running':
                    return {'success': False, 'task_id': tid, 'message': '美股指数更新任务已运行中'}
            
            # 检查更新锁
            if not data_update_manager.acquire_lock(symbol):
                return {'success': False, 'task_id': None, 'message': '更新锁被占用'}
            
            # 生成任务ID
            task_id = self.generate_task_id(symbol, 'us_index')
            
            # 创建后台任务
            task = asyncio.create_task(self._execute_us_index_update(task_id, symbol))
            
            self.background_tasks[task_id] = task
            self.task_status[task_id] = {
                'status': 'pending',
                'stock_code': symbol,
                'data_type': 'us_index',
                'started_at': datetime.now()
            }
            
            return {'success': True, 'task_id': task_id, 'message': '美股指数更新任务已提交'}
            
        except Exception as e:
            logger.error(f"提交美股指数更新任务失败: {str(e)}")
            data_update_manager.release_lock(symbol)
            return {'success': False, 'task_id': None, 'message': f'提交任务失败: {str(e)}'}
    
    async def submit_quote_update_task(self, stock_code: str) -> Dict:
        """
        提交行情数据更新任务
        
        Returns:
            {
                'success': bool,
                'task_id': str,
                'message': str
            }
        """
        try:
            # 检查是否已有该股票的更新任务
            for tid, status in self.task_status.items():
                if status.get('stock_code') == stock_code and status.get('data_type') == 'quote' and status.get('status') == 'running':
                    return {'success': False, 'task_id': tid, 'message': '行情更新任务已运行中'}
            
            # 检查更新锁
            if not data_update_manager.acquire_lock(stock_code):
                return {'success': False, 'task_id': None, 'message': '更新锁被占用'}
            
            # 生成任务ID
            task_id = self.generate_task_id(stock_code, 'quote')
            
            # 创建后台任务
            task = asyncio.create_task(
                self._execute_quote_update(task_id, stock_code)
            )
            
            self.background_tasks[task_id] = task
            self.task_status[task_id] = {
                'status': 'pending',
                'stock_code': stock_code,
                'data_type': 'quote',
                'started_at': datetime.now()
            }
            
            logger.info(f"已提交行情更新任务: {task_id}, stock_code={stock_code}")
            
            return {
                'success': True,
                'task_id': task_id,
                'message': '更新任务已提交'
            }
            
        except Exception as e:
            logger.error(f"提交行情更新任务失败: {str(e)}")
            data_update_manager.release_lock(stock_code)
            return {
                'success': False,
                'task_id': None,
                'message': f'提交任务失败: {str(e)}'
            }
    
    async def _execute_kline_update(self, task_id: str, stock_code: str, 
                                   period: str, force: bool):
        """执行K线更新"""
        log_id = None
        
        # 使用信号量限制并发执行，但不阻塞任务提交
        async with self._semaphore:
            # 创建任务日志
            debug_task_id = debug_log_manager.start_task(
                'background_update',
                f'K线更新 {stock_code}',
                {'stock_code': stock_code, 'period': period, 'force': force, 'task_id': task_id}
            )
            
            try:
                # 更新任务状态
                self.task_status[task_id]['status'] = 'running'
                debug_log_manager.log_debug(debug_task_id, '开始执行K线更新任务')
                
                # 记录更新开始
                log_id = await data_update_manager.record_update_start(
                    stock_code, 'kline', 'auto'
                )
                
                async with async_session_maker() as db:
                    # 执行K线更新
                    result = await stock_data_service.update_stock_kline(
                        db, stock_code, period, force_full=force
                    )
                    
                    if result['success']:
                        updated_records = result.get('saved_count', result.get('records_updated', 0))
                        latest_local_klines = await stock_data_service.get_kline_from_db(
                            db, stock_code, period, 120
                        )
                        local_kline_payload = [
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
                            for k in latest_local_klines
                        ]
                        # 更新日志
                        await data_update_manager.record_update_complete(
                            log_id, updated_records
                        )
                        
                        # 更新任务状态
                        self.task_status[task_id]['status'] = 'completed'
                        self.task_status[task_id]['completed_at'] = datetime.now()
                        
                        # WebSocket推送落库后的本地数据
                        await websocket_manager.broadcast_to_stock(stock_code, {
                            'type': 'kline_updated',
                            'stock_code': stock_code,
                            'period': period,
                            'local_data_available': len(local_kline_payload) > 0,
                            'local_data_count': len(local_kline_payload),
                            'data': {
                                'kline': local_kline_payload
                            },
                            'task_id': task_id,
                            'records_updated': updated_records,
                            'timestamp': datetime.now().isoformat()
                        })
                        
                        # 计算并推送 Force Index 数据
                        try:
                            # 获取股票名称
                            from routers.holding import holding_manager
                            holdings = await holding_manager.load_holdings()
                            stock_name = stock_code
                            if holdings and holdings.sectors:
                                for sector in holdings.sectors:
                                    for stock in sector.stocks:
                                        if stock.code == stock_code:
                                            stock_name = stock.name
                                            break
                            
                            # 计算 Force Index
                            fi_result = await force_index_calculator.calculate_force_index(
                                db=db,
                                stock_code=stock_code,
                                stock_name=stock_name,
                                period=period,
                                ema_short=2,
                                ema_long=13,
                                count=120,
                                use_cache=False  # 强制重新计算
                            )
                            
                            if fi_result and fi_result.get('recent_data'):
                                # 推送 Force Index 数据
                                await websocket_manager.broadcast_to_stock(stock_code, {
                                    'type': 'force_index_updated',
                                    'stock_code': stock_code,
                                    'stock_name': stock_name,
                                    'period': period,
                                    'data': {
                                        'dates': [item['date'] for item in fi_result['recent_data']],
                                        'rawForceIndex': [item['raw_force_index'] for item in fi_result['recent_data']],
                                        'fi2Ema': [item['fi_short_ema'] for item in fi_result['recent_data']],
                                        'fi13Ema': [item['fi_long_ema'] for item in fi_result['recent_data']]
                                    },
                                    'signals': fi_result.get('signals'),
                                    'trend_analysis': fi_result.get('trend_analysis'),
                                    'timestamp': datetime.now().isoformat()
                                })
                                logger.info(f"Force Index 已推送: {stock_code}")
                        except Exception as fi_error:
                            logger.warning(f"Force Index 计算或推送失败: {str(fi_error)}")
                        
                        logger.info(f"K线更新任务完成: {task_id}, records={updated_records}")
                        
                    else:
                        # 更新失败
                        error_msg = result.get('message', '未知错误')
                        await data_update_manager.record_update_complete(
                            log_id, 0, error_msg
                        )
                        
                        self.task_status[task_id]['status'] = 'failed'
                        self.task_status[task_id]['error'] = error_msg
                        
                        logger.error(f"K线更新任务失败: {task_id}, error={error_msg}")
                        
            except asyncio.CancelledError:
                logger.warning(f"K线更新任务被取消: {task_id}")
                self.task_status[task_id]['status'] = 'cancelled'
                if log_id:
                    await data_update_manager.record_update_complete(log_id, 0, '任务被取消')
                    
            except Exception as e:
                logger.error(f"K线更新任务异常: {task_id}, error={str(e)}", exc_info=True)
                self.task_status[task_id]['status'] = 'failed'
                self.task_status[task_id]['error'] = str(e)
                if log_id:
                    await data_update_manager.record_update_complete(log_id, 0, str(e))
                    
            finally:
                # 释放更新锁
                data_update_manager.release_lock(stock_code)
                debug_log_manager.end_task(debug_task_id, success=self.task_status[task_id]['status'] == 'completed')
                
                # 清理已完成的任务（保留最近100个任务）
                await self._cleanup_completed_tasks()
    
    async def scan_and_update_missing_data(self) -> Dict:
        """
        扫描并发现本地缺失的数据，并立即启动异步更新。
        策略：优先处理完全缺失的数据，然后处理已存在但过期的旧数据。
        包含：市场情绪、K线数据、实时行情、财务数据。
        
        重要：此方法会定期让出控制权，避免阻塞事件循环。
        """
        if self._scan_lock.locked():
            logger.info("🔍 已有扫描任务正在运行中，跳过本次请求")
            return {
                'scanned_count': 0,
                'missing_tasks': 0,
                'outdated_tasks': 0,
                'total_tasks': 0,
                'message': '已有扫描任务正在运行中'
            }
            
        async with self._scan_lock:
            logger.info("[SCAN] Starting full scan for missing/stale data...")
        
        # 让出控制权，确保不阻塞启动
        await asyncio.sleep(0)
        
        # 0. 市场情绪数据回填（最高优先级，因为它是大盘数据）
        sentiment_result = await self.backfill_missing_sentiment_data()
        
        # 让出控制权
        await asyncio.sleep(0)
        
        # 1. 获取所有需要关注的股票代码 (自持股票 + 指数)
        from routers.holding import holding_manager
        from routers.stock import CN_INDICES, SECTOR_INDEX_MAP
        
        holdings = await holding_manager.load_holdings()
        stock_codes = []
        if holdings and holdings.sectors:
            for sector in holdings.sectors:
                for stock in sector.stocks:
                    if stock.code not in stock_codes:
                        stock_codes.append(stock.code)
        
        index_codes = list(CN_INDICES.keys()) + list(SECTOR_INDEX_MAP.values())
        all_codes = list(set(stock_codes + index_codes))
        
        results = {
            'scanned_count': len(all_codes),
            'missing_tasks': 0,
            'outdated_tasks': 0,
            'total_tasks': 0
        }
        
        # 让出控制权
        await asyncio.sleep(0)
        
        # --- K 线数据优先级处理 ---
        kline_status = await data_update_manager.get_all_update_status(all_codes, 'kline')
        
        # 让出控制权
        await asyncio.sleep(0)
        
        # 第一阶段：处理完全缺失的 K 线数据 (最高优先级)
        missing_klines = [s for s in kline_status['stocks'] if s['needs_update'] and s.get('last_update') is None]
        for i, item in enumerate(missing_klines):
            logger.info(f"🆕 发现缺失 K 线数据: {item['stock_code']}, 启动最高优先级更新")
            await self.submit_kline_update_task(item['stock_code'])
            results['missing_tasks'] += 1
            results['total_tasks'] += 1
            # 每5个让出一次控制权
            if (i + 1) % 5 == 0:
                await asyncio.sleep(0)
            
        # 第二阶段：处理过期的 K 线数据
        outdated_klines = [s for s in kline_status['stocks'] if s['needs_update'] and s.get('last_update') is not None]
        # 按最后更新时间升序排列，即最老的先更新
        outdated_klines.sort(key=lambda x: x.get('last_update'))
        for i, item in enumerate(outdated_klines):
            logger.info(f"⏰ 发现过期 K 线数据: {item['stock_code']} (上次更新: {item['last_update']}), 加入队列")
            await self.submit_kline_update_task(item['stock_code'])
            results['outdated_tasks'] += 1
            results['total_tasks'] += 1
            # 每5个让出一次控制权
            if (i + 1) % 5 == 0:
                await asyncio.sleep(0)
            
        # 让出控制权
        await asyncio.sleep(0)
            
        # --- 行情数据优先级处理 ---
        async with async_session_maker() as db:
            for i, code in enumerate(all_codes):
                quote = await quote_data_service.get_quote_from_db(db, code)
                if not quote:
                    logger.info(f"🆕 发现缺失行情数据: {code}, 启动更新")
                    await self.submit_quote_update_task(code)
                    results['missing_tasks'] += 1
                    results['total_tasks'] += 1
                # 每10个让出一次控制权
                if (i + 1) % 10 == 0:
                    await asyncio.sleep(0)
        
        # 让出控制权
        await asyncio.sleep(0)
        
        # --- 财务数据优先级处理 ---
        for i, code in enumerate(stock_codes):
            update_necessity = await data_update_manager.check_update_necessity(code, 'financial')
            if update_necessity['needs_update']:
                is_missing = update_necessity.get('last_update') is None
                prefix = "🆕 缺失" if is_missing else "⏰ 过期"
                logger.info(f"{prefix} 财务数据: {code}, 启动更新")
                await self.submit_fundamental_update_task(code)
                if is_missing:
                    results['missing_tasks'] += 1
                else:
                    results['outdated_tasks'] += 1
                results['total_tasks'] += 1
            # 每5个让出一次控制权
            if (i + 1) % 5 == 0:
                await asyncio.sleep(0)
                
        logger.info(f"[OK] 全量扫描完成: 扫描 {results['scanned_count']} 项, "
                    f"提交任务总数: {results['total_tasks']} (缺失: {results['missing_tasks']}, 过期: {results['outdated_tasks']})")
        if sentiment_result.get('backfilled_count', 0) > 0:
            logger.info(f"[OK] 市场情绪回填: 补齐 {sentiment_result['backfilled_count']} 天, "
                        f"跳过 {sentiment_result.get('skipped_count', 0)} 天, "
                        f"失败 {sentiment_result.get('failed_count', 0)} 天")
        
        return results

    async def backfill_missing_sentiment_data(self, lookback_days: int = 60) -> Dict:
        """
        主动扫描并回填缺失的市场情绪历史数据
        
        策略：
        1. 查询数据库中已有的交易日期
        2. 与最近 N 个工作日对比，找出缺失的日期
        3. 使用 Tushare 逐日回填缺失数据
        4. 推送 WebSocket 通知前端刷新
        
        Args:
            lookback_days: 回溯天数（默认60天）
            
        Returns:
            回填结果统计
        """
        result = {
            'backfilled_count': 0,
            'skipped_count': 0,
            'failed_count': 0,
            'missing_dates': []
        }
        
        try:
            from database.operations.market_sentiment_ops import save_sentiment, get_stored_trade_dates

            # 获取Tushare数据源（通过统一datasource模块）
            from datasource import get_datasource, DataSourceType
            tushare = get_datasource().get_source(DataSourceType.TUSHARE)
            if not tushare or not await tushare.is_available():
                logger.debug("[SENTIMENT] Tushare 数据源不可用，跳过市场情绪回填")
                return result

            # 计算缺失日期
            today = date.today()
            start_date = today - timedelta(days=lookback_days)

            async with async_session_maker() as db:
                # 使用 ops 层获取已有日期
                stored_dates = set(await get_stored_trade_dates(db, start_date))

                # 计算缺失的工作日
                missing_dates: List[date] = []
                current = start_date
                while current <= today:
                    if current.weekday() < 5 and current not in stored_dates:
                        missing_dates.append(current)
                    current += timedelta(days=1)
                
                if not missing_dates:
                    logger.debug("[SENTIMENT] 市场情绪数据完整，无需回填")
                    return result
                
                result['missing_dates'] = [d.isoformat() for d in missing_dates]
                
                # 限制每次回填数量，避免长时间阻塞（最多补10天）
                dates_to_fill = missing_dates[:10]
                if len(missing_dates) > 10:
                    logger.info(f"[SENTIMENT] 发现 {len(missing_dates)} 天缺失，本次先回填最近10天")
                
                # 使用统一datasource模块获取历史市场情绪
                for i, trade_date in enumerate(dates_to_fill):
                    try:
                        # 调用 TushareDataSource 的公共方法（封装在datasource层）
                        sentiment_data = await tushare.get_historical_sentiment(trade_date)
                        
                        if not sentiment_data:
                            # 可能是节假日/非交易日，不计为失败
                            result['skipped_count'] += 1
                            continue
                        
                        success = await save_sentiment(db, sentiment_data, trade_date)
                        if success:
                            result['backfilled_count'] += 1
                            logger.info(f"[SENTIMENT] 回填成功: {trade_date_str}, "
                                        f"总数{total_count}, 涨{up_count}, 跌{down_count}")
                        else:
                            result['failed_count'] += 1
                        
                        # 控制API调用频率
                        await asyncio.sleep(0.5)
                        
                        # 每3次让出控制权，避免阻塞事件循环
                        if (i + 1) % 3 == 0:
                            await asyncio.sleep(0)
                        
                    except Exception as e:
                        logger.error(f"[SENTIMENT] 回填 {trade_date} 失败: {str(e)}")
                        result['failed_count'] += 1
                
                # 回填完成后推送通知
                if result['backfilled_count'] > 0:
                    try:
                        await websocket_manager.broadcast({
                            'type': 'market_sentiment_updated',
                            'backfilled': True,
                            'backfilled_count': result['backfilled_count'],
                            'message': f'已回填 {result["backfilled_count"]} 天市场情绪数据',
                            'timestamp': datetime.now().isoformat()
                        })
                    except Exception as e:
                        logger.warning(f"[SENTIMENT] 推送回填通知失败: {str(e)}")
                    
                    logger.info(f"[SENTIMENT] 回填完成: 补齐 {result['backfilled_count']} 天")
            
        except Exception as e:
            logger.error(f"[SENTIMENT] 市场情绪回填任务异常: {str(e)}", exc_info=True)
        
        return result

    async def _cleanup_completed_tasks(self):
        """清理已完成的任务"""
        # 只保留最近100个任务
        max_tasks = 100
        
        if len(self.task_status) > max_tasks:
            # 按开始时间排序
            sorted_tasks = sorted(
                self.task_status.items(),
                key=lambda x: x[1].get('started_at', datetime.min),
                reverse=True
            )
            
            # 保留最新的100个
            tasks_to_keep = dict(sorted_tasks[:max_tasks])
            
            # 取消并删除旧任务
            for task_id in self.task_status.keys():
                if task_id not in tasks_to_keep:
                    if task_id in self.background_tasks:
                        task = self.background_tasks[task_id]
                        if not task.done():
                            task.cancel()
                        del self.background_tasks[task_id]
            
            self.task_status = tasks_to_keep
            logger.debug(f"清理已完成任务，当前任务数: {len(self.task_status)}")

    async def _execute_quote_update(self, task_id: str, stock_code: str):
        """执行行情更新"""
        debug_task_id = debug_log_manager.start_task(
            'background_update',
            f'行情更新 {stock_code}',
            {'stock_code': stock_code, 'task_id': task_id}
        )
        
        async with self._semaphore:
            try:
                # 更新任务状态
                self.task_status[task_id]['status'] = 'running'
                
                async with async_session_maker() as db:
                    # 执行行情更新
                    result = await quote_data_service.update_stock_quote(db, stock_code)
                    
                    if result['success']:
                        # 获取更新后的行情数据
                        quote = await quote_data_service.get_quote_from_db(db, stock_code)
                        if quote:
                            # WebSocket推送落库后的本地数据
                            # 使用 model_to_json_dict 处理 datetime 序列化
                            from utils.json_utils import model_to_json_dict
                            quote_dict = model_to_json_dict(quote)
                            await websocket_manager.send_stock_quote(stock_code, quote_dict)
                            
                        # 更新任务状态
                        self.task_status[task_id]['status'] = 'completed'
                        self.task_status[task_id]['completed_at'] = datetime.now()
                        
                        logger.info(f"行情更新任务完成: {task_id}")
                    else:
                        # 更新失败
                        error_msg = result.get('message', '未知错误')
                        self.task_status[task_id]['status'] = 'failed'
                        self.task_status[task_id]['error'] = error_msg
                        
                        logger.error(f"行情更新任务失败: {task_id}, error={error_msg}")
                        
            except Exception as e:
                logger.error(f"行情更新任务异常: {task_id}, error={str(e)}", exc_info=True)
                self.task_status[task_id]['status'] = 'failed'
                self.task_status[task_id]['error'] = str(e)
                
            finally:
                # 释放更新锁
                data_update_manager.release_lock(stock_code)
                debug_log_manager.end_task(debug_task_id, success=self.task_status[task_id]['status'] == 'completed')
                
                # 清理已完成的任务
                await self._cleanup_completed_tasks()

    async def _execute_fundamental_update(self, task_id: str, stock_code: str):
        """执行财务数据更新"""
        debug_task_id = debug_log_manager.start_task(
            'background_update',
            f'财务更新 {stock_code}',
            {'stock_code': stock_code, 'task_id': task_id}
        )
        
        async with self._semaphore:
            try:
                self.task_status[task_id]['status'] = 'running'
                
                # 记录更新开始
                log_id = await data_update_manager.record_update_start(stock_code, 'financial', 'auto')
                
                # 执行财务分析（包含年报抓取和数据库保存）
                analyzer = FundamentalAnalyzer()
                # 1. 综合分析（更新基础指标）
                result = await analyzer.analyze_fundamental(stock_code)
                
                # 2. 抓取最新年报/季报并保存
                await analyzer.get_annual_report(stock_code)
                
                # 3. 抓取最近三年季报并保存
                await analyzer.get_quarterly_data(stock_code, years=3)
                
                if result:
                    # 更新日志
                    await data_update_manager.record_update_complete(log_id, 1)
                    
                    self.task_status[task_id]['status'] = 'completed'
                    self.task_status[task_id]['completed_at'] = datetime.now()
                    
                    # WebSocket推送
                    await websocket_manager.broadcast({
                        'type': 'financial_updated',
                        'stock_code': stock_code,
                        'task_id': task_id,
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    raise Exception("财务分析返回空结果")
                    
            except Exception as e:
                logger.error(f"财务更新任务失败: {task_id}, error={str(e)}")
                self.task_status[task_id]['status'] = 'failed'
                self.task_status[task_id]['error'] = str(e)
                if 'log_id' in locals():
                    await data_update_manager.record_update_complete(log_id, 0, str(e))
            finally:
                data_update_manager.release_lock(stock_code)
                debug_log_manager.end_task(debug_task_id, success=self.task_status[task_id]['status'] == 'completed')

    async def _execute_us_index_update(self, task_id: str, symbol: str):
        """执行美股指数更新"""
        debug_task_id = debug_log_manager.start_task(
            'background_update',
            f'美股指数更新 {symbol}',
            {'symbol': symbol, 'task_id': task_id}
        )
        
        async with self._semaphore:
            try:
                self.task_status[task_id]['status'] = 'running'
                
                # 记录更新开始
                log_id = await data_update_manager.record_update_start(symbol, 'us_index', 'auto')
                
                # 获取美股数据 - 强制从真实数据源获取，不使用预设数据
                service = USMarketDataService()
                data = await service.get_us_stock_data(symbol, force_real=True)
                
                if data:
                    # 保存到数据库
                    async with async_session_maker() as db:
                        success = await service.save_us_data_to_db(db, data)
                        if success:
                            await data_update_manager.record_update_complete(log_id, 1)
                            self.task_status[task_id]['status'] = 'completed'
                            self.task_status[task_id]['completed_at'] = datetime.now()
                            
                            # WebSocket推送
                            await websocket_manager.broadcast({
                                'type': 'us_index_updated',
                                'symbol': symbol,
                                'task_id': task_id,
                                'timestamp': datetime.now().isoformat()
                            })
                        else:
                            raise Exception("数据库保存失败")
                else:
                    logger.warning(f"后台更新未能获取真实数据: {symbol}")
                    self.task_status[task_id]['status'] = 'failed'
                    self.task_status[task_id]['error'] = '所有数据源均无法获取数据'
                    if 'log_id' in locals():
                        await data_update_manager.record_update_complete(log_id, 0, '所有数据源均无法获取数据')
                    
            except Exception as e:
                logger.error(f"美股指数更新失败: {task_id}, error={str(e)}")
                self.task_status[task_id]['status'] = 'failed'
                self.task_status[task_id]['error'] = str(e)
                if 'log_id' in locals():
                    await data_update_manager.record_update_complete(log_id, 0, str(e))
            finally:
                data_update_manager.release_lock(symbol)
                debug_log_manager.end_task(debug_task_id, success=self.task_status[task_id].get('status') == 'completed')

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        return self.task_status.get(task_id)
    
    def get_all_tasks(self) -> Dict[str, Dict]:
        """获取所有任务状态"""
        return self.task_status.copy()
    
    def get_running_tasks_count(self) -> int:
        """获取正在运行的任务数"""
        return sum(1 for s in self.task_status.values() if s.get('status') == 'running')
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id not in self.background_tasks:
            return False
        
        task = self.background_tasks[task_id]
        if task.done():
            return False
        
        task.cancel()
        logger.info(f"已取消任务: {task_id}")
        return True
    
    async def submit_batch_update(self, stock_codes: list, period: str = 'day', 
                                  force: bool = False) -> Dict:
        """批量提交更新任务（带进度推送）
        
        Returns:
            {
                'success': bool,
                'submitted_count': int,
                'skipped_count': int,
                'task_ids': list
            }
        """
        submitted_count = 0
        skipped_count = 0
        task_ids = []
        
        # 进度跟踪
        progress = {
            'total': len(stock_codes),
            'submitted': 0,
            'skipped': 0,
            'lock': asyncio.Lock()
        }
        
        # 获取更新必要性（内部已优化为单会话查询）
        status_result = await data_update_manager.get_all_update_status(stock_codes, 'kline')
        check_results = status_result['stocks']
        
        # 1. 筛选需要更新的股票并按策略排序
        # 策略：1. 优先更新本地没有数据的股票 (last_update is None)
        #       2. 其他股票按最后更新时间升序排列 (最久未更新的优先)
        items_to_update = [
            item for item in check_results 
            if item['needs_update']
        ]
        
        # 执行排序
        items_to_update.sort(key=lambda x: (
            x['last_update'] is not None,  # None (False) comes first
            x['last_update'] if x['last_update'] is not None else datetime.min
        ))
        
        # 重新生成排序后的 check_results 以便后续循环使用
        # 这里的 check_results 将只包含需要更新的项目，
        # 如果需要保留所有项目的顺序，则需要调整后续的循环逻辑。
        # 原逻辑是循环所有 stock_codes，如果需要更新则提交。
        # 为了保持原逻辑的完整性（包括跳过的），我们只在需要更新的项目中重新排序。
        
        # 推送开始进度
        await websocket_manager.broadcast({
            'type': 'background_update_progress',
            'message': f'开始后台更新 {len(stock_codes)} 项数据 (已根据策略排序)',
            'progress': {
                'stage': 'init',
                'total': len(stock_codes)
            },
            'timestamp': datetime.now().isoformat()
        })
        
        # 我们重新组织循环，先处理需要更新的（已排序），再处理跳过的（如果需要的话，但原代码是在循环中跳过的）
        # 既然是后台更新，最重要的顺序是提交顺序。
        
        # 合并排序后的需要更新的项目和不需要更新的项目
        ordered_check_results = items_to_update + [
            item for item in check_results if not item['needs_update']
        ]
        
        for i, check_result in enumerate(ordered_check_results):
            stock_code = check_result['stock_code']
            
            async with progress['lock']:
                progress['submitted' if check_result['needs_update'] else 'skipped'] += 1
            
            if check_result['needs_update']:
                result = await self.submit_kline_update_task(stock_code, period, force)
                if result['success']:
                    submitted_count += 1
                    task_ids.append(result['task_id'])
                else:
                    skipped_count += 1
                
                # 推送进度更新
                await websocket_manager.broadcast({
                    'type': 'background_update_progress',
                    'message': f'已提交 {stock_code} 更新任务',
                    'progress': {
                        'stage': 'updating',
                        'total': len(stock_codes),
                        'current': i + 1,
                        'submitted': submitted_count,
                        'skipped': skipped_count,
                        'current_code': stock_code
                    },
                    'timestamp': datetime.now().isoformat()
                })
            else:
                skipped_count += 1
                logger.debug(f"跳过更新 {stock_code}: {check_result['reason']}")
        
        logger.info(f"批量提交完成: 提交 {submitted_count} 个，跳过 {skipped_count} 个")
        
        # 推送完成进度
        await websocket_manager.broadcast({
            'type': 'background_update_progress',
            'message': f'批量更新任务已提交：{submitted_count} 个更新中',
            'progress': {
                'stage': 'complete',
                'total': len(stock_codes),
                'submitted': submitted_count,
                'skipped': skipped_count
            },
            'timestamp': datetime.now().isoformat()
        })
        
        return {
            'success': True,
            'submitted_count': submitted_count,
            'skipped_count': skipped_count,
            'task_ids': task_ids
        }
    
    async def precompute_pmr_for_holdings(self) -> Dict:
        """
        预计算自持股票的PMR数据 + Force Index + 飞书警告
        
        优化点：
        1. 整合 Alexander Elder Force Index 计算
        2. 使用 ProcessPoolExecutor 多进程加速 CPU 密集型计算
        3. 当持仓股票超越目标价格区间时，推送飞书警告
        
        Returns:
            {
                'success': bool,
                'precomputed_count': int,
                'failed_count': int,
                'force_index_count': int,
                'price_alerts': list,
                'details': list
            }
        """
        try:
            from services.stock_service import StockService
            from services.extended_cache import pmr_cache
            from concurrent.futures import ProcessPoolExecutor
            import asyncio
            
            stock_service = StockService()
            
            # 获取自持股票列表（包含目标价格）
            from routers.holding import holding_manager
            holdings = await holding_manager.load_holdings()
            
            if not holdings or not holdings.sectors:
                logger.info("未找到自持股票")
                return {
                    'success': True, 
                    'precomputed_count': 0, 
                    'failed_count': 0,
                    'force_index_count': 0,
                    'price_alerts': [],
                    'details': []
                }
            
            # 提取所有股票代码和目标价格
            stock_info_list = []
            for sector in holdings.sectors:
                for stock in sector.stocks:
                    stock_info_list.append({
                        'code': stock.code,
                        'name': stock.name,
                        'target_price_low': getattr(stock, 'target_price_low', None),
                        'target_price_high': getattr(stock, 'target_price_high', None),
                        'current_price': getattr(stock, 'current_price', None)
                    })
            
            logger.info(f"[START] 开始预计算 {len(stock_info_list)} 只股票的 PMR + Force Index 数据")
            
            # 推送开始通知
            await websocket_manager.broadcast({
                'type': 'pmr_precompute_start',
                'message': f'开始预计算 {len(stock_info_list)} 只股票的指标数据',
                'total': len(stock_info_list),
                'timestamp': datetime.now().isoformat()
            })
            
            precomputed_count = 0
            failed_count = 0
            force_index_count = 0
            price_alerts = []
            details = []
            
            # 准备批量计算参数
            batch_args = []
            
            for i, stock_info in enumerate(stock_info_list):
                stock_code = stock_info['code']
                
                # 检查缓存是否已存在
                cached_pmr = await pmr_cache.get(stock_code, 120)
                if cached_pmr:
                    logger.info(f"[OK] {stock_code} PMR已缓存")
                    details.append({'code': stock_code, 'status': 'cached'})
                    continue
                
                # 获取K线数据（异步获取）
                try:
                    klines = await stock_service.get_kline(stock_code, 'day', 240)  # 需要足够数据计算 MA120
                    
                    if not klines or len(klines) < 120:
                        logger.warning(f"[WARN] {stock_code} K线数据不足")
                        details.append({'code': stock_code, 'status': 'insufficient_data'})
                        continue
                    
                    # 转换为可序列化格式
                    klines_data = [
                        {
                            'close': float(k.close),
                            'high': float(k.high),
                            'low': float(k.low),
                            'volume': int(k.volume) if k.volume else 0,
                            'trade_date': str(k.trade_date) if hasattr(k, 'trade_date') else None
                        }
                        for k in klines
                    ]
                    
                    batch_args.append((stock_code, klines_data, 120, stock_info))
                    
                except Exception as e:
                    logger.error(f"[ERROR] {stock_code} 获取K线失败: {str(e)}")
                    details.append({'code': stock_code, 'status': 'failed', 'reason': str(e)})
            
            # 使用 ProcessPoolExecutor 多进程计算（避免阻塞主事件循环）
            if batch_args:
                logger.info(f"[MULTIPROCESS] 启动多进程计算 {len(batch_args)} 只股票的指标")
                
                # 导入多进程计算函数
                from services.indicator_calculator_mp import batch_calculate_indicators_mp
                
                # 创建进程池（最多使用 CPU 核心数 - 1 个进程）
                import os
                max_workers = max(1, os.cpu_count() - 1)
                
                with ProcessPoolExecutor(max_workers=max_workers) as executor:
                    # 在线程池中运行进程池
                    loop = asyncio.get_event_loop()
                    results = await loop.run_in_executor(
                        None,  # 使用默认线程池
                        lambda: list(executor.map(batch_calculate_indicators_mp, batch_args))
                    )
                
                # 处理计算结果
                for i, result in enumerate(results):
                    stock_code = batch_args[i][0]
                    stock_info = batch_args[i][3]
                    
                    try:
                        if result.get('error'):
                            failed_count += 1
                            details.append({'code': stock_code, 'status': 'failed', 'reason': result['error']})
                            logger.error(f"[ERROR] {stock_code} 计算失败: {result['error']}")
                            continue
                        
                        # 存储PMR到缓存
                        if result.get('pmr'):
                            await pmr_cache.set(result['pmr'], stock_code, 120)
                            precomputed_count += 1
                        
                        # 存储 Force Index 到缓存
                        if result.get('force_index'):
                            force_index_count += 1
                            # Force Index 缓存逻辑由 force_index_calculator 处理
                        
                        details.append({
                            'code': stock_code,
                            'status': 'success',
                            'pmr_cached': result.get('pmr') is not None,
                            'force_index_calculated': result.get('force_index') is not None
                        })
                        
                        # 检查价格警告
                        alert = await self._check_price_alert(stock_info, result)
                        if alert:
                            price_alerts.append(alert)
                        
                        logger.info(f"[OK] {stock_code} 指标计算完成 ({i+1}/{len(batch_args)})")
                        
                    except Exception as e:
                        failed_count += 1
                        details.append({'code': stock_code, 'status': 'failed', 'reason': str(e)})
                        logger.error(f"[ERROR] {stock_code} 结果处理失败: {str(e)}")
            
            # 推送飞书警告
            if price_alerts:
                await self._send_feishu_price_alerts(price_alerts)
            
            # 推送完成通知
            await websocket_manager.broadcast({
                'type': 'pmr_precompute_complete',
                'message': f'指标预计算完成: PMR {precomputed_count}, Force Index {force_index_count}, 价格警告 {len(price_alerts)}',
                'precomputed': precomputed_count,
                'force_index': force_index_count,
                'price_alerts': len(price_alerts),
                'failed': failed_count,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"[OK] 指标预计算完成: PMR {precomputed_count}, Force Index {force_index_count}, 价格警告 {len(price_alerts)}")
            
            return {
                'success': True,
                'precomputed_count': precomputed_count,
                'force_index_count': force_index_count,
                'price_alerts_count': len(price_alerts),
                'failed_count': failed_count,
                'price_alerts': price_alerts,
                'details': details
            }
            
        except Exception as e:
            logger.error(f"指标预计算失败: {str(e)}", exc_info=True)
            return {
                'success': False,
                'precomputed_count': 0,
                'force_index_count': 0,
                'price_alerts_count': 0,
                'failed_count': 0,
                'error': str(e)
            }
    
    async def _check_price_alert(self, stock_info: Dict, indicator_result: Dict) -> Optional[Dict]:
        """
        检查价格是否超出目标区间
        
        Args:
            stock_info: 股票信息（包含目标价格区间）
            indicator_result: 指标计算结果
            
        Returns:
            价格警告信息，如果未触发则返回 None
        """
        try:
            current_price = stock_info.get('current_price')
            target_low = stock_info.get('target_price_low')
            target_high = stock_info.get('target_price_high')
            
            if not current_price:
                # 从指标结果中提取当前价格
                if indicator_result.get('pmr') and indicator_result['pmr'].get('closes'):
                    current_price = indicator_result['pmr']['closes'][-1]
                else:
                    return None
            
            # 检查是否超出目标价格区间
            alert_type = None
            alert_message = None
            
            if target_low and current_price < target_low:
                alert_type = 'below_target'
                alert_message = f"{stock_info['name']} ({stock_info['code']}) 当前价格 ¥{current_price:.2f} 低于目标价格下限 ¥{target_low:.2f}"
            elif target_high and current_price > target_high:
                alert_type = 'above_target'
                alert_message = f"{stock_info['name']} ({stock_info['code']}) 当前价格 ¥{current_price:.2f} 高于目标价格上限 ¥{target_high:.2f}"
            
            if alert_type:
                # 结合 Force Index 分析
                force_index = indicator_result.get('force_index')
                force_index_signal = None
                
                if force_index:
                    signal = force_index.get('signals', {}).get('current_signal', '未知')
                    strength = force_index.get('signals', {}).get('signal_strength', '弱')
                    trend = force_index.get('trend_analysis', {}).get('trend_direction', '未知')
                    
                    force_index_signal = f"Force Index: {signal} ({strength}), 趋势: {trend}"
                
                return {
                    'stock_code': stock_info['code'],
                    'stock_name': stock_info['name'],
                    'alert_type': alert_type,
                    'current_price': current_price,
                    'target_price_low': target_low,
                    'target_price_high': target_high,
                    'message': alert_message,
                    'force_index_signal': force_index_signal,
                    'timestamp': datetime.now().isoformat()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"价格警告检查失败: {str(e)}")
            return None
    
    async def _send_feishu_price_alerts(self, price_alerts: List[Dict]) -> None:
        """
        通过飞书推送价格警告
        
        Args:
            price_alerts: 价格警告列表
        """
        try:
            from services.feishu_bot import feishu_long_connection_service
            
            if not feishu_long_connection_service._running:
                logger.warning("飞书长连接服务未运行，跳过价格警告推送")
                return
            
            for alert in price_alerts:
                try:
                    # 构建飞书消息
                    message = {
                        'msg_type': 'text',
                        'content': {
                            'text': f"⚠️ 价格警告\n\n"
                    f"{alert['message']}\n\n"
                    f"{'Force Index 分析: ' + alert['force_index_signal'] if alert.get('force_index_signal') else ''}\n\n"
                    f"时间: {alert['timestamp']}"
                        }
                    }
                    
                    # 发送飞书消息
                    # 注意：这里需要根据飞书服务的实际接口调整
                    # 假设有一个发送消息的方法
                    if hasattr(feishu_long_connection_service, 'send_message'):
                        await feishu_long_connection_service.send_message(message)
                    else:
                        logger.warning("飞书服务不支持消息发送接口")
                    
                    logger.info(f"[FEISHU] 已推送价格警告: {alert['stock_name']}")
                    
                except Exception as e:
                    logger.error(f"推送飞书警告失败 {alert['stock_code']}: {str(e)}")
            
        except Exception as e:
            logger.error(f"飞书价格警告推送失败: {str(e)}")


# 单例实例
background_updater = BackgroundUpdater()
