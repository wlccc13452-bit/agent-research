# Daily Watchlist SKILL

> **Quick Start**: Manage daily watchlist through CLI commands

---

## Command Format

### View Current Watchlist
```
/daily-watchlist
```

### Add Stock to Watchlist
```
/daily-watchlist <股票名称> [日期] [理由]
```

**Examples**:
- `/daily-watchlist 南大光电` - Add to today's watchlist
- `/daily-watchlist 南大光电 2026-03-15` - Add to specific date
- `/daily-watchlist 南大光电 2026-03-15 突破前高` - Add with reason

### Remove Stock from Watchlist
```
/daily-watchlist remove <股票名称或ID>
```

**Examples**:
- `/daily-watchlist remove 南大光电` - Remove by name
- `/daily-watchlist remove 3` - Remove by ID

---

## Execution Steps

### Step 1: Parse Command
Extract: action (add/remove/view), stock_name, date, reason

### Step 2: Execute curl Command

#### View Watchlist
```bash
curl -s "http://localhost:8000/api/daily-watchlist/summary?include_archived=false&limit=30"
```

#### Add Stock
```bash
curl -X POST http://localhost:8000/api/daily-watchlist/stock \
  -H "Content-Type: application/json" \
  -d "{\"stock_name\":\"南大光电\",\"watch_date\":\"2026-03-15\",\"reason\":\"突破前高\"}"
```

**PowerShell**:
```powershell
curl -X POST http://localhost:8000/api/daily-watchlist/stock -H "Content-Type: application/json" -d '{\"stock_name\":\"南大光电\",\"watch_date\":\"2026-03-15\",\"reason\":\"突破前高\"}'
```

#### Remove Stock (by ID)
```bash
# First, search for stock ID
curl -s "http://localhost:8000/api/daily-watchlist/summary" | grep -A5 "南大光电"

# Then delete by ID
curl -X DELETE http://localhost:8000/api/daily-watchlist/stock \
  -H "Content-Type: application/json" \
  -d "{\"stock_ids\":[3]}"
```

**PowerShell**:
```powershell
# Search for stock
Invoke-RestMethod -Uri "http://localhost:8000/api/daily-watchlist/summary" | ConvertTo-Json

# Delete by ID
curl -X DELETE http://localhost:8000/api/daily-watchlist/stock -H "Content-Type: application/json" -d '{\"stock_ids\":[3]}'
```

### Step 3: Verify Operation

#### After Adding
```bash
# Search for the stock to verify it was added
curl -s "http://localhost:8000/api/daily-watchlist/summary" | grep "南大光电"
# Expected: Should find the stock
```

#### After Deleting
```bash
# Search for the stock to verify it was removed
curl -s "http://localhost:8000/api/daily-watchlist/summary" | grep "南大光电"
# Expected: Should NOT find the stock
```

### Step 4: Confirm Frontend Update
- WebSocket pushes update automatically
- Frontend displays new data
- No manual refresh needed (if frontend server restarted)

---

## Feature Overview

The Daily Watchlist helps you monitor short-term trading opportunities:

- **Date-based organization**: Stocks grouped by the date added
- **Rich metadata**: Track reason, target price, stop loss price, and notes
- **Archive support**: Hide entries without losing history
- **Real-time updates**: Changes sync automatically via WebSocket

---

## API Reference

All endpoints are prefixed with `/api/daily-watchlist`

### Core Endpoints

#### Get Watchlist Summary
```
GET /api/daily-watchlist/summary?include_archived=false&limit=30
```
Returns watchlist grouped by date, with most recent dates first.

**Response:**
```json
{
  "dates": [
    {
      "watch_date": "2026-03-12",
      "stocks": [
        {
          "id": 1,
          "stock_code": "601898",
          "stock_name": "中煤能源",
          "reason": "突破前高",
          "target_price": 15.5,
          "stop_loss_price": 13.0,
          "notes": "关注量能变化",
          "is_archived": false
        }
      ],
      "total_count": 1
    }
  ],
  "total_dates": 1,
  "total_stocks": 1
}
```

#### Add Stock to Watchlist
```
POST /api/daily-watchlist/stock
```

**Request Body:**
```json
{
  "stock_name": "中煤能源",           // Required
  "stock_code": "601898",             // Optional (auto-detected if omitted)
  "watch_date": "2026-03-12",         // Required
  "reason": "突破前高，量价配合",      // Optional
  "target_price": 15.50,              // Optional
  "stop_loss_price": 13.00,           // Optional
  "notes": "关注后续量能变化"          // Optional
}
```

**Response:** Returns the created stock entry with `id`, timestamps, etc.

#### Update Stock Entry
```
PUT /api/daily-watchlist/stock/{stock_id}
```

**Request Body:** Any fields you want to update (all optional):
```json
{
  "reason": "更新理由",
  "target_price": 16.00,
  "stop_loss_price": 13.50,
  "notes": "更新备注"
}
```

#### Delete Stocks
```
DELETE /api/daily-watchlist/stock
```

**Request Body:**
```json
{
  "stock_ids": [1, 2, 3]    // Delete specific stocks
  // OR
  "watch_date": "2026-03-12" // Delete all stocks on this date
}
```

#### Archive Stocks
```
POST /api/daily-watchlist/archive
```

Archived stocks are hidden by default but preserved for history.

**Request Body:**
```json
{
  "stock_ids": [1, 2, 3]    // Archive specific stocks
  // OR
  "watch_date": "2026-03-12" // Archive all stocks on this date
}
```

#### Unarchive Stocks
```
POST /api/daily-watchlist/unarchive
```

**Request Body:**
```json
{
  "stock_ids": [1, 2, 3]
}
```

### Utility Endpoints

#### Get All Dates
```
GET /api/daily-watchlist/dates?include_archived=false
```

Returns list of all dates that have watchlist entries.

#### Get Stocks by Date
```
GET /api/daily-watchlist/{watch_date}?include_archived=false
```

Returns all stocks for a specific date.

#### Get Single Stock
```
GET /api/daily-watchlist/stock/{stock_id}
```

Returns details of a specific stock entry.

---

## Frontend Integration

The daily watchlist is integrated into the **Holdings page** (lower section).

### Using the API Service

**Location:** `frontend/src/services/api.ts`

```typescript
import { dailyWatchlistApi } from '../services/api';

// Get summary
const summary = await dailyWatchlistApi.getSummary(false, 30);

// Add stock
const stock = await dailyWatchlistApi.addStock({
  stock_name: '中煤能源',
  watch_date: '2026-03-12',
  reason: '突破前高',
  target_price: 15.5
});

// Archive stocks
await dailyWatchlistApi.archiveStocks({ stock_ids: [1, 2, 3] });
```

### React Query Integration

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Fetch watchlist
const { data } = useQuery({
  queryKey: ['daily-watchlist', showArchived],
  queryFn: () => dailyWatchlistApi.getSummary(showArchived, 30)
});

// Add stock mutation
const mutation = useMutation({
  mutationFn: dailyWatchlistApi.addStock,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['daily-watchlist'] });
  }
});
```

---

## Usage Examples

### Example 1: Add a Stock for Today

```bash
curl -X POST http://localhost:8000/api/daily-watchlist/stock \
  -H "Content-Type: application/json" \
  -d '{
    "stock_name": "中煤能源",
    "watch_date": "2026-03-12",
    "reason": "突破前高，量价配合良好",
    "target_price": 15.50,
    "stop_loss_price": 13.00,
    "notes": "关注后续量能变化"
  }'
```

### Example 2: Get Today's Watchlist

```bash
curl http://localhost:8000/api/daily-watchlist/2026-03-12
```

### Example 3: Archive Multiple Stocks

```bash
curl -X POST http://localhost:8000/api/daily-watchlist/archive \
  -H "Content-Type: application/json" \
  -d '{"stock_ids": [1, 2, 3]}'
```

### Example 4: Show Archived Entries

```bash
curl "http://localhost:8000/api/daily-watchlist/summary?include_archived=true"
```

---

## Database Schema

**Table:** `daily_watchlist`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `stock_code` | VARCHAR(10) | Stock code (auto-detected if not provided) |
| `stock_name` | VARCHAR(50) | Stock name |
| `watch_date` | DATE | Date added to watchlist |
| `reason` | TEXT | Reason for watching |
| `target_price` | DECIMAL(10,2) | Target price |
| `stop_loss_price` | DECIMAL(10,2) | Stop loss price |
| `notes` | TEXT | Additional notes |
| `is_archived` | INTEGER | 0: active, 1: archived |
| `archived_at` | DATETIME | When archived |
| `created_at` | DATETIME | When created |
| `updated_at` | DATETIME | When last updated |

**Unique Constraint:** `(stock_code, watch_date)` - Prevents duplicate entries for the same stock on the same date.

---

## Implementation Files

For implementation details, refer to:

| Component | File Location |
|-----------|--------------|
| Database Model | `backend/database/models.py` → `DailyWatchlist` class |
| Service Layer | `backend/services/daily_watchlist_manager.py` |
| API Routes | `backend/routers/daily_watchlist.py` |
| Pydantic Models | `backend/models/daily_watchlist.py` |
| Frontend API | `frontend/src/services/api.ts` → `dailyWatchlistApi` |
| Frontend UI | `frontend/src/pages/Holdings.tsx` |

---

## Common Use Cases

### Use Case 1: Daily Morning Routine

1. Check yesterday's watchlist: `GET /api/daily-watchlist/{yesterday}`
2. Archive stocks that are no longer relevant
3. Add new stocks for today

### Use Case 2: Weekly Review

1. Get all archived entries: `GET /api/daily-watchlist/summary?include_archived=true&limit=30`
2. Review which stocks hit target/stop loss
3. Update notes with lessons learned

### Use Case 3: Quick Stock Lookup

1. Add stock to watchlist with reason
2. Set target and stop loss prices
3. Review weekly and update or archive

---

## Best Practices

1. **Always set a stop loss** - Protect your capital
2. **Update notes regularly** - Document what happened
3. **Archive completed trades** - Keep the active list clean
4. **Use meaningful reasons** - Help your future self understand why you added it
5. **Review weekly** - Archive old entries and learn from outcomes

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Stock code shows as "UNKNOWN" | Update `backend/data/stock_name_mapping.json` |
| Duplicate entry error | Use PUT to update instead of POST to create |
| Archived entries not showing | Pass `include_archived=true` query parameter |
| Frontend not updating | Check WebSocket connection, refresh the page |

---

## Related Documentation

- **Technical Decisions**: `.harness/decisions.md` (D012, D013, D014)
- **Project Progress**: `.harness/progress.md`
- **Architecture Guide**: `.harness/ARCHITECTURE.md`

---

**Version**: 2.0 (Simplified)  
**Last Updated**: 2026-03-12
