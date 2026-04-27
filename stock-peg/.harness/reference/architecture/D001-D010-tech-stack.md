# D001-D010: Technology Stack Selection

**Priority**: Standard
**Date**: Project inception
**Last Updated**: 2026-03-01
**Status**: Active

This document consolidates technology stack decisions made at project start.

---

## Overview

Core technology stack selection for Stock PEG intelligent stock analysis platform.

---

## D001: State Management Solution

### Decision
Use **Zustand** for global state management.

### Reason
- Lightweight, simple API
- No Provider wrapper needed
- TypeScript friendly

### Alternatives
- Redux Toolkit (too heavy)
- Jotai (smaller ecosystem)

### Implementation
```typescript
// frontend/src/store/useAppStore.ts
import { create } from 'zustand'

interface AppState {
  holdings: Holdings[]
  selectedStock: string | null
  setSelectedStock: (code: string | null) => void
}

export const useAppStore = create<AppState>((set) => ({
  holdings: [],
  selectedStock: null,
  setSelectedStock: (code) => set({ selectedStock: code }),
}))
```

---

## D002: Server State Management

### Decision
Use **TanStack Query** for server state management.

### Reason
- Auto caching, refresh, retry
- Separated concerns from Zustand
- Excellent DevTools

### Alternatives
- SWR (fewer features)
- native fetch

### Implementation
```typescript
// frontend/src/services/api.ts
import { useQuery } from '@tanstack/react-query'

export function useStockQuote(stockCode: string) {
  return useQuery({
    queryKey: ['quote', stockCode],
    queryFn: () => fetchQuote(stockCode),
    staleTime: 5000, // 5 seconds
  })
}
```

---

## D003: UI Component Library

### Decision
Use **shadcn/ui style components**.

### Reason
- Component code copied directly, fully controllable
- Based on Radix UI, good accessibility
- Native Tailwind CSS support

### Alternatives
- Ant Design (hard to customize)
- MUI (bundle too large)

### Implementation
```typescript
// Components are copied directly into project
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
```

---

## D004: Backend Framework

### Decision
Use **FastAPI**.

### Reason
- Native async support
- Auto-generates OpenAPI docs
- Pydantic type validation

### Alternatives
- Flask (sync)
- Django (too heavy)

### Implementation
```python
# backend/main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/api/stocks/{code}")
async def get_stock(code: str):
    # Async endpoint
    pass
```

---

## D005: Database Choice

### Decision
Use **SQLite**.

### Reason
- Single machine deployment, no separate database service
- Simple development, data file is portable
- Sufficient performance (read-heavy workload)

### Alternatives
- PostgreSQL (over-engineered)

### Implementation
```python
# backend/database/session.py
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine

# SQLite async engine
engine = create_async_engine(
    "sqlite+aiosqlite:///./data/stock_peg.db",
    echo=False
)
```

---

## D006: Non-Blocking Architecture

### Decision
API requests return immediately, background async update.

### Reason
- External API response is unstable
- Improves user experience
- Avoids long frontend waits

### Impact
Need to implement WebSocket push mechanism.

### Implementation
```python
# backend/routers/stock.py
@router.get("/api/stocks/{code}/quote")
async def get_quote(code: str):
    # Return cached data immediately
    cached = await get_cached_quote(code)
    
    # Start background update
    asyncio.create_task(update_quote_async(code))
    
    return cached or {"status": "updating"}
```

---

## D007: Holdings Data Source

### Decision
Use `自持股票.md` as single source of truth.

### Reason
- User-familiar editing method
- Version controllable
- Simple and intuitive

### Alternatives
- Database storage (inconvenient editing)
- config UI (over-engineered)

### Implementation
```markdown
# 自持股票.md

## 新能源
- 比亚迪 (002594)
- 宁德时代 (300750)

## 白酒
- 贵州茅台 (600519)
```

---

## D008: Python Version

### Decision
Use **Python 3.13**.

### Reason
- Latest stable version
- Performance improvements
- Better async support

### Risk
Some library compatibility needs verification.

---

## D009: Package Manager

### Decision
- **Backend**: UV
- **Frontend**: npm

### Reason
- UV is fast, accurate dependency resolution
- npm ecosystem mature, team familiar

### Alternatives
- pip (slow)
- pnpm (needs team adaptation)

### Implementation
```bash
# Backend
cd backend
uv sync  # Install dependencies
uv add package-name  # Add new dependency

# Frontend
cd frontend
npm install
npm install package-name
```

---

## D010: Build Tool

### Decision
Frontend uses **Vite**.

### Reason
- Fast dev server startup
- Fast HMR response
- Native ESM support

### Alternatives
- Webpack (complex config)
- Create React App (outdated)

### Implementation
```json
// frontend/vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
```

---

## Lessons Learned

1. **Keep it simple**: Choose proven, well-documented technologies
2. **Type safety matters**: TypeScript + Pydantic catches errors early
3. **Async first**: FastAPI + TanStack Query handles async naturally
4. **Component control**: shadcn/ui gives full control without lock-in

---

## Related Documents

- `BACKEND.md` - Backend development standards
- `FRONTEND.md` - Frontend development standards
- `ARCHITECTURE.md` - System architecture overview
