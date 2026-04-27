# ARCHITECTURE.md - System Architecture

## Overall Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      User Interface (Frontend)                   │
│  React 19 + TypeScript + Vite + Tailwind + Zustand + TanStack  │
└─────────────────────────────┬───────────────────────────────────┘
                              │ HTTP/WebSocket
                              │ /api/* (Vite Proxy)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway (Backend)                       │
│                    FastAPI + Uvicorn                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Routers   │  │  WebSocket  │  │  Middleware │              │
│  └──────┬──────┘  └──────┬──────┘  └─────────────┘              │
│         │                │                                      │
│         ▼                ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    Services Layer                        │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │    │
│  │  │ StockService │  │ HoldingMgr   │  │ Background   │   │    │
│  │  └──────────────┘  └──────────────┘  │   Updater    │   │    │
│  │  ┌──────────────┐  ┌──────────────┐  └──────────────┘   │    │
│  │  │ Fundamental  │  │  US Market   │  ┌──────────────┐   │    │
│  │  │   Service    │  │   Service    │  │   AI Agent   │   │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Data Layer                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │           Database Operations Layer (NEW)                │    │
│  │  database/operations/*_ops.py                            │    │
│  │  - Encapsulates all SQLAlchemy query building            │    │
│  │  - Single source of truth for DB operations              │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              SQLite + SQLAlchemy ORM                     │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │    │
│  │  │  KLine Data  │  │ Fundamental  │  │   Holdings   │   │    │
│  │  │              │  │    Data      │  │              │   │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   自持股票.md (Core Config)               │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    External Data Sources                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ Tencent API  │  │ EastMoney API│  │   Tushare    │           │
│  │ (Real-time)  │  │ (Financials) │  │  (Historical)│           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   yfinance   │  │   OpenAI     │  │   Anthropic  │           │
│  │  (US Stocks) │  │  (AI Analysis)│  │ (AI Analysis)│           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Boundaries

### Boundary 1: Frontend ↔ Backend
- **Communication**: HTTP REST API + WebSocket
- **Frontend MUST NOT**: Directly access database, read file system
- **Backend Responsibility**: Provide complete, frontend-ready data structures

### Boundary 2: Backend ↔ External APIs
- **Communication**: HTTP/HTTPS
- **Strategy**: Non-blocking, background update, cache-first

### Boundary 3: Services/Routers ↔ Database
- **Communication**: SQLAlchemy async session
- **Transaction Management**: Each service method has independent transaction
- **Query Building**: MUST go through `database/operations/*_ops.py` layer
- **Prohibition**: Routers and Services MUST NOT use SQLAlchemy query builders directly
  - ❌ `select()`, `delete()`, `update()`, `insert()`, `func`, `text()`
  - ✅ Use ops functions: `get_chat_history()`, `save_chat_message()`, etc.

---

## Runtime Conventions

- Command instructions across architecture documents use PowerShell-first format.
- Operational examples should be executable in Windows PowerShell environments by default.
- Bash examples are optional fallback and should not replace primary PowerShell instructions.

---

## Data Flow

### 1. Startup Flow
```
Start Backend
    │
    ├── Initialize database (init_db)
    │
    ├── Start WebSocket Manager
    │
    ├── Start holding file watcher (holding_manager.start_watching)
    │
    ├── Start scheduled task scheduler (task_scheduler)
    │
    ├── Start real-time pusher (realtime_pusher)
    │
    ├── Start background updater (background_updater)
    │
    └── Preload market data (preload_market_data)
```

### 2. K-Line Data Fetch Flow
```
Frontend requests GET /api/stocks/{code}/kline
    │
    ▼
Router calls StockService.get_kline_data()
    │
    ├── Query database cache
    │       │
    │       ├── Exists → Return immediately
    │       │
    │       └── Not exists → 
    │               │
    │               ├── Return 404
    │               │
    │               └── Submit background update task
    │
    ▼
Frontend receives response (data or 404)

After background update completes:
    WebSocket.broadcast({ type: "kline_updated", code })
    │
    ▼
Frontend detects push, auto-refreshes
```

### 3. Holdings Change Flow
```
User edits 自持股票.md
    │
    ▼
holding_manager file watcher triggers
    │
    ├── Parse new holdings data
    │
    ├── Update database
    │
    └── WebSocket push { type: "holdings_updated" }
    │
    ▼
Frontend detects push, refreshes holdings list
```

---

## Interface Boundary Ownership

| Interface Category | Owner Document | Scope |
|-------------------|----------------|-------|
| Frontend consumption contract | `FRONTEND.md` | `/api/*` usage, `/ws` event handling, cache invalidation |
| Backend/public interface catalog | `BACKEND.md` | REST/WebSocket endpoint inventory, external API interfaces, MCP capability list |
| Topology and boundaries | `ARCHITECTURE.md` | Layer boundaries, data flow, responsibility ownership |

### Non-Duplication Rule

- Do not duplicate endpoint/tool lists in this file.
- Keep only architecture-level boundaries and data flow.
- Interface inventory changes must be updated in `BACKEND.md`.
- Frontend consumption behavior changes must be updated in `FRONTEND.md`.

---

## Background Tasks

### Scheduled Tasks (APScheduler)

| Task | Frequency | Description |
|------|-----------|-------------|
| Update real-time quotes | 5s | Intraday real-time push |
| Update K-line data | After market close daily | Fill missing data |
| Generate analysis report | Daily | AI analysis report |
| Clean expired logs | Weekly | Log maintenance |

### Async Queue

```python
# Background update queue
background_updater.submit_kline_update(code)      # K-line update
background_updater.submit_fundamental_update(code) # Financial update
background_updater.submit_us_index_update(symbol)  # US index update
```

---

## AI Integration

### Supported AI Services

| Service | Purpose | Config |
|---------|---------|--------|
| OpenAI | GPT-4 Analysis | `OPENAI_API_KEY` |
| Anthropic | Claude Analysis | `ANTHROPIC_API_KEY` |
| Zhipu AI | GLM Analysis | `ZHIPU_API_KEY` |

### AI Analysis Flow

```
Collect data (K-line + Financials + News)
    │
    ▼
Build Prompt
    │
    ▼
Call AI API
    │
    ▼
Parse response
    │
    ▼
Store analysis results
    │
    ▼
WebSocket push
```

---

## Security Considerations

1. **API Key Protection**: All API keys stored in `.env`, not committed to git
2. **CORS Configuration**: Only allow `localhost` and `127.0.0.1`
3. **Input Validation**: All input validated via Pydantic
4. **Error Messages**: Don't expose internal implementation details

---

## Performance Optimization

### Frontend
- TanStack Query caching (5-minute staleTime)
- Route lazy loading
- ECharts on-demand import

### Backend
- Database connection pool
- Async I/O (aiosqlite)
- Memory cache (K-line cache)
- Background tasks don't block main thread

### Database
- Key field indexes (stock_code, trade_date)
- Periodic VACUUM
- WAL mode
