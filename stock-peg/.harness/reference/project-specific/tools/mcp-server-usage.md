# Stock PEG MCP Server Usage Guide

## Overview

The Stock PEG project exposes a FastMCP-based MCP Server that provides 19 tools for AI agents to access stock data directly.

## Server Location

- **Module**: `backend/mcp_server/server.py`
- **Default Port**: 8080
- **Protocol**: MCP (Model Context Protocol)

## Available Tools (19 Total)

### Stock Data Tools (4)
| Tool | Description | Parameters |
|------|-------------|------------|
| `get_stock_quote` | Real-time quote | `stock_code: str` |
| `get_batch_quotes` | Batch quotes | `stock_codes: List[str]` |
| `get_stock_kline` | K-line data | `stock_code, period, start_date, end_date, limit` |
| `get_technical_indicators` | MA/RSI/MACD | `stock_code, period` |

### Analysis Tools (4)
| Tool | Description | Parameters |
|------|-------------|------------|
| `get_force_index` | Force Index indicator | `stock_code, period` |
| `get_pmr` | PMR indicator | `stock_code` |
| `get_fundamental_analysis` | Financial analysis | `stock_code` |
| `get_valuation_metrics` | PEG/PE/PB | `stock_code` |

### Market Data Tools (6)
| Tool | Description | Parameters |
|------|-------------|------------|
| `get_market_sentiment` | Up/down/flat counts | None |
| `get_market_indices` | SSE/SZSE indices | None |
| `get_industry_sectors` | Industry list | None |
| `get_concept_sectors` | Concept list | None |
| `get_stock_fund_flow` | Individual fund flow | `stock_code` |
| `get_north_money_flow` | North-bound capital | None |

### Holdings & US Market (2)
| Tool | Description | Parameters |
|------|-------------|------------|
| `get_holdings` | Current holdings | None |
| `get_us_market_indices` | S&P500/DJIA/NASDAQ | None |

### Macro Data (3)
| Tool | Description | Parameters |
|------|-------------|------------|
| `get_macro_cpi` | CPI data | None |
| `get_macro_gdp` | GDP data | None |
| `get_macro_pmi` | PMI data | None |

## Usage Examples

### PowerShell
```powershell
# Get stock quote
Invoke-RestMethod -Uri "http://localhost:8000/api/stock/quote/000001" -Method Get

# Get K-line data
Invoke-RestMethod -Uri "http://localhost:8000/api/stock/kline/000001?period=day&limit=100" -Method Get

# Get market sentiment
Invoke-RestMethod -Uri "http://localhost:8000/api/market/sentiment" -Method Get
```

### Python
```python
import httpx

async def get_quote(stock_code: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://localhost:8000/api/stock/quote/{stock_code}")
        return response.json()
```

## Starting the Server

```bash
# Start backend server (includes MCP)
cd backend
python main.py

# Or start MCP server separately
cd backend/mcp_server
python server.py
```

## API Endpoints

The MCP tools are also available via HTTP API at `/api/*` endpoints:

- `/api/stock/quote/{code}` - Stock quotes
- `/api/stock/kline/{code}` - K-line data
- `/api/indicators/force-index/{code}` - Force Index
- `/api/market/sentiment` - Market sentiment
- `/api/holdings` - Holdings list

## Integration with AI Agents

The MCP Server can be connected to AI agents that support the MCP protocol:

```json
{
  "mcpServers": {
    "stock-peg": {
      "command": "python",
      "args": ["backend/mcp_server/server.py"]
    }
  }
}
```

## Error Handling

All tools return error messages in this format:
```json
{
  "error": "Error description here"
}
```

## Rate Limiting

- Default: 100 requests/minute per endpoint
- Use batch endpoints when possible (`get_batch_quotes`)
- Cache frequently accessed data

## Related Files

- MCP Server Implementation: `backend/mcp_server/server.py`
- SKILL for API Interaction: `.harness/skills/api-interaction/SKILL.md`
- Architecture Docs: `.harness/ARCHITECTURE.md`
- Backend Docs: `.harness/BACKEND.md`
