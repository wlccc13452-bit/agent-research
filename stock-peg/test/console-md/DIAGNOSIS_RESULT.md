# 数据获取问题诊断结果

**诊断时间**: 2026-03-09 19:50  
**诊断工具**: diagnose_data_issue.py

---

## 📋 问题清单

### ❌ 问题1: 美股数据查询失败 - 列名错误

**问题描述**:
数据库表 `us_daily_data` 的股票代码列名是 `us_stock_code`，但代码中使用了 `symbol`

**影响**:
- 无法查询美股指数数据
- 导致前端headbar无法显示美股指数

**数据库现状**:
```
✓ ^DJI (道琼斯): 2026-03-09, 47501.55点, -0.95%
✓ ^GSPC (标普500): 2026-03-09, 6740.02点, -1.33%
✓ ^IXIC (纳斯达克): 2026-03-09, 22387.68点, -1.59%
✓ ^VIX (恐慌指数): 2026-03-08, 15点, -2%  ⚠️ 数据较旧
```

**修复位置**:
- `backend/services/us_market_analyzer.py` 
- `backend/routers/us_market.py`

**修复方法**:
将所有SQL查询中的 `symbol` 替换为 `us_stock_code`

---

### ❌ 问题2: A股指数获取失败 - 代码格式不兼容

**问题描述**:
- 前端传递格式: `000001.SH`, `399001.SZ`
- 腾讯API不支持此格式 → 返回501错误
- Akshare需要格式: `sh000001` 或纯代码 `000001`

**影响**:
- headbar上的A股指数无法获取
- 腾讯API连续失败触发熔断

**失败的指数**:
- 000001.SH (上证指数)
- 399001.SZ (深证成指)
- 000016.SH (上证50)
- 399006.SZ (创业板指)
- 000905.SH (中证500)

**修复位置**:
- `backend/routers/stock.py`
- `backend/services/akshare_service.py`
- `backend/services/tencent_service.py`

**修复方法**:
添加代码格式转换函数，将 `000001.SH` 转换为各数据源需要的格式

---

### ⚠️ 问题3: VIX指数数据更新不及时

**问题描述**:
数据库中VIX数据日期是 2026-03-08，其他指数是 2026-03-09

**可能原因**:
- VIX数据源获取失败（从console.md日志可见）
- 后台更新任务未成功获取最新数据

**数据源失败记录**:
```
18:51:29 - Eastmoney 返回数据无 data 字段
18:51:31 - Alpha Vantage 返回数据格式异常
18:51:41 - Finnhub 返回数据为空
18:51:42 - Yahoo Finance 证书错误
```

**修复建议**:
- 优先使用东方财富API获取VIX
- 或使用CBOE官方API

---

## ✅ 数据源状态

| 数据源 | 配置状态 | 可用性 | 备注 |
|--------|---------|--------|------|
| Tushare | ✓ 已配置 | ✓ 可用 | 部分接口权限不足 |
| Akshare | ✓ 可用 | ✓ 可用 | 需正确处理代码格式 |
| 腾讯API | ✓ 已配置 | ✗ 熔断 | 代码格式不兼容 |
| 东方财富 | - | ✓ 可用 | 支持美股指数 |
| Alpha Vantage | ✓ 已配置 | ⚠ 异常 | 返回数据格式问题 |
| Finnhub | ✓ 已配置 | ✓ 可用 | 美股数据可用 |

---

## 🔧 修复方案

### 方案1: 修复美股数据查询（优先级: 最高）

**步骤**:
1. 在 `backend/services/us_market_analyzer.py` 中搜索 `symbol`
2. 替换为 `us_stock_code`
3. 重点修改以下方法:
   - `get_us_data_from_db()`
   - `get_us_stock_data()`

**示例**:
```python
# 错误 ❌
result = await session.execute(
    "SELECT * FROM us_daily_data WHERE symbol = :symbol"
)

# 正确 ✓
result = await session.execute(
    "SELECT * FROM us_daily_data WHERE us_stock_code = :symbol"
)
```

---

### 方案2: 修复A股指数代码格式（优先级: 最高）

**步骤**:
1. 创建代码格式转换工具函数
2. 在指数获取接口中调用转换函数
3. 为不同数据源提供正确的代码格式

**代码示例**:
```python
def normalize_index_code(code: str) -> dict:
    """
    将各种格式的指数代码标准化
    
    输入: "000001.SH", "sh000001", "000001"
    输出: {
        'pure_code': '000001',
        'market': 'sh',
        'akshare_code': 'sh000001'
    }
    """
    if '.' in code:
        pure_code, suffix = code.split('.')
        market = suffix.lower()
    elif code.startswith(('sh', 'sz')):
        market = code[:2]
        pure_code = code[2:]
    else:
        pure_code = code
        market = 'sh' if code.startswith(('0', '5', '6')) else 'sz'
    
    return {
        'pure_code': pure_code,
        'market': market,
        'akshare_code': f"{market}{pure_code}"
    }
```

---

### 方案3: 优化VIX数据获取（优先级: 高）

**步骤**:
1. 优先使用东方财富API
2. 备用Yahoo Finance（需修复证书问题）
3. 或使用CBOE官方API

**东方财富VIX API**:
```python
# VIX在东方财富的secid是 100.VIX
url = "https://push2.eastmoney.com/api/qt/ulist.np/get"
params = {
    "secids": "100.VIX",
    "fields": "f2,f3,f4,f5,f6,f12,f14,f15,f16,f17,f18"
}
```

---

## 📝 需要修改的文件

### 必须修改（问题1和2）
1. `backend/services/us_market_analyzer.py`
   - 所有使用 `symbol` 的SQL查询

2. `backend/routers/stock.py` 或 `backend/services/index_service.py`
   - A股指数获取接口
   - 添加代码格式转换

3. `backend/services/akshare_service.py`
   - `get_kline()` 方法
   - 处理指数代码格式

### 建议优化（问题3）
1. `backend/services/us_market_analyzer.py`
   - `_get_from_eastmoney()` 方法
   - 优化VIX数据获取

2. `backend/services/background_updater.py`
   - 美股指数更新任务
   - 添加失败重试逻辑

---

## 🧪 测试验证

修复完成后执行以下测试：

```bash
# 1. 测试美股指数（验证列名修复）
curl http://localhost:8000/api/us-market/indices

# 预期结果：返回标普500、纳斯达克、道琼斯、VIX的数据

# 2. 测试A股指数（验证代码格式修复）
curl http://localhost:8000/api/stock/index/realtime?codes=000001.SH,399001.SZ

# 预期结果：返回上证指数、深证成指的数据

# 3. 检查后台日志
# 预期：不再出现 "no such column: symbol" 错误
# 预期：不再出现腾讯API 501错误
```

---

## 📊 数据库状态

**数据库文件**: `stock_peg.db` (4.52 MB)

**数据统计**:
- 财务数据: 1286条
- 美股数据: 11条
- 日志记录: 大量

**表结构**:
- ✓ `fundamental_metrics` - 财务指标
- ✓ `financial_history` - 财务历史
- ✓ `us_daily_data` - 美股日线（列名: `us_stock_code`）
- ✓ `stock_kline_data` - A股K线
- ✓ `stock_realtime_quote` - 实时行情
- ✓ `data_update_log` - 更新日志
- ✓ `data_source_track` - 数据源追踪

---

## 📌 总结

### 根本原因
1. **数据库列名不匹配**: 代码中使用 `symbol`，实际列名是 `us_stock_code`
2. **代码格式不兼容**: 前端传递的指数代码格式与数据源要求的格式不一致

### 影响范围
- ❌ headbar无法显示任何指数（A股+美股）
- ❌ 美股指数API返回空数据
- ⚠️ VIX数据更新不及时

### 修复难度
- ⭐ 简单: 问题定位清晰，修复方法明确
- ⏱️ 预计时间: 30分钟内可完成修复

### 下一步行动
1. 修改 `us_market_analyzer.py` 中的列名
2. 添加A股指数代码格式转换
3. 测试验证所有指数获取
4. 优化VIX数据源

---

**诊断完成时间**: 2026-03-09 19:55  
**状态**: ✅ 已定位所有问题，等待修复实施
