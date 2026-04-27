# PegBot 事件卡片推送功能

## 功能概述

PegBot 支持通过事件ID推送飞书卡片消息，实现特定场景的主动通知和引导。

## 已支持的事件

### 1. STOCK_RESEARCH_START - 开始股票研究

**事件说明**：用于启动股票研究流程的引导卡片

**推送内容**：
- 显示当前时间
- 提供快捷操作按钮：
  - 输入股票代码 - 跳转到股票查询
  - 查看持仓 - 快速查看持仓列表
  - 查看关注 - 快速查看关注列表
  - 打开主菜单 - 进入完整功能菜单

## 使用方法

### 方式1：通过API推送

**接口地址**：`POST /api/feishu/push-event/{event_id}`

**示例请求**：
```bash
curl -X POST http://localhost:8000/api/feishu/push-event/STOCK_RESEARCH_START
```

**成功响应**：
```json
{
  "status": "ok",
  "message": "Event card STOCK_RESEARCH_START sent successfully",
  "event_id": "STOCK_RESEARCH_START",
  "chat_id": "oc_xxxxxx"
}
```

**错误响应**：
```json
{
  "detail": "暂无可用飞书会话，请先在飞书给机器人发送一条消息"
}
```

### 方式2：在代码中调用

```python
from services.feishu_card_service import card_service

# 发送 STOCK_RESEARCH_START 事件卡片
success = await card_service.send_stock_research_start_card(chat_id)
```

## 前置条件

1. **飞书机器人已配置**：
   - 已在 `.env` 中配置 `FEISHU_APP_ID` 和 `FEISHU_APP_SECRET`
   - 机器人已添加到飞书群聊或已建立单聊

2. **已有聊天记录**：
   - 需要先在飞书给机器人发送一条消息，建立会话
   - 系统会自动获取最近的 chat_id 进行推送

## 扩展新事件

### 步骤1：创建卡片模板

在 `backend/services/feishu_card_service.py` 中添加：

```python
def _create_your_event_card(self) -> dict[str, Any]:
    """Create your event card"""
    card = {
        "type": "template",
        "config": {"wide_screen_mode": True},
        "elements": [
            # 卡片元素定义
        ]
    }
    return card
```

### 步骤2：添加发送方法

```python
async def send_your_event_card(self, chat_id: str) -> bool:
    """Send your event card"""
    card = self._create_your_event_card()
    return await self._send_card_message(chat_id, card)
```

### 步骤3：注册事件处理

在 `backend/routers/feishu.py` 的 `push_event_card` 函数中添加：

```python
if event_id == "YOUR_EVENT_ID":
    success = await card_service.send_your_event_card(chat_id)
```

## 应用场景

### 1. 定时提醒
```python
# 每日开盘前推送
schedule.every().day.at("09:00").do(
    lambda: asyncio.run(push_event("STOCK_RESEARCH_START"))
)
```

### 2. 数据更新通知
```python
# 重大数据更新后推送
if has_important_update:
    await card_service.send_stock_research_start_card(chat_id)
```

### 3. 用户触发
```python
# 前端按钮触发
@app.post("/start-research")
async def start_research():
    return await push_event_card("STOCK_RESEARCH_START")
```

## 测试验证

运行测试脚本：
```bash
cd d:/2026projects/stocks-research/stock-peg
python -c "
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path('backend')))

async def test():
    from services.feishu_card_service import card_service
    # 需要提供实际的 chat_id
    chat_id = 'oc_xxxxxx'  # 替换为实际chat_id
    success = await card_service.send_stock_research_start_card(chat_id)
    print(f'发送结果: {success}')

asyncio.run(test())
"
```

或通过HTTP接口测试：
```bash
# 需要先启动后端服务
python backend/main.py

# 在另一个终端执行
curl -X POST http://localhost:8000/api/feishu/push-event/STOCK_RESEARCH_START
```

## 注意事项

1. **权限要求**：机器人需要有发送消息的权限
2. **频率限制**：避免频繁推送，建议设置合理的推送间隔
3. **用户订阅**：建议实现用户订阅机制，避免打扰不相关用户
4. **错误处理**：推送失败时会记录日志，不会影响主流程

## 相关文件

- 卡片服务：`backend/services/feishu_card_service.py`
- API路由：`backend/routers/feishu.py`
- 使用指南：`docs/pegbot_card_usage.md`
- 持仓关注查询：`docs/pegbot_holdings_watchlist_query.md`

## 更新日志

- **2026-03-17**: 初始实现 STOCK_RESEARCH_START 事件推送功能
