"""Daily watchlist related models"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date


class WatchlistStockCreate(BaseModel):
    """Create watchlist stock request"""
    stock_code: Optional[str] = Field(None, description="Stock code (optional, will auto-detect)")
    stock_name: str = Field(..., description="Stock name")
    watch_date: date = Field(..., description="Watch date")
    reason: Optional[str] = Field(None, description="Reason for watching")
    target_price: Optional[float] = Field(None, description="Target price")
    change_up_pct: Optional[float] = Field(None, description="Change up control percentage")
    change_down_pct: Optional[float] = Field(None, description="Change down control percentage")
    stop_loss_price: Optional[float] = Field(None, description="Stop loss price")
    notes: Optional[str] = Field(None, description="Additional notes")


class WatchlistStockUpdate(BaseModel):
    """Update watchlist stock request"""
    stock_code: Optional[str] = Field(None, description="Stock code")
    reason: Optional[str] = Field(None, description="Reason for watching")
    target_price: Optional[float] = Field(None, description="Target price")
    change_up_pct: Optional[float] = Field(None, description="Change up control percentage")
    change_down_pct: Optional[float] = Field(None, description="Change down control percentage")
    stop_loss_price: Optional[float] = Field(None, description="Stop loss price")
    notes: Optional[str] = Field(None, description="Additional notes")


class WatchlistStockResponse(BaseModel):
    """Watchlist stock response"""
    id: int
    stock_code: str
    stock_name: str
    watch_date: date
    reason: Optional[str] = None
    target_price: Optional[float] = None
    change_up_pct: Optional[float] = None
    change_down_pct: Optional[float] = None
    stop_loss_price: Optional[float] = None
    notes: Optional[str] = None
    price: Optional[float] = None
    change: Optional[float] = None
    change_pct: Optional[float] = None
    quote_timestamp: Optional[datetime] = None
    quote_is_updating: bool = False
    is_archived: bool
    archived_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WatchlistDateGroup(BaseModel):
    """Watchlist grouped by date"""
    watch_date: date
    stocks: List[WatchlistStockResponse]
    total_count: int = Field(..., description="Total number of stocks on this date")


class WatchlistSummary(BaseModel):
    """Watchlist summary"""
    dates: List[WatchlistDateGroup]
    total_dates: int = Field(..., description="Total number of dates")
    total_stocks: int = Field(..., description="Total number of stocks")


class ArchiveRequest(BaseModel):
    """Archive watchlist stock request"""
    stock_ids: Optional[List[int]] = Field(None, description="Stock IDs to archive (if None, archive all stocks on the date)")
    watch_date: Optional[date] = Field(None, description="Archive all stocks on this date (used if stock_ids is None)")


class UnarchiveRequest(BaseModel):
    """Unarchive watchlist stock request"""
    stock_ids: List[int] = Field(..., description="Stock IDs to unarchive")


class DeleteRequest(BaseModel):
    """Delete watchlist stock request"""
    stock_ids: Optional[List[int]] = Field(None, description="Stock IDs to delete (if None, delete all stocks on the date)")
    watch_date: Optional[date] = Field(None, description="Delete all stocks on this date (used if stock_ids is None)")
