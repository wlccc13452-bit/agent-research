# 飞书机器人配置检查清单

## 问题现象

WebSocket 连接成功，进入会话事件触发，但**消息事件未触发**。

## 原因分析

飞书开放平台没有发送消息事件给机器人，可能是权限或配置问题。

## 配置步骤

### 1. 检查权限配置

访问飞书开放平台：https://open.feishu.cn/app

找到你的应用（App ID: cli_a93c48cba4b8dbef）

**权限管理 → 应用能力 → 消息**

需要开通以下权限：

- ✅ `im:message` - 获取消息
- ✅ `im:message:send_as_bot` - 以应用身份发消息
- ✅ `im:message:receive_as_bot` - 接收群聊中@机器人或发送给机器人的消息
- ✅ `im:chat` - 获取群组信息
- ✅ `im:chat:readonly` - 获取群组信息（只读）

### 2. 检查事件订阅

**事件订阅 → 订阅方式**

选择：**使用长连接接收事件**（WebSocket 模式）

**事件订阅 → 订阅事件列表**

需要添加以下事件：

- ✅ `im.message.receive_v1` - 接收消息
- ✅ `im.chat.access_event.bot_p2p_chat_entered_v1` - 进入私聊会话（可选）

### 3. 检查应用发布状态

**版本管理 → 版本列表**

- 如果是测试环境：确保应用状态为"测试中"或"已发布"
- 如果是生产环境：必须"已发布"

### 4. 检查可用性设置

**应用发布 → 可用性设置**

- 确保你的飞书账号在"可用范围"内
- 如果是全员可见，确保设置为"全员可见"

## 快速诊断

### 方法1：使用通用事件处理器

运行修改后的 `bot_chat.py`，查看是否有其他事件类型：

```powershell
cd D:\play-ground\股票研究\stock-peg\test\fei-shu
D:\play-ground\股票研究\stock-peg\backend\.venv\Scripts\python.exe bot_chat.py
```

### 方法2：检查日志中的错误信息

如果飞书发送了事件但没有注册处理器，会看到：

```
[Lark] [ERROR] handle message failed, err: processor not found, type: xxx
```

### 方法3：使用 Webhook 模式对比

如果 WebSocket 模式不工作，可以尝试使用项目的 Webhook 模式：

```bash
# 启动后端服务
cd D:\play-ground\股票研究\stock-peg
python -m backend.main

# 使用 ngrok 暴露本地服务
ngrok http 8000
```

然后将 ngrok URL 配置到飞书开放平台的 Webhook 地址：
`https://xxx.ngrok.io/feishu/webhook`

## 常见问题

### Q1: 为什么进入会话事件触发了，但消息事件没触发？

A: 权限不足或事件未订阅。进入会话是轻量级事件，消息事件需要更高权限。

### Q2: 如何确认权限已生效？

A: 
1. 权限配置后，需要点击"申请发布"
2. 等待管理员审批（或自己审批）
3. 发布成功后，权限才生效

### Q3: WebSocket 和 Webhook 有什么区别？

A:
- **WebSocket（长连接）**：本地开发友好，无需公网域名，适合测试
- **Webhook（HTTP回调）**：需要公网域名，适合生产环境

## 推荐操作顺序

1. ✅ 检查权限配置（开通所有消息相关权限）
2. ✅ 检查事件订阅（确保 `im.message.receive_v1` 已添加）
3. ✅ 检查应用发布状态（确保已发布）
4. ✅ 重启机器人脚本
5. ✅ 在飞书中发送消息测试

## 联系支持

如果以上步骤都无法解决问题：

1. 检查飞书开放平台的"开发者后台"日志
2. 使用飞书官方调试工具测试
3. 考虑使用 Webhook 模式替代

---

**当前状态**：
- ✅ WebSocket 连接成功
- ✅ 进入会话事件正常
- ❌ 消息事件未触发

**下一步**：检查飞书开放平台的权限和事件订阅配置。
