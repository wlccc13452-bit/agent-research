# Stock PEG MCP Server - 使用说明

## 概述

Stock PEG MCP Server 是一个基于 Model Context Protocol (MCP) 的股票数据服务，允许 AI Agent 直接访问后端数据能力，无需通过 HTTP API 调用。

## 功能特性

### 1. 股票行情数据
- 实时行情查询（价格、涨跌幅、成交量等）
- 批量行情查询
- 市场指数查询（上证、深证、创业板等）

### 2. K线数据
- 日K线、周K线、月K线
- 分钟线数据（需要Tushare权限）
- 板块K线、指数K线

### 3. 技术指标
- MA均线（MA5/MA10/MA20/MA60）
- MACD指标（DIF/DEA/MACD柱）
- RSI指标（14日RSI）
- KDJ指标（K/D/J值）
- Force Index力量指数
- PMR动量比值

### 4. 基本面分析
- 估值指标（PE/PB/PS/PEG）
- 成长性指标（营收CAGR、利润CAGR、ROE/ROA）
- 财务健康度（资产负债率、流动比率、Z-Score）
- 综合评分与投资建议

### 5. 市场情绪
- 涨跌停统计
- 市场宽度（上涨/下跌比例）
- 北向资金流向

### 6. 板块数据
- 行业板块列表与表现
- 概念板块列表与表现
- 板块成分股查询

### 7. 资金流向
- 个股资金流向（主力/散户）
- 板块资金流向
- 市场整体资金流向

### 8. 美股数据
- 美股三大指数（标普/纳斯达克/道琼斯）
- 美股实时行情

### 9. 宏观经济数据
- CPI数据（最近12个月）
- GDP数据（最近8季度）
- PMI数据（最近12个月）

---

## 快速开始

### 前置要求
1. Python 3.13+
2. UV 包管理器
3. 后端服务运行在端口 8000

### 配置步骤

#### 1. 检查MCP配置文件
确保 `.codebuddy/mcp-config.json` 包含以下配置：

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

**注意**：请将路径 `d:\\2026projects\\stocks-research\\stock-peg\\backend` 替换为你的实际项目路径。

#### 2. 重启 CodeBuddy
修改 MCP 配置后，必须重启 CodeBuddy 以加载新的 MCP Server。

#### 3. 验证MCP Server加载
重启后，MCP工具应该可用。工具命名格式：
```
mcp__stock_peg_data__<tool_name>
```

---

## 使用示例

### 示例1：查询实时行情

**用户输入**：
```
查询平安银行的实时行情
```

**AI Agent 会使用 MCP 工具**：
```
mcp__stock_peg_data__get_stock_quote(stock_code="000001")
```

**返回结果**：
```json
{
  "stock_code": "000001",
  "stock_name": "平安银行",
  "price": 11.50,
  "change": 0.15,
  "change_pct": 1.32,
  "volume": 125634521,
  "amount": 1445000000,
  "high": 11.60,
  "low": 11.35,
  "open": 11.40,
  "prev_close": 11.35,
  "timestamp": "2026-03-15T10:30:00"
}
```

---

### 示例2：分析技术指标

**用户输入**：
```
分析贵州茅台的技术指标
```

**AI Agent 会使用 MCP 工具**：
```
mcp__stock_peg_data__get_technical_indicators(stock_code="600519")
```

**返回结果**：
```json
{
  "stock_code": "600519",
  "stock_name": "贵州茅台",
  "period": "day",
  "ma": {
    "ma5": 1650.20,
    "ma10": 1645.50,
    "ma20": 1638.80,
    "ma60": 1620.30
  },
  "macd": {
    "dif": 5.20,
    "dea": 3.80,
    "macd": 2.80
  },
  "rsi": {
    "rsi_14": 62.5
  },
  "kdj": {
    "k": 65.2,
    "d": 58.6,
    "j": 78.4
  }
}
```

---

### 示例3：综合分析股票

**用户输入**：
```
全面分析比亚迪
```

**AI Agent 会组合使用多个 MCP 工具**：
1. `get_stock_quote` - 获取实时行情
2. `get_technical_indicators` - 获取技术指标
3. `get_fundamental_analysis` - 获取基本面分析
4. `get_stock_fund_flow` - 获取资金流向

**AI Agent 综合分析报告**：
```
📊 比亚迪 (002594) 综合分析

【实时行情】
价格: ¥215.80 (+2.35%)
成交量: 156.2万手
成交额: 33.6亿

【技术指标】
MA: MA5(213.5) > MA10(210.2) > MA20(205.8) ✅ 多头排列
MACD: DIF(4.2) > DEA(2.8) ✅ 金叉
RSI: 68.5 (偏强)
KDJ: K(72) > D(65) ✅ 买入信号

【基本面】
PE_TTM: 28.5 (合理)
PB: 6.2
ROE: 18.5% (优秀)
综合评分: 82/100

【资金流向】
主力净流入: +5.8亿 ✅
散户净流出: -3.2亿

【建议】
技术面+基本面双重向好，主力资金大幅流入，建议关注。
```

---

## 可用工具列表

### 股票行情
- `get_stock_quote` - 获取实时行情
- `get_batch_quotes` - 批量获取行情
- `get_market_indices` - 获取市场指数

### K线数据
- `get_stock_kline` - 获取K线数据

### 技术指标
- `get_technical_indicators` - 技术指标（MA/MACD/RSI/KDJ）
- `get_force_index` - Force Index力量指数
- `get_pmr` - PMR动量比值

### 基本面分析
- `get_fundamental_analysis` - 综合基本面分析
- `get_valuation_metrics` - 估值指标

### 市场情绪
- `get_market_sentiment` - 市场情绪数据

### 板块数据
- `get_industry_sectors` - 行业板块列表
- `get_concept_sectors` - 概念板块列表

### 资金流向
- `get_stock_fund_flow` - 个股资金流向
- `get_north_money_flow` - 北向资金流向

### 持仓管理
- `get_holdings` - 获取持仓列表

### 美股数据
- `get_us_market_indices` - 美股指数

### 宏观经济
- `get_macro_cpi` - CPI数据
- `get_macro_gdp` - GDP数据
- `get_macro_pmi` - PMI数据

---

## 故障排查

### 问题1：MCP工具不可用

**可能原因**：
1. MCP配置文件路径错误
2. CodeBuddy未重启
3. 后端服务未运行

**解决方案**：
1. 检查 `.codebuddy/mcp-config.json` 中的路径是否正确
2. 重启 CodeBuddy
3. 确认后端服务运行在端口 8000

---

### 问题2：工具返回错误

**可能原因**：
1. 股票代码格式错误
2. 市场休市
3. 网络连接问题

**解决方案**：
1. 确认股票代码为6位数字（如 "000001"）
2. 检查是否为交易时间
3. 检查网络连接和后端日志

---

### 问题3：数据不是最新的

**可能原因**：
1. 数据缓存（1分钟有效期）
2. 市场休市
3. 数据源更新延迟

**解决方案**：
1. 等待1分钟后重试
2. 确认市场是否开市
3. 重启后端服务强制刷新

---

## 高级用法

### 组合多个工具
AI Agent 可以智能组合多个工具来完成复杂任务：

```
用户：对比分析平安银行和招商银行

AI Agent 执行流程：
1. [get_stock_quote("000001")] - 平安银行行情
2. [get_stock_quote("600036")] - 招商银行行情
3. [get_technical_indicators("000001")] - 平安银行技术指标
4. [get_technical_indicators("600036")] - 招商银行技术指标
5. [get_fundamental_analysis("000001")] - 平安银行基本面
6. [get_fundamental_analysis("600036")] - 招商银行基本面
7. [综合对比分析并生成报告]
```

### 自定义分析模板
用户可以要求特定的分析模板：

```
用户：分析贵州茅台，重点关注估值和资金流向

AI Agent 会优先调用：
- get_valuation_metrics("600519")
- get_stock_fund_flow("600519")
```

---

## 最佳实践

1. **明确股票代码**：优先使用6位数字代码，而非股票名称
2. **组合分析**：建议组合多个工具进行综合分析
3. **时间考虑**：注意市场交易时间，非交易时间数据可能不是最新的
4. **错误处理**：遇到错误时，查看错误信息并按建议操作
5. **定期刷新**：长时间未使用时，建议重启后端服务刷新数据

---

## 技术架构

```
用户请求
    ↓
AI Agent (CodeBuddy)
    ↓
MCP Tool Call (mcp__stock_peg_data__*)
    ↓
Stock PEG MCP Server (FastMCP)
    ↓
Backend Services (stock_service, akshare_service, etc.)
    ↓
Data Sources (Tushare, Akshare, Tencent API, Database)
    ↓
返回数据给 AI Agent
    ↓
AI Agent 分析并呈现给用户
```

---

## 相关文档

- **SKILL文档**：`.harness/skills/utils/stock-data-mcp/SKILL.md`
- **MCP Server实现**：`backend/mcp_server/server.py`
- **MCP配置**：`.codebuddy/mcp-config.json`
- **后端服务**：`backend/services/*.py`

---

## 版本信息

- **版本**：1.0
- **发布日期**：2026-03-15
- **兼容性**：CodeBuddy, FastMCP 2.13.3+

---

## 支持与反馈

如有问题或建议，请：
1. 查看本文档的故障排查部分
2. 检查后端日志：`backend/logs/`
3. 查看 SKILL 文档：`.harness/skills/utils/stock-data-mcp/SKILL.md`
