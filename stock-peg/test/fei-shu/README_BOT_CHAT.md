# 飞书机器人独立对话 Demo

## 功能说明

这是一个独立的飞书机器人对话 demo，使用 WebSocket 长连接模式，无需公网域名。

## 运行方式

### 1. 使用项目虚拟环境（推荐）

```powershell
cd D:\play-ground\股票研究\stock-peg\test\fei-shu
D:\play-ground\股票研究\stock-peg\backend\.venv\Scripts\python.exe bot_chat.py
```

### 2. 使用系统 Python（需先安装依赖）

```bash
pip install lark-oapi
cd test/fei-shu
python bot_chat.py
```

## 配置要求

脚本会自动从 `backend/.env` 加载以下配置：

```env
FEISHU_APP_ID=cli_xxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxx
```

## 飞书开放平台配置

### 1. 开通权限

在飞书开放平台 → 应用 → 权限管理 中开通：

- `im:message` - 获取消息
- `im:message:send_as_bot` - 发送消息

### 2. 事件订阅

在事件订阅中启用：

- **接收消息**: `im.message.receive_v1`

### 3. 发布版本

配置完成后，需要创建版本并发布应用

## 测试方法

1. 启动脚本后，会显示：

```
------------------------------------------
[STOCK] 交易机器人正在启动...
[App ID] cli_a93c48...
[模式] WebSocket 长连接 (无需公网域名)
------------------------------------------

[监听] 正在监听消息...
[提示] 在飞书手机端或网页端给机器人发送消息
[停止] 按 Ctrl+C 停止
```

2. 在飞书手机端或网页端给机器人发送消息

3. 机器人会自动回复：

```
查询 700       → 查询股票信息
买入 700       → 模拟买入操作
帮助           → 查看帮助信息
```

## 自定义业务逻辑

修改 `bot_chat.py` 中的 `trading_logic_handler()` 函数，对接你的实际业务：

```python
def trading_logic_handler(command: str) -> str:
    """
    处理交易指令
    可替换为实际的业务逻辑
    """
    # TODO: 对接你的股票查询/交易逻辑
    # 例如：调用 backend API 获取实时行情
    # 或者查询数据库
    pass
```

## 故障排查

### 1. 配置未加载

```
[错误] 请先在 .env 中配置 FEISHU_APP_ID 和 FEISHU_APP_SECRET
```

解决：检查 `backend/.env` 文件是否存在且配置正确

### 2. 连接失败

可能原因：
- App ID 或 App Secret 错误
- 飞书应用未发布
- 权限未开通

### 3. 收不到消息

可能原因：
- 未启用事件订阅 `im.message.receive_v1`
- 机器人未添加到群聊或单聊会话

## 相关文件

- `bot_chat.py` - 机器人主程序
- `test_config.py` - 配置测试脚本
- `check_sdk.py` - SDK 检查脚本
- `backend/.env` - 配置文件
- `backend/services/feishu_bot.py` - 项目集成的飞书服务（webhook 模式）

## 注意事项

1. **WebSocket 模式** 适用于本地开发和测试，无需公网域名
2. **Webhook 模式** 适用于生产环境，需要公网域名（项目主应用使用此模式）
3. 两种模式可以同时使用，互不影响
