# 股票数据读取测试工具

## 功能说明

这是一个用于测试股票数据读取的工具，提供两种数据读取方式：

### 方式1：直接读取数据库（推荐）
- 不需要启动Server
- 直接从数据库读取数据
- 适合本地调试和数据查看

### 方式2：通过WebSocket连接
- 需要启动Backend服务器
- 测试实时行情推送功能
- 适合测试网络通信和WebSocket功能

## 特点

### 直接读取数据库模式
- ✅ 使用与Server端相同的服务类（`QuoteDataService`等）
- ✅ 使用与Server端相同的数据库连接方式（`async_session_maker`）
- ✅ 使用与Server端相同的数据模型（`StockRealtimeQuote`等）
- ✅ 完全复用Server端代码，确保一致性
- ✅ 无需启动Server

### WebSocket模式
- ✅ 测试实时行情推送功能
- ✅ 验证WebSocket连接和消息格式
- ✅ 支持单只/多只股票订阅
- ✅ 支持交互式测试

## 数据类型

支持以下数据类型的读取：

1. **实时行情** (`realtime_quote`)
   - 使用 `QuoteDataService.get_quote_from_db()`
   - 显示股票当前价格、涨跌幅、成交量等

2. **K线数据** (`kline`)
   - 支持日K、周K、月K
   - 显示最近100条K线数据

3. **每日报告** (`daily_report`)
   - 显示每日分析报告
   - 包含技术指标、基本面数据、评分等

4. **基本面指标** (`fundamental`)
   - PE、PB、PEG等估值指标
   - ROE、ROA等财务指标

5. **数据来源追踪** (`data_source`)
   - 显示数据读取记录
   - 追踪数据来源（db/cache/api）

## 使用方法

### 方法1：双击运行（推荐）

```
双击 run_test.bat
```

### 方法2：命令行运行

```bash
cd d:/2026projects/stocks-research/stock-peg/test/data-read
python read_stock_data.py
```

## 依赖要求

### 基础依赖（直接读取数据库）
```bash
pip install sqlalchemy aiosqlite
```

### WebSocket测试额外依赖
```bash
pip install websockets
```

## 界面操作

1. **选择股票**：从下拉列表选择股票代码
2. **选择数据类型**：选择要查看的数据类型
3. **加载数据**：点击"加载数据"按钮
4. **复制数据**：点击"复制到剪贴板"可复制JSON格式数据

## 技术架构

### 直接读取数据库模式

```
测试工具
  ├─ 导入server端模块
  │   ├─ database.session (数据库会话)
  │   ├─ services.quote_data_service (行情服务)
  │   ├─ services.stock_data_service (股票数据服务)
  │   └─ database.models (数据模型)
  │
  ├─ 使用异步数据库连接
  │   └─ async_session_maker (与server相同)
  │
  └─ 调用server端服务方法
      ├─ QuoteDataService.get_quote_from_db()
      ├─ StockKLineData查询
      ├─ DailyReport查询
      └─ FundamentalMetrics查询
```

### WebSocket模式

```
测试工具
  ├─ WebSocket客户端
  │   └─ websockets.connect("ws://localhost:8000/ws")
  │
  ├─ 消息格式
  │   ├─ 订阅: {"action": "subscribe", "stock_code": "xxx"}
  │   └─ 心跳: {"action": "ping"}
  │
  └─ 接收推送
      ├─ subscription: 订阅确认
      ├─ quote: 行情数据
      └─ pong: 心跳响应
```

## 数据库位置

数据库文件：`backend/data/stock_peg.db`

## 注意事项

1. 确保backend服务未运行时也能读取数据（数据库独立访问）
2. 所有异步操作通过 `asyncio.run()` 在GUI中执行
3. 数据库使用WAL模式，支持并发读取

## 故障排除

### 错误：找不到模块

确保在项目根目录运行，或检查 `sys.path` 设置。

### 错误：数据库锁定

确保没有其他进程正在写入数据库。

### 错误：WebSocket连接失败

确保Backend服务器正在运行：
```bash
# 检查服务器是否启动
curl http://localhost:8000/api/status

# 或在浏览器访问
http://localhost:8000/docs
```

### 错误：无数据显示

检查数据库中是否有数据：
```sql
-- 检查实时行情表
SELECT COUNT(*) FROM stock_realtime_quote;

-- 检查K线表
SELECT COUNT(*) FROM stock_kline_data;

-- 检查每日报告表
SELECT COUNT(*) FROM daily_reports;
```

### 错误：WebSocket不推送行情

1. 检查是否在交易时间（9:30-15:00）
2. 检查是否成功订阅股票
3. 检查服务器日志是否有错误

## 开发说明

本测试工具完全基于Serv