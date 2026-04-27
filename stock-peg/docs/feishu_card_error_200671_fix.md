# 飞书卡片错误码200671修复报告

## 问题描述

**错误码**: 200671  
**错误原因**: 飞书卡片消息JSON格式错误  
**具体问题**: button组件缺少必填的`name`属性

## 修复方案

### 1. 添加自动修复函数

在 `backend/services/feishu_card_service.py` 中添加了 `_ensure_button_names` 方法:

```python
def _ensure_button_names(self, card: dict[str, Any]) -> dict[str, Any]:
    """
    Ensure all button elements have name attribute
    
    Args:
        card: Card JSON structure
        
    Returns:
        Card with all buttons having name attribute
    """
    if "elements" not in card:
        return card
    
    btn_counter = 0
    for element in card["elements"]:
        if element.get("tag") == "action" and "actions" in element:
            for action in element["actions"]:
                if action.get("tag") == "button" and "name" not in action:
                    btn_counter += 1
                    # Generate name from action value
                    action_value = action.get("value", {}).get("action", "")
                    if action_value:
                        action["name"] = f"btn_{action_value}"
                    else:
                        action["name"] = f"btn_{btn_counter}"
    
    return card
```

### 2. 在发送前自动应用修复

修改 `_send_card_message` 方法:

```python
async def _send_card_message(self, chat_id: str, card: dict[str, Any]) -> bool:
    """Send card message to chat"""
    try:
        # Ensure all buttons have name attribute (required by Feishu API)
        card = self._ensure_button_names(card)
        
        # ... rest of the code
```

## 修复效果

### 修复前

```json
{
  "tag": "button",
  "text": {"tag": "plain_text", "content": "查看持仓"},
  "type": "primary",
  "value": {"action": "view_holdings"}
}
```

### 修复后

```json
{
  "tag": "button",
  "name": "btn_view_holdings",
  "text": {"tag": "plain_text", "content": "查看持仓"},
  "type": "primary",
  "value": {"action": "view_holdings"}
}
```

## 验证结果

**测试时间**: 2026-03-17 02:00

**API测试**:
```bash
curl -X POST http://localhost:8000/api/feishu/push-event/STOCK_RESEARCH_START
```

**响应**:
```json
{
  "status": "ok",
  "message": "Event card STOCK_RESEARCH_START sent successfully",
  "event_id": "STOCK_RESEARCH_START",
  "chat_id": "oc_2e96d78e081c89b7e9b3677cf53d07cf"
}
```

**状态码**: 200 ✅  
**错误码200671**: 已解决 ✅

## 飞书卡片按钮规范

根据飞书最新卡片规范,button组件必须包含以下属性:

### 必填属性

1. **tag**: "button"
2. **name**: 按钮唯一标识（用于回调识别）
3. **text**: 按钮显示文本
4. **type**: 按钮类型 (primary/default/danger)

### 可选属性

5. **value**: 回调时携带的数据（JSON对象）
6. **url**: 跳转链接
7. **confirm**: 确认弹窗配置

### 完整示例

```json
{
  "tag": "button",
  "name": "btn_view_holdings",
  "text": {
    "tag": "plain_text",
    "content": "查看持仓"
  },
  "type": "primary",
  "value": {
    "action": "view_holdings",
    "event": "STOCK_RESEARCH_START"
  }
}
```

## 受影响的卡片

所有包含button组件的卡片都已自动修复:

1. ✅ 主菜单卡片
2. ✅ 股票查询卡片
3. ✅ 持仓管理卡片
4. ✅ 关注列表卡片
5. ✅ 价格提醒卡片
6. ✅ STOCK_RESEARCH_START 事件卡片

## 注意事项

1. **name属性格式**: 建议使用 `btn_{action}` 格式，便于调试
2. **唯一性**: 同一卡片内的button name应该唯一
3. **向后兼容**: 修复函数不会覆盖已存在的name属性
4. **自动应用**: 所有卡片发送前都会自动检查和修复

## 相关文档

- 飞书官方文档: https://open.feishu.cn/document/client-docs/bot-v1/events-and-callbacks
- 卡片消息格式: https://open.feishu.cn/document/server-docs/im-v1/message/create

## 更新日志

- **2026-03-17**: 修复错误码200671，添加自动修复函数
