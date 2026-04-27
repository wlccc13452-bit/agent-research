# PegBot 卡片功能使用指南

## 问题: 手机看不到卡片?

这可能是因为还没有触发卡片显示。以下是几种触发卡片的方式。

## 方式一: 发送文字命令(推荐)

在飞书手机端,直接给 PegBot 发送以下任一命令:

### 1. 查看主菜单卡片
```
菜单
```
或
```
主菜单
```

### 2. 查看持仓列表(快捷方式)
```
持仓
```
或
```
自持股票
```

### 3. 查看今日关注列表(快捷方式)
```
关注
```
或
```
动态关注
```

### 4. 查询股票
```
查询 平安银行
```
或
```
行情 000001
```

### 5. 查看帮助
```
帮助
```

---

## 方式二: 通过API触发卡片

如果需要主动推送主菜单卡片,可以使用API接口:

### 1. 发送主菜单卡片

**请求:**
```bash
POST http://localhost:8000/feishu/send-main-menu-card
```

**响应:**
```json
{
  "status": "ok",
  "message": "Main menu card sent successfully",
  "chat_id": "oc_xxxxx"
}
```

### 2. 发送股票查询卡片

**请求:**
```bash
POST http://localhost:8000/feishu/send-stock-query-card
```

**响应:**
```json
{
  "status": "ok",
  "message": "Stock query card sent successfully",
  "chat_id": "oc_xxxxx"
}
```

### 3. 通过前端按钮发送

在前端页面(通常是 http://localhost:5173),点击相应按钮即可触发卡片发送。

---

## 方式三: 使用curl命令测试

### 发送主菜单卡片
```bash
curl -X POST http://localhost:8000/feishu/send-main-menu-card
```

### 发送股票查询卡片
```bash
curl -X POST http://localhost:8000/feishu/send-stock-query-card
```

---

## 主菜单卡片功能说明

主菜单卡片包含以下按钮:

### 快捷查看按钮(蓝色主要按钮)
- **📈 查看持仓** → 直接显示持仓列表
- **👀 查看关注** → 直接显示今日关注列表

### 管理功能按钮(灰色默认按钮)
- **📊 股票查询** → 打开股票查询卡片
- **💰 价格查询** → 打开价格查询卡片
- **💼 持仓管理** → 进入持仓管理菜单(添加/删除股票)
- **📋 关注管理** → 进入关注列表管理菜单(添加/删除关注)
- **🔔 价格提醒** → 进入价格提醒菜单

---

## 完整使用流程示例

### 场景1: 查看持仓

**方式A - 发送命令(最简单):**
```
用户: 持仓
Bot: 📊 持仓概览

铝:
  • 南山铝业
  • 中国神华

光伏:
  • 隆基绿能

━━━━━━━━━━━━
共 11 只股票
```

**方式B - 点击卡片按钮:**
```
用户: 菜单
Bot: [发送主菜单卡片]
用户: [点击 "📈 查看持仓"]
Bot: 📊 持仓概览
     ...
```

### 场景2: 查看今日关注

**方式A - 发送命令:**
```
用户: 关注
Bot: 👀 今日关注列表
📅 2026-03-17

平安银行 (000001)
  🎯 目标价: 15.50
  🛡️ 止损价: 13.00
  📝 理由: 突破前期压力位

━━━━━━━━━━━━
共 1 只股票
```

**方式B - 点击卡片按钮:**
```
用户: 菜单
Bot: [发送主菜单卡片]
用户: [点击 "👀 查看关注"]
Bot: 👀 今日关注列表
     ...
```

---

## 常见问题

### Q1: 发送命令没有反应?
**A:** 检查以下几点:
1. 确认后端服务正在运行 (`http://localhost:8000`)
2. 确认飞书机器人配置正确(检查 `.env` 文件中的 `FEISHU_APP_ID` 和 `FEISHU_APP_SECRET`)
3. 确认飞书webhook或长连接服务正常
4. 查看后端日志是否有错误

### Q2: 看不到卡片,只看到文字?
**A:** 飞书卡片可能在某些情况下显示为文字,尝试:
1. 更新飞书客户端到最新版本
2. 使用文字命令代替卡片操作
3. 检查卡片JSON格式是否正确

### Q3: 如何测试卡片功能?
**A:** 使用API接口测试:
```bash
# 发送主菜单卡片
curl -X POST http://localhost:8000/feishu/send-main-menu-card

# 检查WebSocket连接状态
curl http://localhost:8000/feishu/websocket-status

# 检查消息统计
curl http://localhost:8000/feishu/message-stats
```

### Q4: 卡片按钮点击没反应?
**A:** 检查:
1. 后端日志中是否有 `card.callback.trigger` 事件
2. 卡片回调处理函数是否正常执行
3. 使用 `/feishu/test-broadcast` 测试WebSocket连接

---

## 调试技巧

### 1. 查看后端日志
```bash
# 查看最近的飞书事件日志
tail -f backend/logs/bot_chat.log

# 查看后端控制台输出
# 启动后端时会实时显示日志
```

### 2. 测试飞书连接
```bash
# 测试飞书机器人连接
curl http://localhost:8000/feishu/test

# 查看长连接状态
curl http://localhost:8000/feishu/long-connection-status
```

### 3. 手动触发卡片
```bash
# 发送主菜单卡片到最近的会话
curl -X POST http://localhost:8000/feishu/send-main-menu-card

# 发送股票查询卡片
curl -X POST http://localhost:8000/feishu/send-stock-query-card
```

---

## 下一步

1. **在飞书手机端给 PegBot 发送消息"菜单"或"持仓"**
2. 如果还是没有卡片显示,使用 curl 命令测试
3. 检查后端日志确认卡片是否发送成功

## 需要帮助?

如果以上方法都无法解决,请:
1. 提供后端日志截图
2. 提供飞书客户端版本
3. 说明具体的错误现象
