# 数据更新策略配置说明

## 配置文件位置

`backend/config/layout.ini`

---

## 配置项详解

### [data_update] - 数据更新策略配置

#### 1. 后台更新任务配置

| 配置项 | 默认值 | 说明 | 调优建议 |
|-------|--------|------|---------|
| `max_concurrent_tasks` | 10 | 最大并发更新任务数 | • 服务器性能强：可增加到 20<br>• 性能较弱：降低到 5<br>• 避免设置过大导致API限流 |
| `task_timeout_seconds` | 30 | 单个任务超时时间（秒） | • 网络慢：可增加到 60<br>• 网络快：可降低到 20<br>• 超时后任务会被取消 |

**示例场景**：
```
场景1：高性能服务器 + 稳定网络
max_concurrent_tasks = 20
task_timeout_seconds = 20

场景2：普通服务器 + 一般网络
max_concurrent_tasks = 10
task_timeout_seconds = 30

场景3：低性能服务器 + 慢网络
max_concurrent_tasks = 5
task_timeout_seconds = 60
```

---

#### 2. 更新锁配置

| 配置项 | 默认值 | 说明 | 调优建议 |
|-------|--------|------|---------|
| `lock_expire_seconds` | 300 | 更新锁过期时间（秒）<br>防止同一股票重复更新 | • 一般保持默认<br>• 数据源快：可降低到 180<br>• 数据源慢：可增加到 600 |
| `cache_expire_seconds` | 60 | 缓存过期时间（秒）<br>检查更新必要性的缓存时间 | • 实时性要求高：降低到 30<br>• 减少API调用：增加到 120 |

**工作原理**：
```
用户请求 → 检查缓存 → 缓存未过期 → 直接返回结果
                  ↓ 缓存过期
                  → 检查数据库更新时间
                  → 判断是否需要更新
```

---

#### 3. 启动预加载配置

| 配置项 | 默认值 | 说明 | 调优建议 |
|-------|--------|------|---------|
| `preload_timeout_seconds` | 30 | Server启动时预加载超时（秒） | • 数据多：增加到 60<br>• 数据少：降低到 15<br>• 超时后转为后台任务 |
| `preload_wait_for_completion` | true | 是否等待预加载完成 | • 生产环境：true（确保数据完整）<br>• 开发环境：false（快速启动） |

**启动流程**：
```
Server启动
    ↓
预加载数据（阻塞式，最多30秒）
    ├─ 加载自持股票K线
    ├─ 加载国内指数
    ├─ 提交美股指数更新任务（后台）
    └─ 提交财务数据更新任务（后台）
    ↓
超时或完成后启动服务
    ↓
后台继续更新剩余数据
```

---

#### 4. K线数据更新间隔

| 配置项 | 默认值 | 说明 | 调优建议 |
|-------|--------|------|---------|
| `kline_trading_update_interval` | 1 | 交易时段更新间隔（小时）<br>交易时间：9:00-15:00 | • 高频交易：0.5（30分钟）<br>• 一般用户：1（1小时）<br>• 减少API调用：2（2小时） |
| `kline_non_trading_update_interval` | 12 | 非交易时段更新间隔（小时）<br>非交易时间：15:00后 | • 保持默认：12小时<br>• 盘前关注：降低到 4<br>• 减少更新：增加到 24 |

**更新策略说明**：
```
交易时段（9:00-15:00）：
  • 上次更新 < 1小时 → 不更新，返回缓存
  • 上次更新 ≥ 1小时 → 后台更新

非交易时段（15:00后）：
  • 上次更新 < 12小时 → 不更新，返回缓存
  • 上次更新 ≥ 12小时 → 后台更新
```

**示例配置**：
```ini
# 激进更新策略（适合日内交易）
kline_trading_update_interval = 0.5
kline_non_trading_update_interval = 4

# 保守更新策略（适合长线投资）
kline_trading_update_interval = 2
kline_non_trading_update_interval = 24

# 平衡策略（默认推荐）
kline_trading_update_interval = 1
kline_non_trading_update_interval = 12
```

---

#### 5. 财务数据更新间隔

| 配置项 | 默认值 | 说明 | 调优建议 |
|-------|--------|------|---------|
| `financial_update_interval_days` | 7 | 财务数据更新间隔（天） | • 财报季：降低到 1-3<br>• 非财报季：保持 7<br>• 减少更新：增加到 14 |

**财务数据包括**：
- 基本面指标（PE、PB、ROE等）
- 年报数据
- 季报数据（最近3年）

**更新时机**：
```
判断逻辑：
  • 上次更新 < 7天 → 不更新
  • 上次更新 ≥ 7天 → 后台更新
  • 数据库无记录 → 立即更新
```

---

#### 6. 美股指数更新间隔

| 配置项 | 默认值 | 说明 | 调优建议 |
|-------|--------|------|---------|
| `us_index_update_interval_hours` | 24 | 美股指数更新间隔（小时） | • 美股交易时段：12<br>• 一般关注：24<br>• 减少更新：48 |

**包括的美股指数**：
- `^GSPC` - 标普500指数
- `^IXIC` - 纳斯达克指数
- `^DJI` - 道琼斯指数
- `^VIX` - 波动率指数

---

## 配置修改示例

### 场景1：日内交易者（高频更新）

```ini
[data_update]
# 高频交易配置
max_concurrent_tasks = 20
task_timeout_seconds = 20

# 更积极的更新策略
kline_trading_update_interval = 0.5
kline_non_trading_update_interval = 4

# 财报季更频繁更新
financial_update_interval_days = 3

# 美股交易时段更频繁
us_index_update_interval_hours = 12
```

### 场景2：长线投资者（低频更新）

```ini
[data_update]
# 低频更新配置
max_concurrent_tasks = 5
task_timeout_seconds = 60

# 更保守的更新策略
kline_trading_update_interval = 4
kline_non_trading_update_interval = 24

# 财务数据降低更新频率
financial_update_interval_days = 14

# 美股指数降低更新频率
us_index_update_interval_hours = 48
```

### 场景3：服务器性能有限（节省资源）

```ini
[data_update]
# 降低并发
max_concurrent_tasks = 5

# 增加缓存时间
cache_expire_seconds = 120

# 增加更新间隔
kline_trading_update_interval = 2
kline_non_trading_update_interval = 24
financial_update_interval_days = 14
us_index_update_interval_hours = 48
```

---

## 配置生效方式

### 1. 修改配置文件

编辑 `backend/config/layout.ini`

### 2. 重启服务

```bash
# 停止服务
Ctrl+C

# 启动服务
cd backend
python main.py
```

**注意**：配置修改后需要重启服务才能生效

---

## 监控和调试

### 1. 查看当前配置

```python
from config.settings import settings

print(f"最大并发任务: {settings.max_concurrent_tasks}")
print(f"K线交易时段间隔: {settings.kline_trading_update_interval}小时")
print(f"财务数据间隔: {settings.financial_update_interval_days}天")
```

### 2. 查看更新日志

```bash
# 查看后台更新日志
tail -f backend/logs/app.log | grep "更新"

# 查看任务状态
curl http://localhost:8000/api/data/tasks
```

### 3. 检查数据新鲜度

```bash
# 检查股票数据更新状态
curl "http://localhost:8000/api/kline/kline-status/000001"
```

---

## 最佳实践

### 1. 根据使用场景选择配置

| 使用场景 | K线更新 | 财务更新 | 并发数 |
|---------|---------|---------|--------|
| 日内交易 | 0.5小时 | 1天 | 20 |
| 波段操作 | 1-2小时 | 3天 | 10 |
| 长线投资 | 4小时 | 14天 | 5 |
| 性能优先 | 2小时 | 7天 | 5 |

### 2. 根据服务器性能调整

| 服务器性能 | 并发数 | 超时时间 | 锁过期时间 |
|-----------|--------|---------|-----------|
| 高性能 | 20 | 20秒 | 180秒 |
| 中等 | 10 | 30秒 | 300秒 |
| 低性能 | 5 | 60秒 | 600秒 |

### 3. 根据数据源稳定性

| 数据源稳定性 | 重试次数 | 超时时间 | 说明 |
|-------------|---------|---------|------|
| 非常稳定 | 1 | 20秒 | 使用默认配置 |
| 一般 | 2 | 30秒 | 增加超时时间 |
| 不稳定 | 3 | 60秒 | 大幅增加超时 |

---

## 故障排查

### 问题1：更新太频繁，API被限流

**现象**：API返回429错误

**解决**：
```ini
# 降低更新频率
kline_trading_update_interval = 2
financial_update_interval_days = 14
max_concurrent_tasks = 5
```

### 问题2：数据不够新鲜

**现象**：看到的行情数据延迟大

**解决**：
```ini
# 提高更新频率
kline_trading_update_interval = 0.5
cache_expire_seconds = 30
```

### 问题3：服务器负载高

**现象**：CPU/内存占用高

**解决**：
```ini
# 降低并发和缓存
max_concurrent_tasks = 5
cache_expire_seconds = 120
kline_trading_update_interval = 4
```

---

## 配置验证

修改配置后，启动服务时会看到：

```
DataUpdateManager 初始化完成
BackgroundUpdater 初始化完成
开始智能预加载市场数据...
  最大并发任务: 10
  K线交易时段间隔: 1小时
  K线非交易时段间隔: 12小时
  财务数据间隔: 7天
  美股指数间隔: 24小时
```

---

## 总结

通过调整这些配置参数，可以：

1. ✅ **平衡性能与实时性**：根据使用场景调整更新频率
2. ✅ **避免API限流**：控制并发数和更新频率
3. ✅ **节省服务器资源**：降低不必要的更新
4. ✅ **提高用户体验**：确保数据足够新鲜

**推荐配置**（适合大多数用户）：
```ini
[data_update]
max_concurrent_tasks = 10
task_timeout_seconds = 30
lock_expire_seconds = 300
cache_expire_seconds = 60
preload_timeout_seconds = 30
preload_wait_for_completion = true
kline_trading_update_interval = 1
kline_non_trading_update_interval = 12
financial_update_interval_days = 7
us_index_update_interval_hours = 24
```

这个配置在性能、实时性和资源占用之间取得了良好的平衡。
