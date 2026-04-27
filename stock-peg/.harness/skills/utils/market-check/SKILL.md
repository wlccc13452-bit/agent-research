# SKILL.md - Chinese Stock Market Check

> **Purpose**: Query and display Chinese stock market major indices performance in real-time.

---

## Description

This skill provides functionality to check Chinese stock market performance, including major indices (上证指数, 深证成指, 创业板指, 科创50, 北证50), their price movements, trading volume, and market sentiment analysis.

---

## Mandatory Read Order

Before using this skill, read in this exact order:
1. `memory/core-facts.md` → Understand environment constraints and temporary files location
2. This SKILL file → Understand execution steps

---

## Step-by-Step Execution

### Prerequisites
- Python 3.13+ with UV package manager
- Backend virtual environment activated or UV available
- Network connection to access Akshare API

### Step 1: Navigate to Test Directory
```bash
cd d:/play-ground/股票研究/stock-peg/test/temp/market-check
```

### Step 2: Run Market Check Script
```bash
# Using UV (recommended)
cd d:/play-ground/股票研究/stock-peg/backend
uv run python ../test/temp/market-check/check_market.py

# Or if virtual environment is active
python d:/play-ground/股票研究/stock-peg/test/temp/market-check/check_market.py
```

### Step 3: Read Output
The script will display:
- Current timestamp
- Major indices with price, change percentage, and change amount
- Trading volume and amount
- Market sentiment (强势上涨/小幅上涨/小幅下跌/弱势下跌)
- Average change across all indices

### Expected Output Format
```
============================================================
中国股市行情 - 2026-03-13 11:04:14
============================================================

主要指数表现：

📈 上证指数   4117.57   +0.46%  (+18.92)
   成交量: 32.50亿股  成交额: 4521.30亿元

📉 深证成指  14300.92   -0.51%  (-73.25)
   成交量: 45.20亿股  成交额: 6892.40亿元

...

------------------------------------------------------------
市场整体: 小幅上涨 📈
平均涨跌: +0.12%
============================================================
```

---

## Prohibitions

1. ❌ Do NOT create market check scripts in `backend/` directory
2. ❌ Do NOT create market check scripts in project root
3. ❌ Do NOT skip reading `.harness/memory/core-facts.md` before execution
4. ❌ Do NOT run without checking network connectivity first

---

## Allowed Tools

| Tool | Purpose |
|------|---------|
| `execute_command` | Run Python script via UV |
| `read_file` | Read check_market.py source code |
| `write_to_file` | Create or update check_market.py in `test/temp/market-check/` |
| `web_search` | Alternative method if Akshare API fails |

---

## Troubleshooting

### Issue: Proxy Connection Error
**Symptom**: `ProxyError: Unable to connect to proxy`

**Solution**:
1. Check network connection
2. Try using `web_search` as alternative data source
3. Check if backend service has cached market data

### Issue: Module Not Found
**Symptom**: `ModuleNotFoundError: No module named 'akshare'`

**Solution**:
```bash
cd d:/play-ground/股票研究/stock-peg/backend
uv add akshare
uv sync
```

### Issue: Data Not Available
**Symptom**: Empty DataFrame or API timeout

**Solution**:
- Market may be closed (trading hours: 9:30-11:30, 13:00-15:00 Beijing time)
- Use web search to get market data from news sources

---

## Alternative Methods

### Method 1: Web Search (Fallback)
```bash
# If Akshare fails, use web search
web_search("中国股市 上证指数 深证成指 创业板指 今日行情")
```

### Method 2: Backend API (If Service Running)
```bash
# If backend service is running on port 8000
curl http://localhost:8000/api/market/indices
```

---

## Output Format

**Success**: Returns formatted Chinese text showing:
- Timestamp
- Index names and codes
- Current prices with change indicators (📈/📉/➡️)
- Percentage changes and absolute changes
- Trading volume (billion shares) and amount (billion yuan)
- Market sentiment summary

**Failure**: Returns error message with:
- Error type (ProxyError, NetworkError, etc.)
- Suggested solution
- Alternative methods

---

## Related Files

- **Script Location**: `test/temp/market-check/check_market.py`
- **Data Source**: Akshare (东方财富网 API)
- **Related Skills**: `skills/indicators/force-index/SKILL.md`

---

## Version

- **Created**: 2026-03-13
- **Last Updated**: 2026-03-13
- **Version**: 1.0
