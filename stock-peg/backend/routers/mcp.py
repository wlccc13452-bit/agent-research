"""MCP API routes for AI Agent operations"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from services.mcp_service import mcp_service
from database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ Request Models ============

class HoldingsAddStockRequest(BaseModel):
    sector: str
    stock_name: str
    stock_code: Optional[str] = None


class HoldingsRemoveStockRequest(BaseModel):
    sector: str
    stock_name: str


class HoldingsAddSectorRequest(BaseModel):
    sector_name: str


class HoldingsRenameSectorRequest(BaseModel):
    old_name: str
    new_name: str


class WatchlistAddStockRequest(BaseModel):
    stock_name: str
    watch_date: str
    reason: Optional[str] = None
    target_price: Optional[float] = None
    stop_loss_price: Optional[float] = None
    notes: Optional[str] = None
    stock_code: Optional[str] = None


class WatchlistRemoveStockRequest(BaseModel):
    stock_id: int


class WatchlistRemoveByDateRequest(BaseModel):
    watch_date: str


class WatchlistArchiveRequest(BaseModel):
    stock_id: int


class WatchlistUnarchiveRequest(BaseModel):
    stock_id: int


class WatchlistListRequest(BaseModel):
    include_archived: bool = False


class WatchlistGetByDateRequest(BaseModel):
    watch_date: str
    include_archived: bool = False


# ============ Holdings MCP Operations ============

@router.post("/holdings/add-stock")
async def mcp_holdings_add_stock(
    request: HoldingsAddStockRequest
):
    """MCP: Add stock to holdings"""
    result = await mcp_service.holdings_add_stock(
        sector=request.sector,
        stock_name=request.stock_name,
        stock_code=request.stock_code
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/holdings/remove-stock")
async def mcp_holdings_remove_stock(
    request: HoldingsRemoveStockRequest
):
    """MCP: Remove stock from holdings"""
    result = await mcp_service.holdings_remove_stock(
        sector=request.sector,
        stock_name=request.stock_name
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/holdings/add-sector")
async def mcp_holdings_add_sector(
    request: HoldingsAddSectorRequest
):
    """MCP: Add new sector"""
    result = await mcp_service.holdings_add_sector(request.sector_name)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.delete("/holdings/remove-sector/{sector_name}")
async def mcp_holdings_remove_sector(sector_name: str):
    """MCP: Remove sector"""
    result = await mcp_service.holdings_remove_sector(sector_name)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.put("/holdings/rename-sector")
async def mcp_holdings_rename_sector(
    request: HoldingsRenameSectorRequest
):
    """MCP: Rename sector"""
    result = await mcp_service.holdings_rename_sector(
        old_name=request.old_name,
        new_name=request.new_name
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.get("/holdings/list")
async def mcp_holdings_list():
    """MCP: List all holdings"""
    result = await mcp_service.holdings_list()
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return result


# ============ Watchlist MCP Operations ============

@router.post("/watchlist/add-stock")
async def mcp_watchlist_add_stock(
    request: WatchlistAddStockRequest,
    db: AsyncSession = Depends(get_db)
):
    """MCP: Add stock to watchlist"""
    result = await mcp_service.watchlist_add_stock(
        db=db,
        stock_name=request.stock_name,
        watch_date=request.watch_date,
        reason=request.reason,
        target_price=request.target_price,
        stop_loss_price=request.stop_loss_price,
        notes=request.notes,
        stock_code=request.stock_code
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/watchlist/remove-stock")
async def mcp_watchlist_remove_stock(
    request: WatchlistRemoveStockRequest,
    db: AsyncSession = Depends(get_db)
):
    """MCP: Remove stock from watchlist"""
    result = await mcp_service.watchlist_remove_stock(db, request.stock_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/watchlist/remove-by-date")
async def mcp_watchlist_remove_by_date(
    request: WatchlistRemoveByDateRequest,
    db: AsyncSession = Depends(get_db)
):
    """MCP: Remove all stocks for a date"""
    result = await mcp_service.watchlist_remove_by_date(db, request.watch_date)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/watchlist/archive")
async def mcp_watchlist_archive(
    request: WatchlistArchiveRequest,
    db: AsyncSession = Depends(get_db)
):
    """MCP: Archive stock"""
    result = await mcp_service.watchlist_archive_stock(db, request.stock_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/watchlist/unarchive")
async def mcp_watchlist_unarchive(
    request: WatchlistUnarchiveRequest,
    db: AsyncSession = Depends(get_db)
):
    """MCP: Unarchive stock"""
    result = await mcp_service.watchlist_unarchive_stock(db, request.stock_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.get("/watchlist/list")
async def mcp_watchlist_list(
    include_archived: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """MCP: List all watchlist stocks"""
    result = await mcp_service.watchlist_list(db, include_archived)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return result


@router.get("/watchlist/get-by-date/{watch_date}")
async def mcp_watchlist_get_by_date(
    watch_date: str,
    include_archived: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """MCP: Get watchlist stocks by date"""
    result = await mcp_service.watchlist_get_by_date(db, watch_date, include_archived)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return result
