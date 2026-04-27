"""Daily watchlist management routes"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from datetime import date
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from models.daily_watchlist import (
    WatchlistStockCreate,
    WatchlistStockUpdate,
    WatchlistStockResponse,
    WatchlistSummary,
    ArchiveRequest,
    UnarchiveRequest,
    DeleteRequest
)
from services.daily_watchlist_manager import daily_watchlist_manager
from database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/summary", response_model=WatchlistSummary)
async def get_watchlist_summary(
    include_archived: bool = Query(False, description="Include archived stocks"),
    limit: int = Query(30, description="Maximum number of dates to return"),
    db: AsyncSession = Depends(get_db)
):
    """Get watchlist summary (grouped by date)
    
    Returns watchlist stocks grouped by date, with most recent dates first.
    """
    try:
        summary = await daily_watchlist_manager.get_summary(
            db,
            include_archived=include_archived,
            limit=limit
        )
        logger.info(f"Returned watchlist summary: {summary.total_dates} dates, {summary.total_stocks} stocks")
        return summary
    except Exception as e:
        logger.error(f"Failed to get watchlist summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dates")
async def get_all_dates(
    include_archived: bool = Query(False, description="Include archived stocks"),
    db: AsyncSession = Depends(get_db)
):
    """Get all watchlist dates
    
    Returns a list of all dates that have watchlist stocks.
    """
    try:
        dates = await daily_watchlist_manager.get_all_dates(
            db,
            include_archived=include_archived
        )
        logger.info(f"Returned {len(dates)} watchlist dates")
        return {"dates": dates}
    except Exception as e:
        logger.error(f"Failed to get watchlist dates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{watch_date}", response_model=list[WatchlistStockResponse])
async def get_watchlist_by_date(
    watch_date: date,
    include_archived: bool = Query(False, description="Include archived stocks"),
    db: AsyncSession = Depends(get_db)
):
    """Get watchlist stocks by date
    
    Returns all watchlist stocks for a specific date.
    """
    try:
        stocks = await daily_watchlist_manager.get_watchlist_by_date(
            db,
            watch_date,
            include_archived=include_archived
        )
        logger.info(f"Returned {len(stocks)} watchlist stocks for {watch_date}")
        return stocks
    except Exception as e:
        logger.error(f"Failed to get watchlist for {watch_date}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{stock_id}", response_model=WatchlistStockResponse)
async def get_stock(stock_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single watchlist stock by ID"""
    try:
        stock = await daily_watchlist_manager.get_stock(db, stock_id)
        if not stock:
            raise HTTPException(status_code=404, detail="Stock not found")
        return stock
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get watchlist stock {stock_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stock", response_model=WatchlistStockResponse)
async def add_stock(stock_data: WatchlistStockCreate, db: AsyncSession = Depends(get_db)):
    """Add a stock to watchlist
    
    - If stock_code is not provided, it will be auto-detected from stock_name
    - If the stock already exists on the same date, it will be updated
    """
    try:
        stock = await daily_watchlist_manager.add_stock(db, stock_data)
        
        # Broadcast update via WebSocket
        try:
            from services.realtime_pusher import realtime_pusher
            from datetime import datetime
            await realtime_pusher.broadcast({
                "type": "watchlist_updated",
                "message": f"Added stock {stock.stock_name} to watchlist",
                "watch_date": str(stock.watch_date),
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast watchlist update: {str(e)}")
        
        logger.info(f"Added stock {stock.stock_code} ({stock.stock_name}) to watchlist for {stock.watch_date}")
        return stock
    except Exception as e:
        logger.error(f"Failed to add stock to watchlist: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/stock/{stock_id}", response_model=WatchlistStockResponse)
async def update_stock(stock_id: int, stock_data: WatchlistStockUpdate, db: AsyncSession = Depends(get_db)):
    """Update a watchlist stock"""
    try:
        stock = await daily_watchlist_manager.update_stock(db, stock_id, stock_data)
        if not stock:
            raise HTTPException(status_code=404, detail="Stock not found")
        
        # Broadcast update via WebSocket
        try:
            from services.realtime_pusher import realtime_pusher
            from datetime import datetime
            await realtime_pusher.broadcast({
                "type": "watchlist_updated",
                "message": f"Updated stock {stock.stock_name}",
                "stock_id": stock_id,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast watchlist update: {str(e)}")
        
        logger.info(f"Updated watchlist stock {stock_id}")
        return stock
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update watchlist stock {stock_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/stock")
async def delete_stocks(request: DeleteRequest, db: AsyncSession = Depends(get_db)):
    """Delete watchlist stocks
    
    - If stock_ids is provided, delete those specific stocks
    - If watch_date is provided (and stock_ids is None), delete all stocks on that date
    """
    try:
        count = await daily_watchlist_manager.delete_stocks(
            db,
            stock_ids=request.stock_ids,
            watch_date=request.watch_date
        )
        
        # Broadcast update via WebSocket
        try:
            from services.realtime_pusher import realtime_pusher
            from datetime import datetime
            await realtime_pusher.broadcast({
                "type": "watchlist_updated",
                "message": f"Deleted {count} watchlist stocks",
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast watchlist update: {str(e)}")
        
        logger.info(f"Deleted {count} watchlist stocks")
        return {"message": f"Successfully deleted {count} stocks", "count": count}
    except Exception as e:
        logger.error(f"Failed to delete watchlist stocks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/archive")
async def archive_stocks(request: ArchiveRequest, db: AsyncSession = Depends(get_db)):
    """Archive watchlist stocks
    
    - If stock_ids is provided, archive those specific stocks
    - If watch_date is provided (and stock_ids is None), archive all stocks on that date
    """
    try:
        count = await daily_watchlist_manager.archive_stocks(
            db,
            stock_ids=request.stock_ids,
            watch_date=request.watch_date
        )
        
        # Broadcast update via WebSocket
        try:
            from services.realtime_pusher import realtime_pusher
            from datetime import datetime
            await realtime_pusher.broadcast({
                "type": "watchlist_updated",
                "message": f"Archived {count} watchlist stocks",
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast watchlist update: {str(e)}")
        
        logger.info(f"Archived {count} watchlist stocks")
        return {"message": f"Successfully archived {count} stocks", "count": count}
    except Exception as e:
        logger.error(f"Failed to archive watchlist stocks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/unarchive")
async def unarchive_stocks(request: UnarchiveRequest, db: AsyncSession = Depends(get_db)):
    """Unarchive watchlist stocks"""
    try:
        count = await daily_watchlist_manager.unarchive_stocks(
            db,
            stock_ids=request.stock_ids
        )
        
        # Broadcast update via WebSocket
        try:
            from services.realtime_pusher import realtime_pusher
            from datetime import datetime
            await realtime_pusher.broadcast({
                "type": "watchlist_updated",
                "message": f"Unarchived {count} watchlist stocks",
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast watchlist update: {str(e)}")
        
        logger.info(f"Unarchived {count} watchlist stocks")
        return {"message": f"Successfully unarchived {count} stocks", "count": count}
    except Exception as e:
        logger.error(f"Failed to unarchive watchlist stocks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
