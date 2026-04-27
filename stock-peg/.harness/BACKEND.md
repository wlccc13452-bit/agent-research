# BACKEND.md - Backend Development Standards

## Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.13 | Runtime |
| FastAPI | 0.109+ | Web Framework |
| UV | - | Package Manager |
| SQLAlchemy | 2.0+ | ORM |
| Pydantic | 2.5+ | Data Validation |
| SQLite | - | Database |
| aiosqlite | - | Async SQLite |

---

## Directory Structure

```
backend/
├── config/           # Configuration management
│   ├── settings.py   # Pydantic Settings
│   └── .env          # Environment variables
├── database/         # Database layer
│   ├── models.py     # ORM models
│   ├── session.py    # Session management
│   ├── operations/   # Database operations layer (NEW)
│   │   ├── __init__.py        # Exports all ops
│   │   ├── chat_message_ops.py
│   │   ├── data_update_ops.py
│   │   └── ... (other ops)
│   └── __init__.py   # Initialization
├── models/           # Pydantic models (API I/O)
├── routers/          # API routes
├── services/         # Business logic layer
├── middleware/       # Middleware
├── utils/            # Utility functions
├── data/             # Data storage
├── logs/             # Log files
└── main.py           # Entry point
```

---

## Layered Architecture

```
Routers (Route Layer)
    ↓ calls
Services (Service Layer)
    ↓ calls
Database Operations Layer (NEW - database/operations/)
    ↓ calls
Database Models (ORM Layer)
```

**IMPORTANT**: Routers and Services MUST NOT use SQLAlchemy query builders directly.
All database queries MUST go through `database/operations/*_ops.py` functions.

---

## Interface Ownership (Single Source)

- This file is the single source of truth for backend-facing interfaces.
- Maintain complete backend interface details here:
  - Frontend ↔ Backend API contract
  - External/public API contract
  - MCP tool and resource capability contract
- `FRONTEND.md` should keep consumption patterns only, not backend interface catalog.
- `ARCHITECTURE.md` should keep topology and boundaries only, not endpoint/tool inventories.

---

## Public Interface Surface

### Frontend-Facing HTTP APIs (via `/api/*`)

| Module | Endpoint | Method | Purpose |
|--------|----------|--------|---------|
| Holdings | `/api/holdings` | GET | Return holdings list |
| Daily Watchlist | `/api/daily-watchlist/summary` | GET | Return grouped watchlist |
| Daily Watchlist | `/api/daily-watchlist/stock` | POST | Add watchlist stock |
| Daily Watchlist | `/api/daily-watchlist/stock` | DELETE | Remove watchlist stock |
| Stocks | `/api/stocks/{code}/quote` | GET | Return real-time quote |
| Stocks | `/api/stocks/{code}/kline` | GET | Return K-line data |
| Indicators | `/api/indicators/force-index/{code_or_name}` | GET | Return Force Index |
| Fundamental | `/api/fundamental/{code}` | GET | Return financial metrics |
| Reports | `/api/reports/daily` | GET | Return daily report |

### Frontend-Facing WebSocket

- Endpoint: `/ws`
- Core push types:
  - `startup_progress`
  - `kline_updated`
  - `holdings_updated`
  - `watchlist_updated`
  - `price_update`
  - `fundamental_updated`

### External System Interfaces

- Market data providers: Tencent API, EastMoney API, Tushare, Akshare, yfinance
- AI providers: OpenAI, Anthropic, Zhipu AI
- All external calls must follow non-blocking and cache-first strategy.

---

## MCP Capability Surface

### MCP Server Entry

- Location: `backend/mcp_server/server.py`
- Server name: `Stock PEG Data Server`
- Tool namespace format: `mcp__stock_peg_data__<tool_name>`

### MCP Tools

- Quote/Kline: `get_stock_quote`, `get_batch_quotes`, `get_stock_kline`
- Technical indicators: `get_technical_indicators`, `get_force_index`, `get_pmr`
- Fundamental: `get_fundamental_analysis`, `get_valuation_metrics`
- Market sentiment/index: `get_market_sentiment`, `get_market_indices`
- Sector: `get_industry_sectors`, `get_concept_sectors`
- Fund flow/position: `get_stock_fund_flow`, `get_north_money_flow`, `get_holdings`
- US market/macro: `get_us_market_indices`, `get_macro_cpi`, `get_macro_gdp`, `get_macro_pmi`

### MCP Resources

- `stock://{stock_code}/quote`
- `stock://{stock_code}/kline`
- `market://sentiment`

### Router Responsibilities
- Define API endpoints
- Request parameter validation (Pydantic)
- Call Service layer
- Return response

```python
# routers/stock.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from services.stock_service import StockService

router = APIRouter()

@router.get("/{code}/kline")
async def get_kline(
    code: str,
    period: str = "day",
    db: AsyncSession = Depends(get_db)
):
    """Get K-line data"""
    service = StockService(db)
    return await service.get_kline_data(code, period)
```

### Service Responsibilities
- Business logic
- Data processing
- External API calls
- Database operations

```python
# services/stock_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import StockKLineData

class StockService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_kline_data(self, code: str, period: str) -> dict:
        """Get K-line data"""
        stmt = select(StockKLineData).where(
            StockKLineData.stock_code == code,
            StockKLineData.period == period
        ).order_by(StockKLineData.trade_date.desc()).limit(100)
        
        result = await self.db.execute(stmt)
        records = result.scalars().all()
        
        return {"code": code, "data": [r.to_dict() for r in records]}
```

---

## Non-Blocking Principle

### Core Rule
When frontend requests, backend **IMMEDIATELY RETURNS** existing data, **NOT WAITING** for external data fetch.

```python
# ✅ Correct approach
@router.get("/{code}/kline")
async def get_kline(code: str, db: AsyncSession = Depends(get_db)):
    data = await service.get_cached_kline(code)
    
    if data is None:
        # Data doesn't exist, start background update, but return immediately
        await background_updater.submit_kline_update(code)
        raise HTTPException(404, "Data not found, background update started")
    
    return data

# ❌ Wrong approach
@router.get("/{code}/kline")
async def get_kline(code: str, db: AsyncSession = Depends(get_db)):
    data = await fetch_external_api(code)  # Blocking wait for external API
    return data
```

### Background Update Mechanism
```python
# services/background_updater.py
class BackgroundUpdater:
    def __init__(self):
        self.queue = asyncio.Queue()
    
    async def submit_kline_update(self, code: str) -> None:
        """Submit background update task"""
        await self.queue.put(("kline", code))
    
    async def run(self):
        """Background task loop"""
        while True:
            task_type, code = await self.queue.get()
            try:
                await self._update_kline(code)
                # Push WebSocket after update completes
                await ws_manager.broadcast({
                    "type": "kline_updated",
                    "code": code
                })
            except Exception as e:
                logger.error(f"Update {code} failed: {e}")
```

---

## Database Standards

### Database Operations Layer (NEW)

All database queries MUST go through the operations layer to ensure:
- Single source of truth for query logic
- Centralized transaction management
- Easier testing and maintenance
- Consistent error handling

```python
# database/operations/chat_message_ops.py
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import FeishuChatMessage
from typing import List, Optional

async def get_chat_history(
    db: AsyncSession,
    chat_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[FeishuChatMessage]:
    """Get chat history with optional chat_id filter"""
    stmt = select(FeishuChatMessage)
    
    if chat_id:
        stmt = stmt.where(FeishuChatMessage.chat_id == chat_id)
    
    stmt = stmt.order_by(desc(FeishuChatMessage.send_time)) \
        .limit(limit) \
        .offset(offset)
    
    result = await db.execute(stmt)
    return result.scalars().all()
```

### Usage in Routers/Services

```python
# ✅ Correct - Use ops layer
from database.operations import get_chat_history, save_chat_message

@router.get("/history")
async def get_history(db: AsyncSession = Depends(get_db)):
    messages = await get_chat_history(db, limit=100)
    return {"messages": messages}

# ❌ Wrong - Direct SQLAlchemy usage
from sqlalchemy import select, desc

@router.get("/history")
async def get_history(db: AsyncSession = Depends(get_db)):
    query = select(FeishuChatMessage).order_by(desc(...))  # FORBIDDEN
    result = await db.execute(query)
    return result.scalars().all()
```

### ORM Model
```python
# database/models.py
from sqlalchemy import Column, String, Float, DateTime, Integer
from sqlalchemy.sql import func
from database.base import Base

class StockKLineData(Base):
    __tablename__ = "stock_kline_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(20), nullable=False, index=True)
    trade_date = Column(DateTime, nullable=False, index=True)
    period = Column(String(10), default="day")
    open = Column(Float)
    close = Column(Float)
    high = Column(Float)
    low = Column(Float)
    volume = Column(Float)
    amount = Column(Float)
    created_at = Column(DateTime, server_default=func.now())
    
    def to_dict(self) -> dict:
        return {
            "code": self.stock_code,
            "date": self.trade_date.strftime("%Y-%m-%d"),
            "open": self.open,
            "close": self.close,
            "high": self.high,
            "low": self.low,
            "volume": self.volume,
            "amount": self.amount,
        }
```

### Async Session
```python
# database/session.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

engine = create_async_engine(
    "sqlite+aiosqlite:///data/stock_peg.db",
    echo=False,
    future=True
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
```

---

## Pydantic Models

### API Request/Response
```python
# models/stock.py
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, List

class KLineRequest(BaseModel):
    code: str = Field(..., description="Stock code")
    period: str = Field(default="day", description="Period")
    limit: int = Field(default=100, ge=1, le=500)

class KLineItem(BaseModel):
    date: date
    open: float
    close: float
    high: float
    low: float
    volume: int
    amount: float

class KLineResponse(BaseModel):
    code: str
    period: str
    data: List[KLineItem]
    count: int
```

---

## Configuration Management

### Pydantic Settings
```python
# config/settings.py
from pydantic_settings import BaseSettings
from pydantic import field_validator
from pathlib import Path

class Settings(BaseSettings):
    app_name: str = "Stock PEG"
    app_version: str = "0.1.0"
    debug: bool = False
    
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    
    database_url: str = "sqlite+aiosqlite:///./data/stock_peg.db"
    
    tushare_token: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    
    @field_validator("database_url", mode="before")
    @classmethod
    def convert_db_url(cls, v: str) -> str:
        if v.startswith("sqlite://") and "aiosqlite" not in v:
            return v.replace("sqlite://", "sqlite+aiosqlite://")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

---

## Error Handling

### Unified Error Response
```python
# utils/exceptions.py
from fastapi import HTTPException

class DataNotFoundError(HTTPException):
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            status_code=404,
            detail=f"{resource} '{identifier}' not found"
        )

class ExternalAPIError(HTTPException):
    def __init__(self, service: str, message: str):
        super().__init__(
            status_code=502,
            detail=f"{service} service error: {message}"
        )
```

### Global Exception Handler
```python
# main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

---

## Logging Standards

```python
import logging

logger = logging.getLogger(__name__)

# Usage
logger.debug("Debug info")
logger.info("✅ Operation successful")
logger.warning("⚠ Warning message")
logger.error("❌ Error message", exc_info=True)
```

---

## WebSocket Push

```python
# services/websocket_manager.py
from fastapi import WebSocket
from typing import List
import json

class WebSocketManager:
    def __init__(self):
        self.connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        data = json.dumps(message, ensure_ascii=False)
        for conn in self.connections:
            await conn.send_text(data)

manager = WebSocketManager()
```

---

## Dependency Management

### UV Commands
```powershell
# Install all dependencies
Set-Location backend
uv sync

# Add dependency
uv add pandas

# Add dev dependency
uv add --dev pytest

# Remove dependency
uv remove pandas
```

### pyproject.toml Structure
```toml
[project]
name = "stock-peg"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    # ...
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "black>=24.1.0",
    "ruff>=0.1.0",
]
```

---

## Prohibitions

1. ❌ Writing business logic in Router layer
2. ❌ Synchronous database operations (must use async)
3. ❌ Blocking wait for external APIs
4. ❌ Omitting type annotations
5. ❌ Hardcoding configuration values
6. ❌ Directly returning ORM objects (must convert to dict or Pydantic)
7. ❌ Handling HTTP request/response in Service layer
8. ❌ **Using SQLAlchemy query builders in Routers/Services** (MUST use operations layer)
   - Forbidden: `select()`, `delete()`, `update()`, `insert()`, `func`, `text()`
   - Required: Use `database/operations/*_ops.py` functions
