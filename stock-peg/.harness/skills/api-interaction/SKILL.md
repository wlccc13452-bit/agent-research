# Stock PEG API Interaction / SKILL.md

## Skill Name
stock-peg-api-interaction

## Description
Interact with Stock PEG backend APIs and MCP Server tools for stock data analysis, quotes, klines, and market intelligence.

## Trigger Phrases
- "get stock quote for"
- "analyze stock"
- "check market sentiment"
- "get kline data"
- "call API"
- "/api"

## Mandatory Read Order
1. memory/core-facts.md
2. decisions.md
3. progress.md
4. AGENTS.md

---

## Step-by-Step Execution

### Phase 1: Verify Environment
1. Check backend server status: `curl http://localhost:8000/health` or `Invoke-RestMethod http://localhost:8000/health`
2. Confirm MCP server running if using MCP tools
3. Identify which API endpoint needed (see Reference below)

### Phase 2: Execute API Call
4. Use appropriate endpoint based on task:
   - **Quotes**: `/api/stock/quote/{code}`
   - **Klines**: `/api/stock/kline/{code}`
   - **Fundamentals**: `/api/fundamental/{code}`
   - **Indicators**: `/api/indicators/force-index/{code}`
   - **Market**: `/api/market/sentiment`

5. Format request with proper parameters
6. Handle response (success/error)
7. Log API call with trace_id

### Phase 3: Post-Processing
8. Parse and format data for user
9. Update session summary if significant findings
10. Cache frequently used data (avoid repeated calls)

---

## API Reference (MCP Server Tools)

### Stock Data
| Tool | Endpoint | Description |
|------|----------|-------------|
| `get_stock_quote` | `/api/stock/quote/{code}` | Real-time quote |
| `get_batch_quotes` | `/api/stock/quotes/batch` | Batch quotes |
| `get_stock_kline` | `/api/stock/kline/{code}` | K-line data |
| `get_technical_indicators` | `/api/indicators/{code}` | MA/RSI/MACD |

### Analysis
| Tool | Endpoint | Description |
|------|----------|-------------|
| `get_force_index` | `/api/indicators/force-index/{code}` | Force Index |
| `get_pmr` | `/api/indicators/pmr/{code}` | PMR indicator |
| `get_fundamental_analysis` | `/api/fundamental/{code}` | Financial analysis |
| `get_valuation_metrics` | `/api/valuation/{code}` | PEG/PE/PB |

### Market Data
| Tool | Endpoint | Description |
|------|----------|-------------|
| `get_market_sentiment` | `/api/market/sentiment` | Up/down/flat counts |
| `get_market_indices` | `/api/market/indices` | SSE/SZSE indices |
| `get_industry_sectors` | `/api/market/sectors/industry` | Industry list |
| `get_concept_sectors` | `/api/market/sectors/concept` | Concept list |
| `get_north_money_flow` | `/api/market/north-flow` | North-bound capital |

### Holdings
| Tool | Endpoint | Description |
|------|----------|-------------|
| `get_holdings` | `/api/holdings` | Current holdings list |

### US Market
| Tool | Endpoint | Description |
|------|----------|-------------|
| `get_us_market_indices` | `/api/us/indices` | S&P500/DJIA/NASDAQ |

### Macro
| Tool | Endpoint | Description |
|------|----------|-------------|
| `get_macro_cpi` | `/api/macro/cpi` | CPI data |
| `get_macro_gdp` | `/api/macro/gdp` | GDP data |
| `get_macro_pmi` | `/api/macro/pmi` | PMI data |

---

## PowerShell Examples

### Get Stock Quote
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/stock/quote/000001" -Method Get
```

### Get K-line Data
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/stock/kline/000001?period=day&limit=100" -Method Get
```

### Get Market Sentiment
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/market/sentiment" -Method Get
```

### Get Force Index
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/indicators/force-index/000001" -Method Get
```

---

## Prohibitions

### API Usage
- ❌ NEVER call API without checking server status first
- ❌ NEVER use hardcoded stock codes without validation
- ❌ NEVER exceed rate limits (max 100 requests/minute)

### Data Handling
- ❌ NEVER cache sensitive data in plain text
- ❌ NEVER expose API responses with internal errors to users
- ❌ NEVER log full response bodies (truncate to 500 chars)

### Error Handling
- ❌ NEVER ignore API errors
- ❌ NEVER retry failed requests more than 3 times
- ✅ ALWAYS provide fallback data source if primary fails

---

## Allowed Tools
- `execute_command` - Run curl/Invoke-RestMethod
- `read_file` - Read cached data
- `write_to_file` - Write test scripts
- `search_content` - Find API definitions

---

## Output Format

```
<thinking>
Checking API availability...
Identifying correct endpoint for [task]...
</thinking>

**Step 1:** Verify server status → Server running on port 8000

**Step 2:** Call API endpoint → `GET /api/stock/quote/000001`

**Step 3:** Parse response → 
- Stock: 平安银行 (000001)
- Price: ¥12.45 (+0.32%)
- Volume: 45,678,900

**Final:**
- ✅ API call successful
- ✅ Data formatted for user
- ✅ Response logged with trace_id
- Ready for next instruction
```

---

## Error Recovery

### Server Not Running
```powershell
# Start backend server
cd d:\2026projects\stocks-research\stock-peg\backend
python main.py
```

### Invalid Stock Code
- Search stock first: `/api/stock/search?keyword={name}`
- Use returned stock_code for subsequent calls

### Rate Limit Exceeded
- Wait 60 seconds
- Use cached data if available
- Batch requests to reduce call count

---

## Notes

- Backend default port: **8000**
- MCP Server default port: **8080**
- All APIs return JSON format
- Authentication required for write operations (future)
