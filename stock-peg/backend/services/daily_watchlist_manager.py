"""Daily watchlist management service"""
import logging
from typing import List, Optional, Dict
from datetime import date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from database import DailyWatchlist
from models.daily_watchlist import (
    WatchlistStockCreate,
    WatchlistStockUpdate,
    WatchlistStockResponse,
    WatchlistDateGroup,
    WatchlistSummary
)
from config.settings import settings
from services.quote_data_service import quote_data_service
from services.background_updater import background_updater
from database.operations import (
    upsert_watchlist_stock,
    get_stock_by_id,
    update_watchlist_stock,
    remove_from_watchlist,
    get_watchlist_by_date as get_watchlist_by_date_op,
    get_all_dates,
    archive_watchlist_stocks,
    unarchive_watchlist_stocks,
)

logger = logging.getLogger(__name__)


class DailyWatchlistManager:
    """Daily watchlist management service (singleton pattern)"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Avoid re-initialization
        if DailyWatchlistManager._initialized:
            return
        
        self.stock_name_mapping: Dict[str, str] = {}
        self._load_stock_name_mapping()
        logger.info("[START] DailyWatchlistManager initialized")
        DailyWatchlistManager._initialized = True
    
    def _load_stock_name_mapping(self):
        """Load stock name to code mapping"""
        import json
        mapping_file = settings.data_dir / "stock_name_mapping.json"
        if mapping_file.exists():
            try:
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Support both formats:
                    # 1. Direct mapping: {"平安银行": "000001", ...}
                    # 2. Nested mapping: {"mapping": {"平安银行": "000001", ...}}
                    if isinstance(data, dict):
                        if 'mapping' in data:
                            self.stock_name_mapping = data.get('mapping', {})
                        else:
                            self.stock_name_mapping = data
                    logger.info(f"Loaded {len(self.stock_name_mapping)} stock name mappings")
            except Exception as e:
                logger.warning(f"Failed to load stock name mapping: {str(e)}")
    
    def _get_stock_code(self, stock_name: str) -> Optional[str]:
        """Get stock code by name"""
        return self.stock_name_mapping.get(stock_name)

    async def _trigger_quote_update(self, stock_code: str):
        if not stock_code or stock_code.startswith("UNKNOWN"):
            return
        await background_updater.submit_quote_update_task(stock_code)
    
    async def _check_and_resolve_unknown_stocks(self, db: AsyncSession, stocks: List[DailyWatchlist]):
        """检查并异步解析UNKNOWN股票代码
        
        发现UNKNOWN代码后，立即异步启动解析和更新
        使用Fire-and-Forget模式确保任务不被取消
        """
        unknown_stocks = [
            stock for stock in stocks 
            if stock.stock_code and stock.stock_code.startswith('UNKNOWN')
        ]
        
        if not unknown_stocks:
            return
        
        logger.info(f"[UNKNOWN-CHECK] 发现 {len(unknown_stocks)} 个UNKNOWN股票，启动异步解析")
        
        # 使用后台线程启动解析任务（不受请求生命周期影响）
        import threading
        import asyncio
        
        def run_async_task():
            """在新线程中运行异步任务"""
            try:
                # 创建新的事件循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    from services.background_updater import background_updater
                    
                    async def resolve_all():
                        for stock in unknown_stocks:
                            try:
                                logger.info(f"[UNKNOWN-CHECK] 开始解析: {stock.stock_name} ({stock.stock_code})")
                                
                                # 提交K线更新任务（会自动触发UNKNOWN解析）
                                result = await background_updater.submit_kline_update_task(
                                    stock.stock_code, 
                                    period='day', 
                                    force=False
                                )
                                
                                logger.info(f"[UNKNOWN-CHECK] 解析结果: {stock.stock_name} - {result}")
                            except Exception as e:
                                logger.error(f"[UNKNOWN-CHECK] 解析失败 {stock.stock_name}: {str(e)}")
                    
                    # 运行异步任务
                    loop.run_until_complete(resolve_all())
                finally:
                    loop.close()
            except Exception as e:
                logger.error(f"[UNKNOWN-CHECK] 后台线程失败: {str(e)}")
        
        # 启动后台线程（Fire-and-Forget）
        thread = threading.Thread(target=run_async_task, daemon=True)
        thread.start()
        
        logger.info(f"[UNKNOWN-CHECK] 已启动后台解析线程")

    async def _build_stock_response(
        self,
        db: AsyncSession,
        stock: DailyWatchlist
    ) -> WatchlistStockResponse:
        response = WatchlistStockResponse.from_orm(stock)

        if not stock.stock_code or stock.stock_code.startswith("UNKNOWN"):
            return response

        try:
            quote = await quote_data_service.get_quote_from_db(db, stock.stock_code)
            if quote:
                response.price = quote.price
                response.change = quote.change
                response.change_pct = quote.change_pct
                response.quote_timestamp = quote.timestamp

                update_check = await quote_data_service.check_update_necessity(
                    db,
                    stock.stock_code,
                    max_age_seconds=60
                )
                if update_check.get("needs_update"):
                    await self._trigger_quote_update(stock.stock_code)
                    response.quote_is_updating = True
            else:
                await self._trigger_quote_update(stock.stock_code)
                response.quote_is_updating = True
        except Exception as e:
            logger.warning(f"Failed to load quote for watchlist stock {stock.stock_code}: {str(e)}")

        return response
    
    async def add_stock(
        self,
        db: AsyncSession,
        stock_data: WatchlistStockCreate
    ) -> WatchlistStockResponse:
        """Add a stock to watchlist

        Args:
            db: Database session
            stock_data: Stock data to add

        Returns:
            Created watchlist stock
        """
        # Auto-detect stock code if not provided
        stock_code = stock_data.stock_code
        if not stock_code:
            stock_code = self._get_stock_code(stock_data.stock_name)
            if not stock_code:
                logger.warning(f"Stock code not found for '{stock_data.stock_name}', using 'UNKNOWN'")
                stock_code = "UNKNOWN"

        # Convert float to Decimal for operations
        target_price = Decimal(str(stock_data.target_price)) if stock_data.target_price else None
        stop_loss_price = Decimal(str(stock_data.stop_loss_price)) if stock_data.stop_loss_price else None

        # Use upsert operation
        watchlist_stock = await upsert_watchlist_stock(
            db=db,
            watch_date=stock_data.watch_date,
            stock_code=stock_code,
            stock_name=stock_data.stock_name,
            target_price=target_price,
            stop_loss_price=stop_loss_price,
            reason=stock_data.reason,
            notes=stock_data.notes
        )

        await self._trigger_quote_update(stock_code)
        logger.info(f"Added/Updated watchlist stock: {stock_code} ({stock_data.stock_name}) on {stock_data.watch_date}")
        return await self._build_stock_response(db, watchlist_stock)
    
    async def get_stock(
        self,
        db: AsyncSession,
        stock_id: int
    ) -> Optional[WatchlistStockResponse]:
        """Get a single watchlist stock by ID

        Args:
            db: Database session
            stock_id: Stock ID

        Returns:
            Watchlist stock or None
        """
        stock = await get_stock_by_id(db, stock_id)

        if stock:
            return await self._build_stock_response(db, stock)
        return None
    
    async def update_stock(
        self,
        db: AsyncSession,
        stock_id: int,
        stock_data: WatchlistStockUpdate
    ) -> Optional[WatchlistStockResponse]:
        """Update a watchlist stock

        Args:
            db: Database session
            stock_id: Stock ID
            stock_data: Update data

        Returns:
            Updated watchlist stock or None
        """
        # Convert float to Decimal for operations
        target_price = Decimal(str(stock_data.target_price)) if stock_data.target_price else None
        change_up_pct = Decimal(str(stock_data.change_up_pct)) if stock_data.change_up_pct else None
        change_down_pct = Decimal(str(stock_data.change_down_pct)) if stock_data.change_down_pct else None
        stop_loss_price = Decimal(str(stock_data.stop_loss_price)) if stock_data.stop_loss_price else None

        stock = await update_watchlist_stock(
            db=db,
            stock_id=stock_id,
            stock_code=stock_data.stock_code,
            reason=stock_data.reason,
            target_price=target_price,
            change_up_pct=change_up_pct,
            change_down_pct=change_down_pct,
            stop_loss_price=stop_loss_price,
            notes=stock_data.notes
        )

        if not stock:
            return None

        await self._trigger_quote_update(stock.stock_code)
        logger.info(f"Updated watchlist stock ID {stock_id}")
        return await self._build_stock_response(db, stock)
    
    async def delete_stocks(
        self,
        db: AsyncSession,
        stock_ids: Optional[List[int]] = None,
        watch_date: Optional[date] = None
    ) -> int:
        """Delete watchlist stocks

        Args:
            db: Database session
            stock_ids: List of stock IDs to delete (optional)
            watch_date: Delete all stocks on this date (used if stock_ids is None)

        Returns:
            Number of deleted records
        """
        if stock_ids:
            deleted_count = await remove_from_watchlist(db, stock_ids=stock_ids)
        elif watch_date:
            deleted_count = await remove_from_watchlist(db, watch_date=watch_date)
        else:
            deleted_count = 0

        logger.info(f"Deleted {deleted_count} watchlist stocks")
        return deleted_count
    
    async def archive_stocks(
        self,
        db: AsyncSession,
        stock_ids: Optional[List[int]] = None,
        watch_date: Optional[date] = None
    ) -> int:
        """Archive watchlist stocks

        Args:
            db: Database session
            stock_ids: List of stock IDs to archive (optional)
            watch_date: Archive all stocks on this date (used if stock_ids is None)

        Returns:
            Number of archived records
        """
        archived_count = await archive_watchlist_stocks(db, stock_ids, watch_date)
        logger.info(f"Archived {archived_count} watchlist stocks")
        return archived_count
    
    async def unarchive_stocks(
        self,
        db: AsyncSession,
        stock_ids: List[int]
    ) -> int:
        """Unarchive watchlist stocks

        Args:
            db: Database session
            stock_ids: List of stock IDs to unarchive

        Returns:
            Number of unarchived records
        """
        unarchived_count = await unarchive_watchlist_stocks(db, stock_ids)
        logger.info(f"Unarchived {unarchived_count} watchlist stocks")
        return unarchived_count
    
    async def get_watchlist_by_date(
        self,
        db: AsyncSession,
        watch_date: date,
        include_archived: bool = False
    ) -> List[WatchlistStockResponse]:
        """Get watchlist stocks by date

        Args:
            db: Database session
            watch_date: Watch date
            include_archived: Include archived stocks

        Returns:
            List of watchlist stocks
        """
        stocks = await get_watchlist_by_date_op(db, watch_date, include_archived)
        
        # 主动检测并解析UNKNOWN股票代码
        await self._check_and_resolve_unknown_stocks(db, stocks)

        result = []
        for stock in stocks:
            result.append(await self._build_stock_response(db, stock))
        return result
    
    # Note: Synchronous methods removed - use async versions with database.operations
    
    async def get_all_dates(
        self,
        db: AsyncSession,
        include_archived: bool = False
    ) -> List[date]:
        """Get all watchlist dates

        Args:
            db: Database session
            include_archived: Include archived stocks

        Returns:
            List of dates (sorted descending)
        """
        dates = await get_all_dates(db, include_archived)
        return dates
    
    async def get_summary(
        self,
        db: AsyncSession,
        include_archived: bool = False,
        limit: int = 30
    ) -> WatchlistSummary:
        """Get watchlist summary (grouped by date) - 立即返回本地数据
        
        原则：立即返回数据库中的本地数据，不等待外部数据源更新
        
        Args:
            db: Database session
            include_archived: Include archived stocks
            limit: Maximum number of dates to return
            
        Returns:
            Watchlist summary with full stock details
        """
        # Get all dates
        dates = await self.get_all_dates(db, include_archived)
        
        # Limit dates
        dates = dates[:limit]
        
        # 批量查询所有日期的股票数据（立即返回本地数据）
        date_groups = []
        total_stocks = 0
        
        from sqlalchemy import select
        from database import DailyWatchlist
        
        if dates:
            # 构建批量查询：一次性获取所有日期的股票详情
            query = select(DailyWatchlist).where(
                DailyWatchlist.watch_date.in_(dates)
            ).order_by(DailyWatchlist.watch_date.desc(), DailyWatchlist.id)
            
            if not include_archived:
                query = query.where(DailyWatchlist.is_archived == False)
            
            result = await db.execute(query)
            all_stocks = result.scalars().all()
            
            # 按日期分组
            stocks_by_date = {}
            for stock in all_stocks:
                if stock.watch_date not in stocks_by_date:
                    stocks_by_date[stock.watch_date] = []
                stocks_by_date[stock.watch_date].append(WatchlistStockResponse(
                    id=stock.id,
                    stock_code=stock.stock_code,
                    stock_name=stock.stock_name,
                    watch_date=stock.watch_date,
                    reason=stock.reason,
                    target_price=float(stock.target_price) if stock.target_price else None,
                    stop_loss_price=float(stock.stop_loss_price) if stock.stop_loss_price else None,
                    change_up_pct=float(stock.change_up_pct) if stock.change_up_pct else None,
                    change_down_pct=float(stock.change_down_pct) if stock.change_down_pct else None,
                    notes=stock.notes,
                    is_archived=stock.is_archived,
                    created_at=stock.created_at,
                    updated_at=stock.updated_at,
                    price=None,  # 稍后填充
                    change_pct=None,
                    quote_is_updating=False
                ))
            
            # 构建响应
            for watch_date in dates:
                stocks = stocks_by_date.get(watch_date, [])
                if stocks:
                    date_groups.append(WatchlistDateGroup(
                        watch_date=watch_date,
                        stocks=stocks,
                        total_count=len(stocks)
                    ))
                    total_stocks += len(stocks)
            
            # 异步触发行情更新（后台任务，不阻塞响应）
            import asyncio
            for stock in all_stocks:
                if stock.stock_code and not stock.stock_code.startswith('UNKNOWN'):
                    asyncio.create_task(self._trigger_quote_update(stock.stock_code))
        
        return WatchlistSummary(
            dates=date_groups,
            total_dates=len(date_groups),
            total_stocks=total_stocks
        )


# Singleton instance
daily_watchlist_manager = DailyWatchlistManager()
