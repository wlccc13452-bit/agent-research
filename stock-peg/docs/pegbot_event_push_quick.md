# PegBot 事件推送快速指南

## 功能验证结果

✅ **测试通过** - 2026-03-17 01:52:20

```
状态码: 200
事件ID: STOCK_RESEARCH_START
Chat ID: oc_2e96d78e081c89b7e9b3677cf53d07cf
响应: Event card STOCK_RESEARCH_START sent successfully
```

## 快速使用

### 方式1：curl命令

```bash
curl -X POST http://localhost:8000/api/feishu/push-event/STOCK_RESEARCH_START
```

### 方式2：浏览器访问

直接在浏览器地址栏输入:
```
http://localhost:8000/api/feishu/push-event/STOCK_RESEARCH_START
```

### 方式3：前端JavaScript

```javascript
// 推送STOCK_RESEARCH_START事件
async function pushResearchEvent() {
  const response = await fetch('/api/feishu/push-event/STOCK_RESEARCH_START', {
    method: 'POST'
  });
  const result = await response.json();
  console.log('推送结果:', result);
}
```

### 方式4：Python脚本

```python
import httpx
import asyncio

async def push_event():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            'http://localhost:8000/api/feishu/push-event/STOCK_RESEARCH_START'
        )
        print(response.json())

asyncio.run(push_event())
```

## STOCK_RESEARCH_START 卡片内容

用户将在飞书收到包含以下内容的卡片:

```
🚀 股票研究开始
时间: 2026-03-17 01:52

请选择研究方式:
[输入股票代码] [查看持仓] [查看关注]
[打开主菜单]

事件ID: STOCK_RESEARCH_START
```

## 注意事项

1. **必须先建立会话**：用户需要先在飞书给机器人发送一条消息
2. **后端服务运行中**：确保 `python backend/main.py` 正在运行
3. **机器人权限配置**：确保机器人有发送消息的权限

## 扩展新事件

如需添加新的事件推送,参考文档:
- 完整文档: `docs/pegbot_event_push.md`
- 代码位置: `backend/services/feishu_card_service.py`
- API路由: `backend/routers/feishu.py`

## 相关功能

- 📱 卡片使用: `docs/pegbot_card_usage.md`
- 📊 持仓关注查询: `docs/pegbot_holdings_watchlist_query.md`
- 🚀 事件推送: `docs/pegbot_event_push.md`
