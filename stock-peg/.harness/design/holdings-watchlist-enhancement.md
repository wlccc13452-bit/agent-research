# Holdings and Watchlist Enhancement Design

**Date**: 2026-03-14
**Author**: AI Agent
**Status**: Design Phase

---

## Overview

This document describes the comprehensive enhancement plan for holdings management and daily watchlist features, including frontend UI, backend API, and MCP interfaces.

---

## Current Status Analysis

### Holdings (自持股票)
- **Current**: Displayed by sector, support add/remove stocks
- **Issue**: Cannot add new sectors dynamically
- **Data Source**: `自持股票.md` file

### Daily Watchlist (每日关注)
- **Current**: Displayed by date, support CRUD operations
- **Issue**: No stock code auto-detection for some stocks
- **Data Source**: SQLite database

---

## Enhancement Requirements

### 1. Holdings Enhancement

#### 1.1 Add Sector Feature
- User can add new sectors dynamically
- New sector appears at the top of sector list
- Empty sectors can be deleted

#### 1.2 Add Stock Enhancement
- Improve stock name/code auto-detection
- Support batch add (multiple stocks at once)
- Support adding stocks without specifying sector (creates "未分类" sector)

#### 1.3 Edit Sector Name
- Allow renaming existing sectors
- Update all stocks under the sector

#### 1.4 Delete Sector
- Delete entire sector with all stocks
- Confirmation required

### 2. Watchlist Enhancement

#### 2.1 UI Structure Change
- Display as date tree: 当前日期 → 关注股票列表
- Each date node shows:
  - Date label (YYYY-MM-DD)
  - Stock count
  - Expand/collapse icon
  - Quick actions (delete all, archive all)

#### 2.2 Date Grouping
- Group stocks by `watch_date`
- Sort dates descending (most recent first)
- Show relative date (今天, 昨天, X天前)

#### 2.3 Stock Card Enhancement
- Show stock code and name
- Display reason for watching
- Show target price / stop loss price (if set)
- Quick actions: edit, delete, archive

#### 2.4 Add Stock Flow
1. User clicks "添加关注"
2. Dialog shows:
   - Stock name input (with auto-suggestion)
   - Stock code input (auto-detected if possible)
   - Date picker (default: today)
   - Reason text area
   - Target price / stop loss price inputs
   - Notes text area
3. Submit to API
4. Refresh list

### 3. MCP Interface (For AI Agent)

#### 3.1 Holdings MCP Operations
```typescript
// Add stock to holdings
mcp__holdings_add_stock(sector: string, stock_name: string, stock_code?: string)

// Remove stock from holdings
mcp__holdings_remove_stock(sector: string, stock_name: string)

// Add new sector
mcp__holdings_add_sector(sector_name: string)

// Remove sector
mcp__holdings_remove_sector(sector_name: string)

// Rename sector
mcp__holdings_rename_sector(old_name: string, new_name: string)

// List all holdings
mcp__holdings_list()
```

#### 3.2 Watchlist MCP Operations
```typescript
// Add stock to watchlist
mcp__watchlist_add_stock(stock_name: string, watch_date: string, reason?: string, ...)

// Remove stock from watchlist
mcp__watchlist_remove_stock(stock_id: number)

// Remove all stocks for a date
mcp__watchlist_remove_by_date(watch_date: string)

// Archive stock
mcp__watchlist_archive_stock(stock_id: number)

// Unarchive stock
mcp__watchlist_unarchive_stock(stock_id: number)

// List watchlist
mcp__watchlist_list(include_archived: boolean)

// Get stocks for a specific date
mcp__watchlist_get_by_date(watch_date: string)
```

---

## Implementation Plan

### Phase 1: Backend API Enhancement (2-3 hours)

#### 1.1 Holdings API
- [ ] `POST /api/holdings/sectors` - Add new sector
- [ ] `DELETE /api/holdings/sectors/{sector_name}` - Remove sector
- [ ] `PUT /api/holdings/sectors/{sector_name}` - Rename sector
- [ ] Enhance `POST /api/holdings/stocks` - Support auto-create sector

#### 1.2 Watchlist API
- [ ] Already implemented, verify all endpoints work
- [ ] Add stock code auto-detection enhancement
- [ ] Add batch operations if needed

#### 1.3 Testing
- [ ] Test all API endpoints with curl
- [ ] Verify database operations
- [ ] Check error handling

### Phase 2: MCP Interface Development (1-2 hours)

#### 2.1 Create MCP Service
- [ ] Create `services/mcp_service.py`
- [ ] Implement holdings MCP operations
- [ ] Implement watchlist MCP operations

#### 2.2 Register MCP Routes
- [ ] Create `routers/mcp.py`
- [ ] Register MCP endpoints
- [ ] Add authentication (if needed)

#### 2.3 Testing
- [ ] Test MCP endpoints with curl
- [ ] Verify AI Agent can call MCP functions
- [ ] Document MCP API

### Phase 3: Frontend UI Implementation (3-4 hours)

#### 3.1 Holdings Enhancement
- [ ] Add "添加板块" button
- [ ] Create AddSectorDialog component
- [ ] Create EditSectorDialog component
- [ ] Add sector delete confirmation
- [ ] Improve AddStockDialog with sector auto-creation

#### 3.2 Watchlist Enhancement
- [ ] Refactor date tree display
- [ ] Create WatchlistDateNode component
- [ ] Create WatchlistStockCard component
- [ ] Enhance AddWatchlistDialog
- [ ] Add relative date display

#### 3.3 Testing
- [ ] Test all UI interactions
- [ ] Verify API calls
- [ ] Check responsive design
- [ ] Test error states

### Phase 4: Integration Testing (1-2 hours)

#### 4.1 End-to-End Testing
- [ ] Test complete user flows
- [ ] Verify data persistence
- [ ] Check WebSocket updates
- [ ] Test across browsers

#### 4.2 AI Agent Testing
- [ ] Test MCP operations via AI Agent
- [ ] Verify holdings management
- [ ] Verify watchlist management
- [ ] Check error handling

### Phase 5: Documentation (30 minutes)

- [ ] Update API documentation
- [ ] Update progress.md
- [ ] Create session summary
- [ ] Update SKILL files if needed

---

## Technical Decisions

### D019: Sector Auto-Creation Strategy
- **Decision**: When adding stock without sector, create "未分类" sector automatically
- **Reason**: Simplify user workflow, reduce friction
- **Impact**: Backend API needs to handle sector creation transparently

### D020: Watchlist Date Display Format
- **Decision**: Show relative date (今天, 昨天) for recent dates, absolute date for older ones
- **Reason**: Better UX, easier to scan
- **Impact**: Frontend needs date calculation logic

### D021: MCP Authentication
- **Decision**: No authentication for now, rely on local development environment
- **Reason**: Simplified development, single-user scenario
- **Impact**: Future multi-user support will need authentication

---

## API Specification

### Holdings API

```http
POST /api/holdings/sectors
Content-Type: application/json

{
  "sector_name": "金融"
}

Response:
{
  "message": "Sector created successfully",
  "sector": {
    "name": "金融",
    "stocks": []
  }
}
```

```http
DELETE /api/holdings/sectors/{sector_name}

Response:
{
  "message": "Sector deleted successfully",
  "deleted_stocks_count": 5
}
```

```http
PUT /api/holdings/sectors/{sector_name}
Content-Type: application/json

{
  "new_name": "金融科技"
}

Response:
{
  "message": "Sector renamed successfully",
  "sector": {
    "name": "金融科技",
    "stocks": [...]
  }
}
```

### MCP API

```http
POST /api/mcp/holdings/add-stock
Content-Type: application/json

{
  "sector": "科技",
  "stock_name": "腾讯控股",
  "stock_code": "00700"
}

Response:
{
  "success": true,
  "message": "Stock added successfully"
}
```

```http
POST /api/mcp/watchlist/add-stock
Content-Type: application/json

{
  "stock_name": "方正科技",
  "watch_date": "2026-03-14",
  "reason": "技术突破"
}

Response:
{
  "success": true,
  "stock_id": 1
}
```

---

## Database Schema

### DailyWatchlist (existing)
```sql
CREATE TABLE daily_watchlist (
  id INTEGER PRIMARY KEY,
  stock_code TEXT,
  stock_name TEXT NOT NULL,
  watch_date DATE NOT NULL,
  reason TEXT,
  target_price REAL,
  stop_loss_price REAL,
  notes TEXT,
  is_archived BOOLEAN DEFAULT 0,
  archived_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(stock_code, watch_date)
);
```

### Holdings (file-based)
No database changes needed. Holdings are stored in `自持股票.md`.

---

## Success Criteria

1. ✅ User can add/remove sectors dynamically
2. ✅ User can add stocks to holdings with improved UX
3. ✅ Watchlist displays in date tree structure
4. ✅ All API endpoints tested and working
5. ✅ MCP operations work correctly
6. ✅ No critical bugs in production
7. ✅ Documentation updated

---

## Risks and Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| File-based holdings may have concurrency issues | Medium | Use file locking, implement retry logic |
| MCP operations may conflict with manual operations | Low | Document operational guidelines |
| Frontend state management complexity | Medium | Use TanStack Query for caching |

---

## Timeline

- **Phase 1**: Backend API Enhancement - 2-3 hours
- **Phase 2**: MCP Interface - 1-2 hours
- **Phase 3**: Frontend UI - 3-4 hours
- **Phase 4**: Testing - 1-2 hours
- **Phase 5**: Documentation - 30 minutes

**Total**: 8-12 hours (can be done across multiple sessions)

---

## Next Steps

1. Start with Phase 1: Backend API Enhancement
2. Create detailed API implementation
3. Test each endpoint before moving to next phase
4. Follow mandatory testing protocol
