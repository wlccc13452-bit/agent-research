# 配置文件快速参考

## 📝 配置文件

`backend/config/layout.ini`

## 🎯 快速配置模板

### 1️⃣ 日内交易者（推荐）

```ini
[data_update]
max_concurrent_tasks = 15
kline_trading_update_interval = 0.5
kline_non_trading_update_interval = 6
financial_update_interval_days = 3
us_index_update_interval_hours = 12
```

### 2️⃣ 长线投资者（推荐）

```ini
[data_update]
max_concurrent_tasks = 5
kline_trading_update_interval = 4
kline_non_trading_update_interval = 24
financial_update_interval_days = 14
us_index_update_interval_hours = 48
```

### 3️⃣ 默认平衡配置

```ini
[data_update]
max_concurrent_tasks = 10
kline_trading_update_interval = 1
kline_non_trading_update_interval = 12
financial_update_interval_days = 7
us_index_update_interval_hours = 24
```

## ⚙️ 配置项速查

| 配置项 | 作用 | 默认值 | 建议范围 |
|-------|------|--------|---------|
| `max_concurrent_tasks` | 最大并发更新数 | 10 | 5-20 |
| `kline_trading_update_interval` | 交易时段K线更新间隔(小时) | 1 | 0.5-4 |
| `kline_non_trading_update_interval` | 非交易时段K线更新间隔(小时) | 12 | 4-24 |
| `financial_update_interval_days` | 财务数据更新间隔(天) | 7 | 1-14 |
| `us_index_update_interval_hours` | 美股指数更新间隔(小时) | 24 | 12-48 |

## 🔄 生效方式

修改配置后重启服务：
```bash
# 停止服务: Ctrl+C
# 启动服务: python main.py
```

## 📊 详细说明

查看 `数据更新策略配置说明.md` 了解更多细节。
