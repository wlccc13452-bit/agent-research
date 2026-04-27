# 飞书卡片Button组件规范

## Button组件必填字段

根据飞书最新API规范，所有button组件必须包含以下字段:

### 必填字段清单

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| **tag** | string | 固定值"button" | `"tag": "button"` |
| **name** | string | 按钮唯一标识 | `"name": "btn_view_holdings"` |
| **text** | object | 按钮文本 | `{"tag": "plain_text", "content": "查看持仓"}` |
| **type** | string | 按钮类型 | `"type": "primary"` |

### name字段要求

- **必填性**: 飞书API要求button必须有name字段
- **唯一性**: 同一卡片内的button name应该唯一
- **格式建议**: 使用 `btn_{action}` 格式
- **用途**: 用于回调事件中识别点击的按钮

## 正确的Button示例

### 示例1: 基础按钮

```json
{
  "tag": "button",
  "name": "btn_query_stock",
  "text": {
    "tag": "plain_text",
    "content": "查询股票"
  },
  "type": "primary",
  "value": {
    "action": "query_stock"
  }
}
```

### 示例2: 带事件的按钮

```json
{
  "tag": "button",
  "name": "btn_view_holdings",
  "text": {
    "tag": "plain_text",
    "content": "查看持仓"
  },
  "type": "default",
  "value": {
    "action": "view_holdings",
    "event": "STOCK_RESEARCH_START"
  }
}
```

### 示例3: 多个按钮

```json
{
  "tag": "action",
  "actions": [
    {
      "tag": "button",
      "name": "btn_view_holdings",
      "text": {"tag": "plain_text", "content": "查看持仓"},
      "type": "primary",
      "value": {"action": "view_holdings"}
    },
    {
      "tag": "button",
      "name": "btn_view_watchlist",
      "text": {"tag": "plain_text", "content": "查看关注"},
      "type": "default",
      "value": {"action": "view_watchlist"}
    }
  ]
}
```

## 常见错误

### 错误1: 缺少name字段 ❌

```json
{
  "tag": "button",
  "text": {"tag": "plain_text", "content": "查看持仓"},
  "type": "primary",
  "value": {"action": "view_holdings"}
}
```

**错误码**: 200671  
**错误信息**: JSON格式错误

### 修正后 ✅

```json
{
  "tag": "button",
  "name": "btn_view_holdings",
  "text": {"tag": "plain_text", "content": "查看持仓"},
  "type": "primary",
  "value": {"action": "view_holdings"}
}
```

## 自动修复方案

### 修复函数

```python
def _ensure_button_names(self, card: dict[str, Any]) -> dict[str, Any]:
    """Ensure all button elements have name attribute"""
    if "elements" not in card:
        return card
    
    btn_counter = 0
    for element in card["elements"]:
        if element.get("tag") == "action" and "actions" in element:
            for action in element["actions"]:
                if action.get("tag") == "button" and "name" not in action:
                    btn_counter += 1
                    action_value = action.get("value", {}).get("action", "")
                    if action_value:
                        action["name"] = f"btn_{action_value}"
                    else:
                        action["name"] = f"btn_{btn_counter}"
    
    return card
```

### 使用方法

```python
# 在发送卡片前自动修复
async def _send_card_message(self, chat_id: str, card: dict[str, Any]) -> bool:
    # Ensure all buttons have name attribute
    card = self._ensure_button_names(card)
    
    # Send to Feishu
    # ...
```

## Button类型说明

### primary
- 主要操作按钮
- 显示为蓝色
- 用于最重要的操作

### default
- 默认按钮
- 显示为灰色
- 用于次要操作

### danger
- 危险按钮
- 显示为红色
- 用于删除等危险操作

## Value字段说明

`value`字段用于携带回调数据:

```json
{
  "value": {
    "action": "view_holdings",      // 操作类型
    "event": "STOCK_RESEARCH_START", // 事件ID（可选）
    "stock_code": "000001"          // 其他参数（可选）
  }
}
```

**重要提示**:
- `value`必须是JSON对象
- 不能是字符串或数组
- 可以包含任意自定义数据

## 测试验证

### 测试命令

```bash
curl -X POST http://localhost:8000/api/feishu/push-event/STOCK_RESEARCH_START
```

### 成功响应

```json
{
  "status": "ok",
  "message": "Event card STOCK_RESEARCH_START sent successfully"
}
```

### 失败响应

```json
{
  "detail": "发送卡片失败: 错误码200671"
}
```

## 参考文档

- [飞书卡片消息官方文档](https://open.feishu.cn/document/server-docs/im-v1/message/create)
- [错误码200671修复报告](./feishu_card_error_200671_fix.md)
- [事件推送使用指南](./pegbot_event_push.md)
