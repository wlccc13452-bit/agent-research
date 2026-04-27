"""Holdings management routes"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from services.holdings_manager import holdings_manager

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models
class SectorRequest(BaseModel):
    sector_name: str


class StockRequest(BaseModel):
    stock_name: str
    sector_name: str


class MoveStockRequest(BaseModel):
    stock_name: str
    from_sector: str
    to_sector: str


class RemoveStockRequest(BaseModel):
    stock_name: str
    sector_name: Optional[str] = None


# Endpoints
@router.get("")
async def get_holdings():
    """Get all holdings (sectors and stocks)"""
    try:
        data = holdings_manager.read_holdings()
        logger.info(f"Returned holdings: {len(data['sectors'])} sectors")
        return data
    except Exception as e:
        logger.error(f"Failed to get holdings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sector")
async def add_sector(request: SectorRequest):
    """Add a new sector"""
    try:
        success = holdings_manager.add_sector(request.sector_name)
        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to add sector '{request.sector_name}' (may already exist)")
        
        # Broadcast update via WebSocket
        await _broadcast_holdings_update("sector_added", f"Added sector: {request.sector_name}")
        
        logger.info(f"Added sector: {request.sector_name}")
        return {"message": f"Successfully added sector: {request.sector_name}", "sector_name": request.sector_name}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add sector: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sector")
async def remove_sector(request: SectorRequest):
    """Remove a sector"""
    try:
        success = holdings_manager.remove_sector(request.sector_name)
        if not success:
            raise HTTPException(status_code=404, detail=f"Sector '{request.sector_name}' not found")
        
        # Broadcast update via WebSocket
        await _broadcast_holdings_update("sector_removed", f"Removed sector: {request.sector_name}")
        
        logger.info(f"Removed sector: {request.sector_name}")
        return {"message": f"Successfully removed sector: {request.sector_name}", "sector_name": request.sector_name}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove sector: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stock")
async def add_stock(request: StockRequest):
    """Add a stock to a sector (auto-create sector if not exists)"""
    try:
        # Check if sector exists
        current_holdings = holdings_manager.read_holdings()
        sector_exists = any(s['name'] == request.sector_name for s in current_holdings['sectors'])
        
        success = holdings_manager.add_stock(request.stock_name, request.sector_name, auto_create_sector=True)
        if not success:
            raise HTTPException(status_code=400, detail=f"Stock '{request.stock_name}' already exists in sector '{request.sector_name}'")
        
        # Broadcast update via WebSocket
        if not sector_exists:
            message = f"Auto-created sector '{request.sector_name}' and added stock {request.stock_name}"
        else:
            message = f"Added stock {request.stock_name} to sector {request.sector_name}"
        
        await _broadcast_holdings_update("stock_added", message)
        
        logger.info(f"Added stock {request.stock_name} to sector {request.sector_name}")
        return {
            "message": message,
            "stock_name": request.stock_name,
            "sector_name": request.sector_name,
            "sector_auto_created": not sector_exists
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add stock: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/stock")
async def remove_stock(request: RemoveStockRequest):
    """Remove a stock from a sector (or all sectors if sector_name is None)"""
    try:
        success = holdings_manager.remove_stock(request.stock_name, request.sector_name)
        if not success:
            if request.sector_name:
                detail = f"Stock '{request.stock_name}' not found in sector '{request.sector_name}'"
            else:
                detail = f"Stock '{request.stock_name}' not found in any sector"
            raise HTTPException(status_code=404, detail=detail)
        
        # Broadcast update via WebSocket
        if request.sector_name:
            await _broadcast_holdings_update("stock_removed", f"Removed stock {request.stock_name} from sector {request.sector_name}")
        else:
            await _broadcast_holdings_update("stock_removed", f"Removed stock {request.stock_name} from all sectors")
        
        logger.info(f"Removed stock {request.stock_name} from sector {request.sector_name or 'all'}")
        return {
            "message": f"Successfully removed stock {request.stock_name}",
            "stock_name": request.stock_name,
            "sector_name": request.sector_name
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove stock: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stock/move")
async def move_stock(request: MoveStockRequest):
    """Move a stock from one sector to another"""
    try:
        success = holdings_manager.move_stock(request.stock_name, request.from_sector, request.to_sector)
        if not success:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to move stock '{request.stock_name}' from '{request.from_sector}' to '{request.to_sector}'"
            )
        
        # Broadcast update via WebSocket
        await _broadcast_holdings_update(
            "stock_moved", 
            f"Moved stock {request.stock_name} from {request.from_sector} to {request.to_sector}"
        )
        
        logger.info(f"Moved stock {request.stock_name} from {request.from_sector} to {request.to_sector}")
        return {
            "message": f"Successfully moved stock {request.stock_name}",
            "stock_name": request.stock_name,
            "from_sector": request.from_sector,
            "to_sector": request.to_sector
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to move stock: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket broadcast helper
async def _broadcast_holdings_update(update_type: str, message: str):
    """Broadcast holdings update via WebSocket"""
    try:
        from services.realtime_pusher import realtime_pusher
        from datetime import datetime
        await realtime_pusher.broadcast({
            "type": "holdings_updated",
            "update_type": update_type,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.warning(f"Failed to broadcast holdings update: {str(e)}")
