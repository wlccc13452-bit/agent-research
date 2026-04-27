"""股票数据持久化服务 - 数据库智能更新"""
import asyncio
import logging
from typing import List, Optional, Dict
from datetime import datetime, date, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import StockKLineData
from database.operations.stock_kline_ops import (
    get_latest_date as ops_get_latest_date,
    get_kline_data as ops_get_kline_data,
    save_kline_data as ops_save_kline_data,
    clean_duplicates as ops_clean_duplicates,
)
from services.stock_service import StockService
from services.debug_log_manager import debug_log_manager
from services.database_logger import db_logger, log_db_operation
from services.kline_cache import kline_cache  # 导入内存缓存
from models import StockKLine, SectorInfo, StockInfo

logger = logging.getLogger(__name__)


class StockDataService:
    """股票数据持久化服务"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StockDataService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self.stock_service = StockService()
        self._initialized = True

    async def get_sectors_from_cache(self) -> List[SectorInfo]:
        from routers.holding import holding_manager

        if holding_manager.holdings and holding_manager.holdings.sectors:
            return holding_manager.holdings.sectors

        try:
            holdings = await asyncio.wait_for(holding_manager.load_holdings(), timeout=2.0)
            if holdings and holdings.sectors:
                return holdings.sectors
        except Exception:
            pass

        try:
            from database.session import async_session_maker
            async with async_session_maker() as db:
                stmt = (
                    select(StockKLineData.stock_code)
                    .distinct()
                    .where(StockKLineData.period == 'day')
                    .limit(30)
                )
                result = await db.execute(stmt)
                codes = [row[0] for row in result.fetchall() if row[0]]

            if not codes:
                return []

            fallback_sector = SectorInfo(
                name="自持股票",
                stocks=[
                    StockInfo(code=code, name=code, sector="自持股票")
                    for code in codes
                ]
            )
            return [fallback_sector]
        except Exception as e:
            logger.warning(f"获取数据库兜底板块失败: {str(e)}")
            return []
    
    async def get_allowed_codes(self) -> Dict[str, List[str]]:
        """
        获取所有允许更新的股票和指数代码
        
        Returns:
            {
                'stocks': [stock_codes],
                'indices': [index_codes],
                'all': [all_codes]
            }
        """
        from routers.holding import holding_manager
        from routers.stock import CN_INDICES, SECTOR_INDEX_MAP
        from config.settings import settings
        import json
        from pathlib import Path
        
        stocks = []
        indices = []
        
        # 1. 获取自持股票
        try:
            holdings = await holding_manager.load_holdings()
            if holdings and holdings.sectors:
                for sector in holdings.sectors:
                    for stock in sector.stocks:
                        if stock.code and stock.code != 'UNKNOWN':
                            stocks.append(stock.code)
        except Exception as e:
            logger.warning(f"获取自持股票失败: {str(e)}")
        
        # 2. 获取内置指数
        indices.extend(CN_INDICES.keys())
        
        # 3. 获取行业板块指数
        indices.extend(SECTOR_INDEX_MAP.values())
        
        # 4. 获取配置文件中的指数
        indices_config_path = settings.data_dir / "indices_config.json"
        if indices_config_path.exists():
            try:
                import asyncio
                def read_config():
                    with open(indices_config_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                
                config = await asyncio.to_thread(read_config)
                for idx in config.get('indices', []):
                        code = idx.get('full_code') or idx.get('code')
                        if code and code not in indices:
                            indices.append(code)
            except Exception as e:
                logger.warning(f"读取指数配置失败: {str(e)}")
        
        return {
            'stocks': list(set(stocks)),
            'indices': list(set(indices)),
            'all': list(set(stocks + indices))
        }
    
    async def is_code_allowed(self, code: str) -> bool:
        """
        检查代码是否在允许更新的列表中
        
        Args:
            code: 股票或指数代码
            
        Returns:
            是否允许更新
        """
        allowed = await self.get_allowed_codes()
        return code in allowed['all']
    
    @log_db_operation('query', '获取最新日期')
    async def get_latest_date_from_db(
        self, 
        db: AsyncSession, 
        stock_code: str, 
        period: str = 'day'
    ) -> Optional[date]:
        """
        从数据库获取指定股票的最新日期
        
        Args:
            db: 数据库会话
            stock_code: 股票代码
            period: K线周期
            
        Returns:
            最新交易日期，如果没有数据返回None
        """
        return await ops_get_latest_date(db, stock_code, period)
    
    @log_db_operation('query', '获取K线数据')
    async def get_kline_from_db(
        self,
        db: AsyncSession,
        stock_code: str,
        period: str = 'day',
        count: int = 100
    ) -> List[StockKLine]:
        """
        从数据库获取K线数据（带内存缓存优化）
        
        Args:
            db: 数据库会话
            stock_code: 股票代码
            period: K线周期
            count: 获取数量
            
        Returns:
            K线数据列表
        """
        try:
            # [START] 性能优化：优先从内存缓存获取
            cached_data = await kline_cache.get(stock_code, period, count)
            if cached_data:
                logger.info(f"⚡ 从内存缓存获取 {stock_code} K线数据 {len(cached_data)} 条")
                return [StockKLine(**item) for item in cached_data]
            
            # 缓存未命中，从数据库查询
            logger.info(f"💾 从数据库查询 {stock_code} K线数据")
            
            # Use ops function
            records = await ops_get_kline_data(db, stock_code, period, count)
            
            # 转换为StockKLine格式
            klines = []
            cache_data = []  # 用于缓存的数据
            
            for record in records:
                kline = StockKLine(
                    code=record.stock_code,
                    date=record.trade_date.strftime('%Y-%m-%d'),
                    open=float(record.open),
                    close=float(record.close),
                    high=float(record.high),
                    low=float(record.low),
                    volume=int(record.volume) if record.volume else 0,
                    amount=float(record.amount) if record.amount else 0.0
                )
                klines.append(kline)
                
                # 准备缓存数据
                cache_data.append({
                    'code': record.stock_code,
                    'date': record.trade_date.strftime('%Y-%m-%d'),
                    'open': float(record.open),
                    'close': float(record.close),
                    'high': float(record.high),
                    'low': float(record.low),
                    'volume': int(record.volume) if record.volume else 0,
                    'amount': float(record.amount) if record.amount else 0.0
                })
            
            # [START] 将查询结果存入内存缓存
            if cache_data:
                await kline_cache.set(stock_code, cache_data, period, count)
                logger.info(f"[OK] 已缓存 {stock_code} K线数据 {len(klines)} 条")
            
            return klines
            
        except Exception as e:
            logger.error(f"从数据库获取K线数据失败: {str(e)}")
            return []
    
    @log_db_operation('insert', '保存K线数据')
    async def clean_stock_duplicates(
        self,
        db: AsyncSession,
        stock_code: str,
        period: str = 'day'
    ) -> int:
        """
        清理指定股票和周期的重复K线数据 (保留 ID 最小的一条)
        使用更高效的 SQL 批量删除
        """
        return await ops_clean_duplicates(db, stock_code, period)

    async def save_kline_to_db(
        self,
        db: AsyncSession,
        stock_code: str,
        klines: List[StockKLine],
        period: str = 'day'
    ) -> int:
        """
        保存K线数据到数据库 (批量更新优化)
        
        Args:
            db: 数据库会话
            stock_code: 股票代码
            klines: K线数据列表
            period: K线周期
            
        Returns:
            成功保存的记录数
        """
        if not klines:
            return 0
        
        # Convert StockKLine to dict format expected by ops function
        klines_dict = []
        for kline in klines:
            klines_dict.append({
                'date': kline.date,
                'open': kline.open,
                'close': kline.close,
                'high': kline.high,
                'low': kline.low,
                'volume': kline.volume,
                'amount': kline.amount,
            })
        
        saved_count = await ops_save_kline_data(db, stock_code, klines_dict, period)
        
        if saved_count > 0:
            logger.info(f"保存 {stock_code} K线数据到数据库: {saved_count} 条记录 (批量更新)")
        
        return saved_count
    
    async def update_stock_kline(
        self,
        db: AsyncSession,
        stock_code: str,
        period: str = 'day',
        force_full: bool = False
    ) -> Dict:
        """
        智能更新股票K线数据
        
        Args:
            db: 数据库会话
            stock_code: 股票代码
            period: K线周期
            force_full: 是否强制全量更新
            
        Returns:
            {
                'success': bool,
                'message': str,
                'saved_count': int,
                'latest_date': str
            }
        """
        try:
            # 1. 检查数据库中是否存在该股票数据
            latest_date = await self.get_latest_date_from_db(db, stock_code, period)
            
            # 2. 决定获取策略
            if force_full or latest_date is None:
                # 全量获取
                logger.info(f"全量获取 {stock_code} K线数据 (period={period})")
                klines = await self.stock_service.get_kline(stock_code, period, 500)
                strategy = "full"
            else:
                # 增量获取 - 只获取最新数据
                # 计算需要获取的天数
                days_to_fetch = (date.today() - latest_date).days + 10  # 多获取几天以确保完整
                if days_to_fetch <= 0:
                    return {
                        'success': True,
                        'message': '数据已是最新，无需更新',
                        'saved_count': 0,
                        'latest_date': latest_date.strftime('%Y-%m-%d')
                    }
                
                logger.info(f"增量获取 {stock_code} K线数据 (从 {latest_date} 至今, {days_to_fetch} 天)")
                klines = await self.stock_service.get_kline(stock_code, period, min(days_to_fetch, 100))
                strategy = "incremental"
            
            # 3. 保存到数据库
            if not klines:
                return {
                    'success': False,
                    'message': '未能获取到K线数据',
                    'saved_count': 0,
                    'latest_date': latest_date.strftime('%Y-%m-%d') if latest_date else None
                }
            
            # 清理重复数据（主动清理）
            await self.clean_stock_duplicates(db, stock_code, period)
            
            saved_count = await self.save_kline_to_db(db, stock_code, klines, period)
            
            # 4. 获取最新日期
            new_latest_date = await self.get_latest_date_from_db(db, stock_code, period)
            
            return {
                'success': True,
                'message': f'更新成功 (策略: {strategy})',
                'saved_count': saved_count,
                'latest_date': new_latest_date.strftime('%Y-%m-%d') if new_latest_date else None,
                'total_count': len(klines)
            }
            
        except Exception as e:
            logger.error(f"更新股票 {stock_code} K线数据失败: {str(e)}")
            return {
                'success': False,
                'message': f'更新失败: {str(e)}',
                'saved_count': 0,
                'latest_date': None
            }
    
    async def get_or_update_kline(
        self,
        db: AsyncSession,
        stock_code: str,
        period: str = 'day',
        count: int = 100,
        task_id: Optional[str] = None
    ) -> List[StockKLine]:
        """
        获取K线数据，优先从数据库读取，如果数据不足则更新
        
        Args:
            db: 数据库会话
            stock_code: 股票代码
            period: K线周期
            count: 需要的数量
            task_id: 任务ID（可选，用于日志跟踪）
            
        Returns:
            K线数据列表
        """
        # 如果没有提供task_id，创建一个内部任务
        own_task = False
        if not task_id:
            task_id = debug_log_manager.start_task(
                'data_service',
                f'get_or_update_kline {stock_code}',
                {'stock_code': stock_code, 'period': period, 'count': count}
            )
            own_task = True
        
        try:
            # 1. 先从数据库读取
            debug_log_manager.log_debug(task_id, '从数据库读取K线数据', {
                'stock_code': stock_code,
                'period': period,
                'count': count
            })
            klines = await self.get_kline_from_db(db, stock_code, period, count)
            
            # 2. 检查数据是否足够
            if len(klines) >= count:
                debug_log_manager.log_debug(task_id, '数据库数据充足', {
                    'klines_count': len(klines)
                })
                if own_task:
                    debug_log_manager.end_task(task_id, success=True)
                return klines
            
            # 3. 数据不足，尝试更新
            debug_log_manager.log_info(task_id, '数据库数据不足，尝试更新', {
                'current_count': len(klines),
                'required_count': count
            })
            await self.update_stock_kline(db, stock_code, period)
            
            # 4. 再次从数据库读取
            klines = await self.get_kline_from_db(db, stock_code, period, count)
            
            # 5. 如果还是不足，直接从API获取
            if len(klines) < count:
                debug_log_manager.log_warning(task_id, '数据库更新后仍不足，从API获取', {
                    'current_count': len(klines)
                })
                klines = await self.stock_service.get_kline(stock_code, period, count)
            
            if own_task:
                debug_log_manager.end_task(task_id, success=True)
            return klines
            
        except Exception as e:
            debug_log_manager.log_error(task_id, '获取/更新K线数据失败', {
                'error': str(e)
            })
            if own_task:
                debug_log_manager.end_task(task_id, success=False, error=str(e))
            # 失败时直接从API获取
            return await self.stock_service.get_kline(stock_code, period, count)


# 单例实例
stock_data_service = StockDataService()
