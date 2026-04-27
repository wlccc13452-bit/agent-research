# 控制台输出配置说明

## 配置文件位置

`backend/config/console_output.ini`

## 快速开始

### 1. 最小化输出（推荐生产环境）

```ini
[console_output]
enable_console_output = true
enable_errors = true
enable_warnings = true
enable_startup_info = true
enable_feishu_bot = true
enable_feishu_connection = true
enable_feishu_chat = true

# 其他全部设置为 false
enable_stock_data = false
enable_market_index = false
...（其他设为false）
```

### 2. 调试模式（开发环境）

```ini
[console_output]
enable_console_output = true
enable_debug = true
enable_stock_data = true
enable_market_index = true
enable_kline_data = true
...（根据需要开启）
```

### 3. 完全静默

```ini
[console_output]
enable_console_output = false
enable_errors = false
```

---

## 配置项详解

### 总开关

| 配置项 | 默认值 | 说明 |
|-------|--------|------|
| `enable_console_output` | true | 总开关，关闭后只输出错误（如果enable_errors=true） |

### 数据类输出

| 配置项 | 默认值 | 控制内容 |
|-------|--------|---------|
| `enable_stock_data` | false | 股票数据读取、更新、查询日志 |
| `enable_market_index` | false | 市场指数数据日志 |
| `enable_kline_data` | false | K线数据读取、更新日志 |
| `enable_financial_data` | false | 财务数据日志 |
| `enable_us_market` | false | 美股市场数据日志 |

**适用场景**：
- 日常运行：设为 `false` 减少噪音
- 调试数据问题：设为 `true` 查看数据流

### 功能类输出

| 配置项 | 默认值 | 控制内容 |
|-------|--------|---------|
| `enable_update_progress` | false | 数据更新进度日志 |
| `enable_preload_progress` | false | 启动预加载进度日志 |
| `enable_cache` | false | 缓存命中/未命中日志 |
| `enable_websocket` | false | WebSocket连接/断开/消息日志 |

**适用场景**：
- 正常使用：设为 `false`
- 排查更新问题：`enable_update_progress = true`
- 排查连接问题：`enable_websocket = true`

### 飞书机器人专用

| 配置项 | 默认值 | 控制内容 |
|-------|--------|---------|
| `enable_feishu_bot` | **true** | 飞书机器人消息收发日志 |
| `enable_feishu_connection` | **true** | 飞书长连接状态日志 |
| `enable_feishu_chat` | **true** | 飞书对话历史日志 |

**重要**：飞书机器人日志默认开启，方便监控机器人运行状态

### 其他输出

| 配置项 | 默认值 | 控制内容 |
|-------|--------|---------|
| `enable_scheduler` | false | 定时任务触发、执行日志 |
| `enable_background_task` | false | 后台任务执行日志 |
| `enable_database` | false | 数据库操作日志 |
| `enable_api_request` | false | API请求/响应日志 |

### 错误和警告

| 配置项 | 默认值 | 说明 |
|-------|--------|------|
| `enable_errors` | **true** | 错误日志（ERROR级别） |
| `enable_warnings` | **true** | 警告日志（WARNING级别） |
| `enable_debug` | false | 调试日志（DEBUG级别） |

**建议**：
- 生产环境：保持 `enable_errors = true` 和 `enable_warnings = true`
- 开发调试：开启 `enable_debug = true`

### 启动信息

| 配置项 | 默认值 | 说明 |
|-------|--------|------|
| `enable_startup_info` | **true** | 启动进度、服务就绪信息 |
| `enable_system_status` | **true** | 系统状态、完成标记 |

---

## 进度条配置

```ini
[progress_bar]
show_progress_bar = true
progress_update_interval = 500
```

| 配置项 | 默认值 | 说明 |
|-------|--------|------|
| `show_progress_bar` | true | 是否显示命令行进度条 |
| `progress_update_interval` | 500 | 进度条更新间隔（毫秒） |

**注意**：进度条仅在 `enable_preload_progress = true` 时显示

---

## 使用示例

### 示例1：监控飞书机器人运行

```ini
[console_output]
enable_console_output = true
enable_errors = true
enable_warnings = true
enable_feishu_bot = true
enable_feishu_connection = true
enable_feishu_chat = true
enable_startup_info = true

# 其他全部 false
```

**效果**：只显示启动信息、错误、警告和飞书相关日志

### 示例2：排查数据更新问题

```ini
[console_output]
enable_console_output = true
enable_errors = true
enable_warnings = true
enable_debug = true
enable_stock_data = true
enable_update_progress = true
enable_database = true
```

**效果**：显示股票数据、更新进度和数据库操作日志

### 示例3：完全静默运行

```ini
[console_output]
enable_console_output = false
enable_errors = false
```

**效果**：控制台几乎无输出（仅严重错误）

---

## 配置生效方式

### 方法1：重启服务（推荐）

```bash
# 停止服务
Ctrl+C

# 启动服务
cd backend
python main.py
```

### 方法2：API动态重载（开发中）

未来将支持通过API动态修改配置：

```bash
POST /api/config/reload-console-output
```

---

## 日志过滤规则

系统按以下优先级过滤日志：

1. **总开关检查**：`enable_console_output`
2. **日志级别检查**：ERROR、WARNING、DEBUG配置
3. **模块名匹配**：根据日志记录器名称匹配配置
4. **关键词匹配**：根据日志消息中的关键词匹配配置
5. **默认策略**：未匹配的日志默认输出

---

## 常见问题

### Q1: 修改配置后没有生效？

**A**: 需要重启服务才能生效

### Q2: 错误日志太多怎么办？

**A**: 设置 `enable_errors = false`（不推荐，可能错过重要错误）

### Q3: 想看特定股票的数据日志？

**A**: 
```ini
enable_stock_data = true
enable_debug = true
```

### Q4: 飞书机器人没有响应，如何排查？

**A**: 
```ini
enable_feishu_bot = true
enable_feishu_connection = true
enable_debug = true
```

---

## 代码集成

### 使用ManagedLogger

```python
from services.managed_logger import get_stock_logger, get_feishu_logger

# 股票数据日志
stock_logger = get_stock_logger('my_module')
stock_logger.info("更新股票数据: 000001")  # 受enable_stock_data控制

# 飞书日志
feishu_logger = get_feishu_logger('my_bot')
feishu_logger.info("收到消息: 你好")  # 受enable_feishu_bot控制
```

### 使用原生logger（自动过滤）

```python
import logging

logger = logging.getLogger('services.stock_data_service')
logger.info("更新数据")  # 自动被过滤器控制
```

---

## 推荐配置

### 生产环境（服务器部署）

```ini
[console_output]
enable_console_output = true
enable_errors = true
enable_warnings = true
enable_startup_info = true
enable_system_status = true
enable_feishu_bot = true
enable_feishu_connection = true

[progress_bar]
show_progress_bar = false
```

### 开发环境

```ini
[console_output]
enable_console_output = true
enable_errors = true
enable_warnings = true
enable_debug = true
enable_startup_info = true
enable_system_status = true

[progress_bar]
show_progress_bar = true
```

### 测试环境

```ini
[console_output]
enable_console_output = true
enable_errors = true
enable_warnings = true
enable_debug = true
enable_database = true
enable_api_request = true

[progress_bar]
show_progress_bar = true
```

---

## 总结

1. ✅ **飞书机器人日志默认开启**，方便监控运行状态
2. ✅ **错误和警告默认开启**，不遗漏重要信息
3. ✅ **数据类日志默认关闭**，减少控制台噪音
4. ✅ **灵活配置**，根据需要开启特定类型日志
5. ✅ **重启生效**，修改配置后记得重启服务
