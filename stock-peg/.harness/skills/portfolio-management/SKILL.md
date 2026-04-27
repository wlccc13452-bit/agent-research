# Portfolio Management SKILL

> **Purpose**: Manage portfolio through SKILL commands - watchlist and holdings management

---

## Description

This SKILL provides a unified interface for managing:
1. **Daily Watchlist** (动态关注股票) - Short-term trading opportunities
2. **Holdings Sectors** (自持股票板块) - Long-term investment sectors
3. **Sector Stocks** (板块下的股票) - Stocks within each sector

**Key Features**:
- Natural language commands
- Automatic WebSocket push to frontend
- Real-time updates without page refresh

---

## Command Format

### 1. Daily Watchlist Commands

#### Add Stock to Watchlist
```
/daily-watchlist <股票名称> [日期] [理由]
```

**Examples**:
- `/daily-watchlist 南大光电` - Add to today's watchlist
- `/daily-watchlist 南大光电 2026-03-15` - Add to specific date
- `/daily-watchlist 南大光电 2026-03-15 突破前高,量价配合` - Add with reason

**Default**: If date is omitted, uses current date

#### Remove Stock from Watchlist
```
/daily-watchlist remove <股票ID或名称> [日期]
```

**Examples**:
- `/daily-watchlist remove 3` - Remove by ID
- `/daily-watchlist remove 南大光电` - Remove by name
- `/daily-watchlist remove 南大光电 2026-03-15` - Remove from specific date

**Execution Flow**:
1. **Search**: Server searches watchlist for matching stock (by ID or name)
2. **Delete**: Removes found stock(s) from database
3. **Update**: Broadcasts WebSocket update to all connected clients
4. **Auto-Refresh**: Frontend automatically refreshes watchlist display

**WebSocket Update Example**:
```json
{
  "type": "watchlist_updated",
  "message": "Deleted 1 watchlist stocks",
  "timestamp": "2026-03-15T18:30:00"
}
```

**Note**: When removing by name, ALL matching stocks will be deleted (e.g., if same stock appears on multiple dates)

#### Archive/Unarchive Watchlist
```
/daily-watchlist archive <股票ID或名称>
/daily-watchlist unarchive <股票ID或名称>
```

---

### 2. Holdings Sector Commands

#### Add Sector
```
/holdings add-sector <板块名称>
```

**Example**:
- `/holdings add-sector 新能源` - Create new sector "新能源"

#### Remove Sector
```
/holdings remove-sector <板块名称>
```

**Example**:
- `/holdings remove-sector 新能源` - Delete sector "新能源" and all its stocks

**Warning**: This will remove ALL stocks in the sector!

---

### 3. Holdings Stock Commands

#### Add Stock to Sector
```
/holdings add-stock <股票名称> <板块名称>
```

**Examples**:
- `/holdings add-stock 宁德时代 新能源` - Add stock to sector (auto-create if not exists)
- `/holdings add-stock 比亚迪 新能源` - Add another stock

**Auto-Create Feature**: If the sector doesn't exist, it will be automatically created!

#### Remove Stock from Sector
```
/holdings remove-stock <股票名称> [板块名称]
```

**Examples**:
- `/holdings remove-stock 宁德时代 新能源` - Remove from specific sector
- `/holdings remove-stock 宁德时代` - Remove from all sectors

#### Move Stock Between Sectors
```
/holdings move-stock <股票名称> <源板块> <目标板块>
```

**Example**:
- `/holdings move-stock 宁德时代 光伏 新能源` - Move from "光伏" to "新能源"

---

## Execution Steps

### Step 1: Parse Command
1. Extract command type (watchlist/holdings)
2. Extract action (add/remove/move)
3. Extract parameters (stock name, sector name, date, reason)

### Step 2: Validate Parameters
1. Check required parameters are present
2. Validate stock name exists in mapping
3. Validate sector exists (for stock operations)

### Step 3: Execute CLI Command (curl)

#### Daily Watchlist Operations

**View Watchlist**:
```bash
curl -s "http://localhost:8000/api/daily-watchlist/summary?include_archived=false&limit=30"
```

**Add Stock to Watchlist**:
```bash
curl -X POST http://localhost:8000/api/daily-watchlist/stock \
  -H "Content-Type: application/json" \
  -d "{\"stock_name\":\"南大光电\",\"watch_date\":\"2026-03-15\",\"reason\":\"突破前高\"}"
```

**Remove Stock from Watchlist**:
```bash
# Method 1: Delete by stock_ids
curl -X DELETE http://localhost:8000/api/daily-watchlist/stock \
  -H "Content-Type: application/json" \
  -d "{\"stock_ids\":[3]}"

# Method 2: Delete by watch_date (all stocks on that date)
curl -X DELETE http://localhost:8000/api/daily-watchlist/stock \
  -H "Content-Type: application/json" \
  -d "{\"watch_date\":\"2026-03-15\"}"
```

**PowerShell Alternative**:
```powershell
# Add stock
curl -X POST http://localhost:8000/api/daily-watchlist/stock -H "Content-Type: application/json" -d '{\"stock_name\":\"南大光电\",\"watch_date\":\"2026-03-15\"}'

# Delete stock
curl -X DELETE http://localhost:8000/api/daily-watchlist/stock -H "Content-Type: application/json" -d '{\"stock_ids\":[3]}'
```

#### Holdings Sector Operations

**View All Holdings**:
```bash
curl -s http://localhost:8000/api/holdings-management
```

**Add Sector**:
```bash
curl -X POST http://localhost:8000/api/holdings-management/sector \
  -H "Content-Type: application/json" \
  -d "{\"sector_name\":\"新能源\"}"
```

**Remove Sector**:
```bash
curl -X DELETE http://localhost:8000/api/holdings-management/sector \
  -H "Content-Type: application/json" \
  -d "{\"sector_name\":\"新能源\"}"
```

**PowerShell**:
```powershell
curl -X POST http://localhost:8000/api/holdings-management/sector -H "Content-Type: application/json" -d '{\"sector_name\":\"新能源\"}'
```

#### Holdings Stock Operations

**Add Stock to Sector**:
```bash
curl -X POST http://localhost:8000/api/holdings-management/stock \
  -H "Content-Type: application/json" \
  -d "{\"stock_name\":\"宁德时代\",\"sector_name\":\"新能源\"}"
```

**Remove Stock from Sector**:
```bash
curl -X DELETE http://localhost:8000/api/holdings-management/stock \
  -H "Content-Type: application/json" \
  -d "{\"stock_name\":\"宁德时代\",\"sector_name\":\"新能源\"}"
```

**Move Stock Between Sectors**:
```bash
curl -X POST http://localhost:8000/api/holdings-management/stock/move \
  -H "Content-Type: application/json" \
  -d "{\"stock_name\":\"宁德时代\",\"from_sector\":\"光伏\",\"to_sector\":\"新能源\"}"
```

**PowerShell**:
```powershell
curl -X POST http://localhost:8000/api/holdings-management/stock -H "Content-Type: application/json" -d '{\"stock_name\":\"宁德时代\",\"sector_name\":\"新能源\"}'
```

### Step 4: MANDATORY - Search and Verify
**CRITICAL**: After every operation (add/remove/move), MUST perform a search to verify:

**For Watchlist Operations**:
```bash
# After adding/deleting stock - search for it
curl -s "http://localhost:8000/api/daily-watchlist/summary" | grep -i "南大光电"

# If adding: Should find the stock name
# If deleting: Should NOT find the stock name (empty result)
```

**For Holdings Operations**:
```bash
# After adding/removing stock or sector - check holdings
curl -s http://localhost:8000/api/holdings-management | grep -A10 "新能源"

# If adding stock: Should see stock name in sector
# If removing stock: Should NOT see stock name in sector
# If adding sector: Should see sector name
# If removing sector: Should NOT see sector name
```

**PowerShell**:
```powershell
# View watchlist
Invoke-RestMethod -Uri "http://localhost:8000/api/daily-watchlist/summary" | Select-Object -ExpandProperty dates | ConvertTo-Json

# View holdings
Invoke-RestMethod -Uri "http://localhost:8000/api/holdings-management" | ConvertTo-Json
```

**VERIFICATION FAILURES**:
- If stock still exists after deletion → **ERROR**: Operation failed
- If stock doesn't exist after addition → **ERROR**: Operation failed
- If sector still exists after deletion → **ERROR**: Operation failed

**DO NOT SKIP THIS STEP!** Verification ensures:
1. Database operation actually succeeded
2. Frontend will receive correct data
3. No silent failures

### Step 5: Auto-Update Frontend
1. Backend broadcasts WebSocket update
2. Frontend automatically refreshes data
3. No manual page refresh needed
4. Verify frontend UI shows updated data

---

## API Endpoints

### Daily Watchlist
- `POST /api/daily-watchlist/stock` - Add stock
- `DELETE /api/daily-watchlist/stock` - Remove stock
- `PUT /api/daily-watchlist/stock/{id}` - Update stock
- `POST /api/daily-watchlist/archive` - Archive stock
- `POST /api/daily-watchlist/unarchive` - Unarchive stock
- `GET /api/daily-watchlist/summary` - Get watchlist summary

### Holdings Management
- `GET /api/holdings-management` - Get all holdings
- `POST /api/holdings-management/sector` - Add sector
- `DELETE /api/holdings-management/sector` - Remove sector
- `POST /api/holdings-management/stock` - Add stock to sector
- `DELETE /api/holdings-management/stock` - Remove stock from sector
- `POST /api/holdings-management/stock/move` - Move stock between sectors

---

## Workflow Integration

### Typical Usage Flow

1. **Morning Analysis**:
   ```
   /daily-watchlist 中际旭创 2026-03-15 突破前高
   /daily-watchlist 新易盛 2026-03-15 量价配合
   ```

2. **Weekly Review**:
   ```
   /holdings add-sector 科技
   /holdings add-stock 中际旭创 科技
   /holdings add-stock 新易盛 科技
   ```

3. **Portfolio Adjustment**:
   ```
   /holdings move-stock 隆基绿能 光伏 新能源
   /holdings remove-stock 雅化集团 锂
   ```

---

## Frontend Integration

### WebSocket Events

When operations complete, backend broadcasts:

**Watchlist Updates**:
```json
{
  "type": "watchlist_updated",
  "message": "Added stock 南大光电 to watchlist",
  "watch_date": "2026-03-15",
  "timestamp": "2026-03-15T08:30:00"
}
```

**Holdings Updates**:
```json
{
  "type": "holdings_updated",
  "update_type": "stock_added",
  "message": "Added stock 宁德时代 to sector 新能源",
  "timestamp": "2026-03-15T08:30:00"
}
```

### Frontend Auto-Refresh

Frontend should listen to WebSocket and auto-refresh:

```typescript
// In frontend
useEffect(() => {
  const handleWebSocketMessage = (event: MessageEvent) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'watchlist_updated') {
      // Auto-refresh watchlist
      queryClient.invalidateQueries({ queryKey: ['daily-watchlist'] });
    }
    
    if (data.type === 'holdings_updated') {
      // Auto-refresh holdings
      queryClient.invalidateQueries({ queryKey: ['holdings'] });
    }
  };
  
  // Subscribe to WebSocket
  websocket.addEventListener('message', handleWebSocketMessage);
  
  return () => {
    websocket.removeEventListener('message', handleWebSocketMessage);
  };
}, []);
```

---

## Prohibitions

1. ❌ **Do not** create temporary Python scripts for API calls - **MUST use curl or Invoke-RestMethod directly**
2. ❌ **Do not** create temporary test files - execute curl commands inline
3. ❌ **Do not** skip WebSocket integration test
4. ❌ **Do not** forget to update stock name mapping if stock code is UNKNOWN
5. ❌ **Do not** allow duplicate stocks in same sector/date

**Why use curl instead of Python scripts?**
- Faster execution (no file creation overhead)
- Easier to debug (see exact API calls)
- More portable (works in any shell)
- No cleanup needed

---

## Troubleshooting

### Stock Code Shows UNKNOWN

**Problem**: Stock name not in mapping file

**Solution**:
```bash
# Update mapping file
curl -X PUT http://localhost:8000/api/daily-watchlist/stock/{id} \
  -H "Content-Type: application/json" \
  -d '{"stock_code": "300346"}'
```

Or manually add to `backend/data/stock_name_mapping.json`:
```json
{
  "南大光电": "300346"
}
```

### Frontend Not Auto-Updating

**Check**:
1. WebSocket connection active?
2. Frontend listening to correct event types?
3. Query invalidation triggered?

### Sector Not Found

**Check**:
1. Sector name exact match (case-sensitive, no extra spaces)
2. Use `GET /api/holdings-management` to see all sectors

---

## Related Documentation

- **Daily Watchlist SKILL**: `.harness/skills/daily-watchlist/SKILL.md`
- **Backend Implementation**: `backend/services/holdings_manager.py`
- **API Routes**: `backend/routers/holdings.py`, `backend/routers/daily_watchlist.py`
- **Data Storage**: `backend/data/自持股票.md`, `backend/data/stock_peg.db`

---

## Version History

- **v1.0** (2026-03-15): Initial version with watchlist and holdings management
