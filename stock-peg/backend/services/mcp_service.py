"""MCP Service for AI Agent operations"""
import logging
from typing import List, Optional
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from services.holding_manager import HoldingManager
from services.daily_watchlist_manager import daily_watchlist_manager
from config.settings import settings

logger = logging.getLogger(__name__)

# 创建持仓管理器
holding_manager = HoldingManager(settings.holdings_file_path)


class MCPService:
    """MCP service for AI Agent operations"""
    
    # ============ Holdings Operations ============
    
    async def holdings_add_stock(
        self,
        sector: str,
        stock_name: str,
        stock_code: Optional[str] = None
    ) -> dict:
        """
        Add stock to holdings
        
        Args:
            sector: Sector name
            stock_name: Stock name
            stock_code: Stock code (optional, auto-detected if not provided)
        
        Returns:
            Success message
        """
        try:
            success = await holding_manager.add_stock(sector, stock_name, stock_code)
            if success:
                return {
                    "success": True,
                    "message": f"成功添加股票 {stock_name} 到板块 {sector}"
                }
            else:
                return {
                    "success": False,
                    "message": f"添加股票失败"
                }
        except Exception as e:
            logger.error(f"Failed to add stock: {str(e)}")
            return {
                "success": False,
                "message": f"添加股票失败: {str(e)}"
            }
    
    async def holdings_remove_stock(self, sector: str, stock_name: str) -> dict:
        """
        Remove stock from holdings
        
        Args:
            sector: Sector name
            stock_name: Stock name
        
        Returns:
            Success message
        """
        try:
            success = await holding_manager.remove_stock(sector, stock_name)
            if success:
                return {
                    "success": True,
                    "message": f"成功从板块 {sector} 删除股票 {stock_name}"
                }
            else:
                return {
                    "success": False,
                    "message": "删除股票失败"
                }
        except Exception as e:
            logger.error(f"Failed to remove stock: {str(e)}")
            return {
                "success": False,
                "message": f"删除股票失败: {str(e)}"
            }
    
    async def holdings_add_sector(self, sector_name: str) -> dict:
        """
        Add new sector to holdings
        
        Args:
            sector_name: Sector name
        
        Returns:
            Success message
        """
        try:
            success = await holding_manager.add_sector(sector_name)
            if success:
                return {
                    "success": True,
                    "message": f"成功添加板块 {sector_name}"
                }
            else:
                return {
                    "success": False,
                    "message": "添加板块失败（可能已存在）"
                }
        except Exception as e:
            logger.error(f"Failed to add sector: {str(e)}")
            return {
                "success": False,
                "message": f"添加板块失败: {str(e)}"
            }
    
    async def holdings_remove_sector(self, sector_name: str) -> dict:
        """
        Remove sector from holdings
        
        Args:
            sector_name: Sector name
        
        Returns:
            Success message
        """
        try:
            success = await holding_manager.remove_sector(sector_name)
            if success:
                return {
                    "success": True,
                    "message": f"成功删除板块 {sector_name}"
                }
            else:
                return {
                    "success": False,
                    "message": "删除板块失败（可能不存在或还有股票）"
                }
        except Exception as e:
            logger.error(f"Failed to remove sector: {str(e)}")
            return {
                "success": False,
                "message": f"删除板块失败: {str(e)}"
            }
    
    async def holdings_rename_sector(self, old_name: str, new_name: str) -> dict:
        """
        Rename sector
        
        Args:
            old_name: Current sector name
            new_name: New sector name
        
        Returns:
            Success message
        """
        try:
            success = await holding_manager.rename_sector(old_name, new_name)
            if success:
                return {
                    "success": True,
                    "message": f"成功重命名板块 {old_name} 为 {new_name}"
                }
            else:
                return {
                    "success": False,
                    "message": "重命名板块失败"
                }
        except Exception as e:
            logger.error(f"Failed to rename sector: {str(e)}")
            return {
                "success": False,
                "message": f"重命名板块失败: {str(e)}"
            }
    
    async def holdings_list(self) -> dict:
        """
        List all holdings
        
        Returns:
            Holdings data with sectors and stocks
        """
        try:
            holdings = await holding_manager.load_holdings()
            return {
                "success": True,
                "data": holdings.model_dump()
            }
        except Exception as e:
            logger.error(f"Failed to list holdings: {str(e)}")
            return {
                "success": False,
                "message": f"获取持仓列表失败: {str(e)}"
            }
    
    # ============ Watchlist Operations ============
    
    async def watchlist_add_stock(
        self,
        db: AsyncSession,
        stock_name: str,
        watch_date: str,
        reason: Optional[str] = None,
        target_price: Optional[float] = None,
        stop_loss_price: Optional[float] = None,
        notes: Optional[str] = None,
        stock_code: Optional[str] = None
    ) -> dict:
        """
        Add stock to watchlist
        
        Args:
            db: Database session
            stock_name: Stock name
            watch_date: Watch date (YYYY-MM-DD)
            reason: Reason for watching
            target_price: Target price
            stop_loss_price: Stop loss price
            notes: Additional notes
            stock_code: Stock code (optional, auto-detected if not provided)
        
        Returns:
            Stock ID if successful
        """
        try:
            from models.daily_watchlist import WatchlistStockCreate
            
            stock_data = WatchlistStockCreate(
                stock_name=stock_name,
                stock_code=stock_code,
                watch_date=watch_date,
                reason=reason,
                target_price=target_price,
                stop_loss_price=stop_loss_price,
                notes=notes
            )
            
            stock = await daily_watchlist_manager.add_stock(db, stock_data)
            return {
                "success": True,
                "stock_id": stock.id,
                "message": f"成功添加 {stock_name} 到关注列表"
            }
        except Exception as e:
            logger.error(f"Failed to add stock to watchlist: {str(e)}")
            return {
                "success": False,
                "message": f"添加关注股票失败: {str(e)}"
            }
    
    async def watchlist_remove_stock(self, db: AsyncSession, stock_id: int) -> dict:
        """
        Remove stock from watchlist
        
        Args:
            db: Database session
            stock_id: Stock ID
        
        Returns:
            Success message
        """
        try:
            count = await daily_watchlist_manager.delete_stocks(db, stock_ids=[stock_id])
            if count > 0:
                return {
                    "success": True,
                    "message": f"成功删除关注股票"
                }
            else:
                return {
                    "success": False,
                    "message": "删除失败（股票不存在）"
                }
        except Exception as e:
            logger.error(f"Failed to remove stock from watchlist: {str(e)}")
            return {
                "success": False,
                "message": f"删除关注股票失败: {str(e)}"
            }
    
    async def watchlist_remove_by_date(self, db: AsyncSession, watch_date: str) -> dict:
        """
        Remove all stocks for a specific date
        
        Args:
            db: Database session
            watch_date: Watch date (YYYY-MM-DD)
        
        Returns:
            Success message with count
        """
        try:
            count = await daily_watchlist_manager.delete_stocks(db, watch_date=watch_date)
            return {
                "success": True,
                "message": f"成功删除 {count} 只关注股票",
                "count": count
            }
        except Exception as e:
            logger.error(f"Failed to remove stocks by date: {str(e)}")
            return {
                "success": False,
                "message": f"删除关注股票失败: {str(e)}"
            }
    
    async def watchlist_archive_stock(self, db: AsyncSession, stock_id: int) -> dict:
        """
        Archive stock from watchlist
        
        Args:
            db: Database session
            stock_id: Stock ID
        
        Returns:
            Success message
        """
        try:
            count = await daily_watchlist_manager.archive_stocks(db, stock_ids=[stock_id])
            if count > 0:
                return {
                    "success": True,
                    "message": "成功归档关注股票"
                }
            else:
                return {
                    "success": False,
                    "message": "归档失败（股票不存在）"
                }
        except Exception as e:
            logger.error(f"Failed to archive stock: {str(e)}")
            return {
                "success": False,
                "message": f"归档关注股票失败: {str(e)}"
            }
    
    async def watchlist_unarchive_stock(self, db: AsyncSession, stock_id: int) -> dict:
        """
        Unarchive stock from watchlist
        
        Args:
            db: Database session
            stock_id: Stock ID
        
        Returns:
            Success message
        """
        try:
            count = await daily_watchlist_manager.unarchive_stocks(db, stock_ids=[stock_id])
            if count > 0:
                return {
                    "success": True,
                    "message": "成功取消归档关注股票"
                }
            else:
                return {
                    "success": False,
                    "message": "取消归档失败（股票不存在）"
                }
        except Exception as e:
            logger.error(f"Failed to unarchive stock: {str(e)}")
            return {
                "success": False,
                "message": f"取消归档关注股票失败: {str(e)}"
            }
    
    async def watchlist_list(self, db: AsyncSession, include_archived: bool = False) -> dict:
        """
        List all watchlist stocks
        
        Args:
            db: Database session
            include_archived: Include archived stocks
        
        Returns:
            Watchlist summary data
        """
        try:
            summary = await daily_watchlist_manager.get_summary(
                db,
                include_archived=include_archived,
                limit=30
            )
            return {
                "success": True,
                "data": summary.model_dump()
            }
        except Exception as e:
            logger.error(f"Failed to list watchlist: {str(e)}")
            return {
                "success": False,
                "message": f"获取关注列表失败: {str(e)}"
            }
    
    async def watchlist_get_by_date(self, db: AsyncSession, watch_date: str, include_archived: bool = False) -> dict:
        """
        Get watchlist stocks for a specific date
        
        Args:
            db: Database session
            watch_date: Watch date (YYYY-MM-DD)
            include_archived: Include archived stocks
        
        Returns:
            List of stocks for the date
        """
        try:
            stocks = await daily_watchlist_manager.get_watchlist_by_date(
                db,
                watch_date,
                include_archived=include_archived
            )
            return {
                "success": True,
                "data": [stock.model_dump() for stock in stocks]
            }
        except Exception as e:
            logger.error(f"Failed to get watchlist by date: {str(e)}")
            return {
                "success": False,
                "message": f"获取指定日期关注列表失败: {str(e)}"
            }


# 全局 MCP 服务实例
mcp_service = MCPService()
