# Stock Data MCP Server SKILL

## Description

Access Stock PEG platform data via MCP (Model Context Protocol) tools. This enables AI Agents to directly query stock quotes, K-line data, technical indicators, fundamental analysis, market sentiment, and more without making HTTP API calls.

## Mandatory Read Order

1. This SKILL document
2. `backend/mcp_server/server.py` - MCP server implementation
3. `.codebuddy/mcp-config.json` - MCP configuration

## Available MCP Tools

### 1. Stock Quote Tools

#### `get_stock_quote`
Get real-time stock quote (实时行情)

**Parameters**:
- `stock_code` (string): Stock code (e.g., "000001", "600519")

**Returns**:
- Price, change, change percentage, volume, amount, high, low, open, prev_close, timestamp

**Example**:
```
User: "查询平安银行的实时行情"
Agent: [Uses get_stock_quote tool with stock_code="000001"]
Result: 
{
  "stock_code": "000001",
  "stock_name": "平安银行",
  "price": 11.50,
  "change": 0.15,
  "change_pct": 1.32,
  "volume": 125634521,
  ...
}
```

#### `get_batch_quotes`
Get real-time quotes for multiple stocks (批量行情)

**Parameters**:
- `stock_codes` (list): List of stock codes

**Returns**:
- Dictionary mapping stock codes to quote data

**Example**:
```
User: "查询平安银行、招商银行、贵州茅台的实时行情"
Agent: [Uses get_batch_quotes tool with stock_codes=["000001", "600036", "600519"]]
```

---

### 2. K-Line Data Tools

#### `get_stock_kline`
Get K-line (candlestick) data for a stock (K线数据)

**Parameters**:
- `stock_code` (string): Stock code
- `period` (string, optional): K-line period - "day", "week", "month", "m1", "m5", "m15", "m30", "m60" (default: "day")
- `start_date` (string, optional): Start date (YYYY-MM-DD)
- `end_date` (string, optional): End date (YYYY-MM-DD)
- `limit` (int, optional): Number of records (default: 100)

**Returns**:
- K-line data with OHLCV values

**Example**:
```
User: "获取比亚迪最近100天的日K线数据"
Agent: [Uses get_stock_kline with stock_code="002594", period="day", limit=100]
```

---

### 3. Technical Indicators Tools

#### `get_technical_indicators`
Get technical indicators (技术指标: MA/MACD/RSI/KDJ)

**Parameters**:
- `stock_code` (string): Stock code
- `period` (string, optional): K-line period - "day", "week", "month" (default: "day")

**Returns**:
- MA (MA5/MA10/MA20/MA60)
- MACD (DIF/DEA/MACD柱)
- RSI (14日RSI)
- KDJ (K/D/J值)

**Example**:
```
User: "分析贵州茅台的技术指标"
Agent: [Uses get_technical_indicators with stock_code="600519"]
```

#### `get_force_index`
Get Force Index indicator (力量指数)

**Parameters**:
- `stock_code` (string): Stock code
- `period` (int, optional): Force Index period (default: 13)

**Returns**:
- Force Index values, signal (buy/sell/hold), strength, trend, recommendation

**Example**:
```
User: "查看比亚迪的Force Index指标"
Agent: [Uses get_force_index with stock_code="002594"]
```

#### `get_pmr`
Get PMR (Price Momentum Ratio) indicator (价格动量比值)

**Parameters**:
- `stock_code` (string): Stock code

**Returns**:
- PMR values across multiple timeframes (PMR_5/10/20/60), signal, trend

**Example**:
```
User: "获取招商银行的PMR指标"
Agent: [Uses get_pmr with stock_code="600036"]
```

---

### 4. Fundamental Analysis Tools

#### `get_fundamental_analysis`
Get comprehensive fundamental analysis (基本面综合分析)

**Parameters**:
- `stock_code` (string): Stock code

**Returns**:
- Valuation metrics (PE/PB/PS/PEG)
- Growth metrics (营收/利润CAGR, ROE/ROA)
- Financial health (资产负债率, 流动比率, Z-Score)
- Overall score, rating, recommendation

**Example**:
```
User: "分析平安银行的基本面"
Agent: [Uses get_fundamental_analysis with stock_code="000001"]
```

#### `get_valuation_metrics`
Get valuation metrics (估值指标: PE/PB/PS/PEG)

**Parameters**:
- `stock_code` (string): Stock code

**Returns**:
- PE_TTM, PB, PS, PEG, market_cap

**Example**:
```
User: "查看贵州茅台的估值指标"
Agent: [Uses get_valuation_metrics with stock_code="600519"]
```

---

### 5. Market Sentiment Tools

#### `get_market_sentiment`
Get market sentiment data (市场情绪: 涨跌停/市场宽度)

**Parameters**: None

**Returns**:
- up_count, down_count, flat_count
- limit_up_count, limit_down_count
- market_breadth, total_count

**Example**:
```
User: "今天市场情绪如何?"
Agent: [Uses get_market_sentiment]
Result: 
{
  "up_count": 2156,
  "down_count": 2843,
  "limit_up_count": 45,
  "limit_down_count": 12,
  "market_breadth": 43.1,
  ...
}
```

#### `get_market_indices`
Get major market indices (主要指数)

**Parameters**: None

**Returns**:
- Shanghai Index, Shenzhen Index, ChiNext, STAR 50, etc.

**Example**:
```
User: "查询主要指数情况"
Agent: [Uses get_market_indices]
```

---

### 6. Sector Data Tools

#### `get_industry_sectors`
Get industry sector list (行业板块列表)

**Parameters**: None

**Returns**:
- List of industry sectors with performance data

**Example**:
```
User: "哪些行业板块表现最好?"
Agent: [Uses get_industry_sectors, then analyze top performers]
```

#### `get_concept_sectors`
Get concept sector list (概念板块列表)

**Parameters**: None

**Returns**:
- List of concept sectors with performance data

**Example**:
```
User: "今天哪些概念板块在涨?"
Agent: [Uses get_concept_sectors, then filter positive performers]
```

---

### 7. Fund Flow Tools

#### `get_stock_fund_flow`
Get fund flow data for a stock (个股资金流向)

**Parameters**:
- `stock_code` (string): Stock code

**Returns**:
- main_net_inflow, retail_net_inflow, super/big/medium/small net inflow

**Example**:
```
User: "比亚迪今天资金流向如何?"
Agent: [Uses get_stock_fund_flow with stock_code="002594"]
```

#### `get_north_money_flow`
Get northbound money flow data (北向资金流向)

**Parameters**: None

**Returns**:
- Northbound capital flow data

**Example**:
```
User: "北向资金今天流入多少?"
Agent: [Uses get_north_money_flow]
```

---

### 8. Holdings Management Tools

#### `get_holdings`
Get current holdings list (获取持仓列表)

**Parameters**: None

**Returns**:
- Holdings data with sectors and stocks

**Example**:
```
User: "我目前持有哪些股票?"
Agent: [Uses get_holdings]
```

---

### 9. US Market Tools

#### `get_us_market_indices`
Get US market indices (美股指数)

**Parameters**: None

**Returns**:
- S&P 500, NASDAQ, Dow Jones, etc.

**Example**:
```
User: "美股三大指数情况如何?"
Agent: [Uses get_us_market_indices]
```

---

### 10. Macro Economic Tools

#### `get_macro_cpi`
Get China CPI data (中国CPI数据)

**Parameters**: None

**Returns**:
- CPI data for the last 12 months

**Example**:
```
User: "最近CPI数据如何?"
Agent: [Uses get_macro_cpi]
```

#### `get_macro_gdp`
Get China GDP data (中国GDP数据)

**Parameters**: None

**Returns**:
- GDP data for the last 8 quarters

**Example**:
```
User: "查看中国GDP数据"
Agent: [Uses get_macro_gdp]
```

#### `get_macro_pmi`
Get China PMI data (中国PMI数据)

**Parameters**: None

**Returns**:
- PMI data for the last 12 months

**Example**:
```
User: "最近PMI数据如何?"
Agent: [Uses get_macro_pmi]
```

---

## Step-by-Step Execution

### Step 1: Verify MCP Server Configuration
Check that MCP server is registered in `.codebuddy/mcp-config.json`:
```json
{
  "mcpServers": {
    "stock-peg-data": {
      "command": "uv",
      "args": [
        "--directory",
        "d:\\2026projects\\stocks-research\\stock-peg\\backend",
        "run",
        "python",
        "run_mcp_server.py"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

### Step 2: Restart CodeBuddy
After modifying MCP config, restart CodeBuddy to load the new MCP server.

### Step 3: Test MCP Tools
Use any MCP tool in conversation:
```
User: "查询平安银行的实时行情"
Agent: [Uses mcp__stock_peg_data__get_stock_quote tool]
```

Tool naming convention: `mcp__<server_name>__<tool_name>`
Example: `mcp__stock_peg_data__get_stock_quote`

### Step 4: Combine Multiple Tools
Chain multiple MCP tools for comprehensive analysis:
```
User: "全面分析平安银行"
Agent: 
1. [Uses get_stock_quote] - Get real-time quote
2. [Uses get_technical_indicators] - Get technical indicators
3. [Uses get_fundamental_analysis] - Get fundamental analysis
4. [Uses get_stock_fund_flow] - Get fund flow data
5. [Synthesize all data into comprehensive analysis report]
```

---

## Prohibitions

1. ❌ Do NOT modify `mcp-config.json` paths manually - use absolute paths only
2. ❌ Do NOT create duplicate MCP tools with same names
3. ❌ Do NOT expose sensitive data (API keys, passwords) via MCP tools
4. ❌ Do NOT use MCP tools for operations that should go through API (e.g., data modification)
5. ❌ Do NOT bypass error handling - always check for `error` field in responses

---

## Allowed Tools

This SKILL allows using:
- ✅ All MCP tools defined in `backend/mcp_server/server.py`
- ✅ `read_file` - Read MCP server code for debugging
- ✅ `execute_command` - Test MCP server manually

---

## Output Format

When using MCP tools, format the output as follows:

### Success Case
```
📊 **Stock Analysis for 平安银行 (000001)**

**实时行情**:
- 价格: ¥11.50 (+1.32%)
- 成交量: 125.63万手
- 成交额: 14.5亿

**技术指标**:
- MA: MA5(11.45) > MA10(11.30) > MA20(11.10) ✅ 多头排列
- MACD: DIF(0.12) > DEA(0.08) ✅ 金叉
- RSI: 62.5 (偏强)
- KDJ: K(65) > D(58) ✅ 买入信号

**基本面**:
- PE_TTM: 5.8 (低估)
- PB: 0.65 (破净)
- ROE: 11.2%
- 综合评分: 78/100

**资金流向**:
- 主力净流入: +2.3亿 ✅
- 散户净流出: -1.8亿

**建议**: 技术面+基本面双重向好,主力资金流入,建议关注
```

### Error Case
```
❌ **Error**: No quote data found for 999999

Possible reasons:
1. Invalid stock code
2. Market closed
3. Network error

Please verify:
- Stock code format (6 digits)
- Market is open (trading hours)
- Backend server is running
```

---

## Troubleshooting

### Issue: MCP tools not available
**Cause**: MCP server not loaded
**Solution**: 
1. Check `.codebuddy/mcp-config.json` has correct paths
2. Restart CodeBuddy
3. Check backend server is running on port 8000

### Issue: Tool returns error
**Cause**: Backend service error or invalid parameters
**Solution**:
1. Check error message for details
2. Verify parameter format (stock code should be 6 digits)
3. Check backend logs: `backend/logs/`

### Issue: Data not up-to-date
**Cause**: Cache or market closed
**Solution**:
1. Market data is cached for 1 minute
2. Check if market is open (trading hours)
3. Force refresh by restarting backend server

---

## Related Files

- **MCP Server Implementation**: `backend/mcp_server/server.py`
- **MCP Configuration**: `.codebuddy/mcp-config.json`
- **Backend Services**: `backend/services/*.py`
- **API Routes**: `backend/routers/*.py`

---

## Version

- **Last Updated**: 2026-03-15
- **Version**: 1.0
- **Author**: Stock PEG Team
