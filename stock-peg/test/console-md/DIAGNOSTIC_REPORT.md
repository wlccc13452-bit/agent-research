# 数据获取问题诊断报告

**诊断时间**: 2026-03-09 19:34:40  
**诊断工具**: diagnose_data_issue.py

---

## 一、问题总结

根据console.md日志和诊断脚本检查，发现以下问题：

### 1. A股指数获取失败（headbar上的指数）

**问题代码**:
- 000001.SH (上证指数)
- 399001.SZ (深证成指)
- 000016.SH (上证50)
- 399006.SZ (创业板指)
- 000905.SH (中证500)

**错误日志**:
```
18:45:17 - WARNING - ⚠️ 腾讯API获取行情失败 (1/3): 000001.SH, 错误: Server error '501 Not Implemented'
18:45:17 - WARNING - Akshare 未找到股票 000001.SH
18:45:17 - WARNING - ❌ 所有数据源都无法获取行情: 000001.SH
```

**根本原因**:
1. **指数代码格式问题**: 前端传递的是 `000001.SH` 格式（带后缀），但：
   - 腾讯API不支持这种格式（返回501错误）
   - Akshare需要不带后缀的代码或带市场前缀的代码（如 `sh000001`）
   
2. **数据源处理逻辑问题**:
   - 没有对指数代码格式进行转换
   - 腾讯API连续失败后触发熔断机制

---

### 2. 美股指数获取失败（VIX指数）

**问题代码**:
- ^VIX (VIX恐慌指数)

**错误日志**:
```
18:51:29 - WARNING - Eastmoney 返回数据无 data 字段
18:51:31 - WARNING - Alpha Vantage 返回数据格式异常: Unknown
18:51:41 - WARNING - Finnhub 返回数据为空或格式不正确: ^VIX
18:51:42 - ERROR - Failed to get ticker '^VIX' reason: curl证书问题
18:51:42 - WARNING - 已尝试的数据源: eastmoney, alphavantage, finnhub, yahoo，均失败: ^VIX
```

**根本原因**:
1. **VIX指数特殊性**: VIX是波动率指数，部分数据源不支持
2. **证书问题**: Yahoo Finance调用时出现证书路径错误
3. **API响应格式**: 各数据源返回格式不一致

**其他美股指数状态**:
- ^GSPC (标普500): 可能正常
- ^IXIC (纳斯达克): 可能正常
- ^DJI (道琼斯): 可能正常

---

### 3. 财务数据获取问题

**诊断结果**:
- ✓ 数据库中有财务数据记录: **1286条**
- ✓ Tushare Token 已配置
- ✓ Akshare 可用

**潜在问题**:
- Tushare部分接口可能权限不足（根据日志中的"没有接口访问权限"）
- 需要检查具体股票的财务数据是否完整

---

## 二、数据源状态

| 数据源 | 状态 | 备注 |
|--------|------|------|
| Tushare | ✓ 已配置 | 部分接口可能权限不足 |
| Akshare | ✓ 可用 | 需正确处理代码格式 |
| 东方财富(美股) | ✓ 可用 | 支持主要美股指数 |
| Alpha Vantage | ⚠ 异常 | 已配置，但返回数据异常 |
| Finnhub | ✓ 可用 | 已配置且可用 |
| 腾讯API | ✗ 熔断 | 连续失败触发熔断机制 |

---

## 三、数据库状态

### 1. 基本情况
- ✓ 数据库文件存在: `stock_peg.db`
- ✓ 文件大小: 4.52 MB
- ✓ 数据库连接正常
- ✓ 数据库表数量: 10

### 2. 数据统计
- ✓ 财务数据记录数: **1286条**
- ✓ 美股数据记录数: **11条**

### 3. 表结构问题
⚠ **发现**: `us_daily_data` 表查询失败，错误提示 "no such column: symbol"

**需要检查**: 该表的实际列名是什么（可能是 `ticker`、`code` 或其他）

---

## 四、解决方案建议

### 优先级1: 修复A股指数获取

**方案**: 在后端API路由中添加指数代码格式转换

**修改位置**: 
- `backend/routers/stock.py` 或相关的指数获取接口
- `backend/services/` 下的数据获取服务

**代码建议**:
```python
def normalize_index_code(code: str) -> tuple:
    """
    标准化指数代码格式
    
    Args:
        code: 原始代码，如 "000001.SH" 或 "sh000001"
    
    Returns:
        (pure_code, market, akshare_code)
        例如: ("000001", "sh", "sh000001")
    """
    # 去除后缀
    if '.' in code:
        pure_code, suffix = code.split('.')
        market = suffix.lower()
    elif code.startswith(('sh', 'sz')):
        market = code[:2]
        pure_code = code[2:]
    else:
        # 默认判断市场
        market = 'sh' if code.startswith('6') else 'sz'
        pure_code = code
    
    akshare_code = f"{market}{pure_code}"
    
    return pure_code, market, akshare_code
```

---

### 优先级2: 修复VIX指数获取

**方案A**: 使用专门的VIX数据源
- 考虑使用 CBOE官网API
- 或使用支持VIX的数据源（如Yahoo Finance修复证书问题）

**方案B**: 修复证书问题
```python
# 在Yahoo Finance调用时，确保证书路径正确
import certifi
import yfinance as yf

# 方式1: 使用certifi的证书
import ssl
import urllib
ssl_context = ssl.create_default_context(cafile=certifi.where())

# 方式2: 禁用SSL验证（仅测试用，不推荐生产环境）
# import urllib3
# urllib3.disable_warnings()
```

**方案C**: 改用其他数据源优先级
调整 `backend/services/us_market_analyzer.py` 中的数据源优先级，对VIX使用东方财富优先。

---

### 优先级3: 检查数据库表结构

**需要检查**: `us_daily_data` 表的实际列名

**SQL查询**:
```sql
PRAGMA table_info(us_daily_data);
```

**修复**: 如果列名不是 `symbol`，需要更新所有使用该列的查询。

---

### 优先级4: 优化数据源熔断机制

**问题**: 腾讯API熔断后，影响后续所有请求

**建议**:
1. 针对不同类型的数据使用不同的数据源优先级：
   - A股指数: Akshare > 腾讯API
   - A股个股: 腾讯API > Akshare
   - 美股指数: 东方财富 > Yahoo Finance > Alpha Vantage > Finnhub

2. 实现数据源降级策略：
   - 记录每个数据源的失败率
   - 自动切换到备用数据源
   - 定期重试失败的数据源

---

## 五、立即行动计划

### 第一步: 修复指数代码格式
1. 在后端添加代码格式转换函数
2. 修改指数获取接口，正确处理代码格式
3. 测试A股指数获取

### 第二步: 修复VIX数据源
1. 检查并修复证书路径问题
2. 调整数据源优先级
3. 测试VIX数据获取

### 第三步: 检查数据库表结构
1. 确认 `us_daily_data` 表结构
2. 修复相关查询
3. 测试美股指数数据存储和读取

### 第四步: 测试财务数据
1. 选择几只测试股票
2. 验证财务数据完整性
3. 检查Tushare权限

---

## 六、测试验证

运行修复后，使用以下命令验证：

```bash
# 测试A股指数
curl http://localhost:8000/api/stock/index/realtime?codes=000001.SH,399001.SZ

# 测试美股指数
curl http://localhost:8000/api/us-market/indices

# 测试财务数据
curl http://localhost:8000/api/fundamental/600519/annual-report
```

---

## 七、相关文件

- 诊断脚本: `test/console-md/diagnose_data_issue.py`
- 运行脚本: `test/console-md/run_diagnose.bat`
- 日志文件: `test/console-md/console.md`
- 后端服务: `backend/services/`
- API路由: `backend/routers/`

---

**报告生成时间**: 2026-03-09 19:40:00
