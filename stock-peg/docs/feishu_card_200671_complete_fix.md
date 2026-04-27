# 飞书卡片错误码 200671 完整修复方案

## 错误原因

错误码 **200671** 表示卡片 JSON 格式不符合飞书规范。常见原因：

### 1. Button 组件缺少 `name` 属性 ✅ 已修复

**错误写法**：
```json
{
  "tag": "button",
  "text": {"tag": "plain_text", "content": "查询"},
  "type": "primary",
  "value": {"action": "query"}
}
```

**正确写法**：
```json
{
  "tag": "button",
  "name": "btn_query",  // 必填！
  "text": {"tag": "plain_text", "content": "查询"},
  "type": "primary",
  "value": {"action": "query"}
}
```

### 2. Input 组件缺少 `name` 属性 ✅ 已检查

**错误写法**：
```json
{
  "tag": "input",
  "placeholder": {"tag": "plain_text", "content": "输入股票代码"},
  "label": {"tag": "plain_text", "content": "股票代码"}
}
```

**正确写法**：
```json
{
  "tag": "input",
  "name": "stock_code",  // 必填！
  "placeholder": {"tag": "plain_text", "content": "输入股票代码"},
  "label": {"tag": "plain_text", "content": "股票代码"}
}
```

### 3. Button 的 `value` 为空对象 ✅ 已检查

**错误写法**：
```json
{
  "tag": "button",
  "name": "btn_action",
  "text": {"tag": "plain_text", "content": "按钮"},
  "type": "primary",
  "value": {}  // ❌ 空对象
}
```

**正确写法**：
```json
{
  "tag": "button",
  "name": "btn_action",
  "text": {"tag": "plain_text", "content": "按钮"},
  "type": "primary",
  "value": {"action": "some_action"}  // ✅ 非空对象
}
```

### 4. 卡片顶层使用错误的 `type` 字段 ✅ 已修复

**错误写法**：
```json
{
  "type": "template",  // ❌ 内联卡片不应包含此字段
  "config": {"wide_screen_mode": true},
  "elements": [...]
}
```

**正确写法**（内联卡片）：
```json
{
  "config": {"wide_screen_mode": true},  // ✅ 直接从 config 开始
  "elements": [...]
}
```

## 已实施的修复

### 1. 自动修复 Button name 属性

**位置**：`backend/services/feishu_card_service.py`

**修复方法**：
```python
def _ensure_button_names(self, card: dict[str, Any]) -> dict[str, Any]:
    """自动为所有缺少 name 的 button 添加 name"""
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

**调用位置**：
```python
async def _send_card_message(self, chat_id: str, card: dict[str, Any]) -> bool:
    # 发送前自动修复
    card = self._ensure_button_names(card)
    # ... 发送逻辑
```

### 2. 移除所有卡片定义中的 `type: "template"`

已从以下卡片中移除：
- ✅ 主菜单卡片
- ✅ 股票查询卡片
- ✅ 技术分析卡片
- ✅ 基本面分析卡片
- ✅ 持仓管理卡片
- ✅ 关注列表卡片
- ✅ 价格提醒卡片
- ✅ STOCK_RESEARCH_START 事件卡片

## 验证步骤

### 1. 检查修复是否生效

```python
# 运行测试脚本
python test/temp/test_ensure_button_names.py
```

**预期输出**：
```
修复前:
Button 0: 📊 股票查询
  has name: False

修复后:
Button 0: 📊 股票查询
  name: btn_stock_query_menu
```

### 2. 重启后端服务（重要！）

修复代码后**必须重启后端服务**才能生效：

```bash
# 方法1: 使用启动脚本
restart_backend.bat

# 方法2: 手动重启
# 停止现有服务（Ctrl+C）
# 重新启动
python backend/main.py
```

### 3. 测试 API 调用

```bash
# 测试推送 STOCK_RESEARCH_START 事件
curl -X POST http://localhost:8000/api/feishu/push-event/STOCK_RESEARCH_START
```

**成功响应**：
```json
{
  "status": "ok",
  "message": "Event card STOCK_RESEARCH_START sent successfully",
  "event_id": "STOCK_RESEARCH_START",
  "chat_id": "oc_..."
}
```

**失败响应**（如果仍有问题）：
```json
{
  "detail": "发送事件卡片失败: STOCK_RESEARCH_START"
}
```

### 4. 检查飞书客户端

成功后在飞书客户端应该看到：
- 卡片正常显示
- 按钮可点击
- 没有错误提示

## 排查清单

如果仍然报错 200671，请按以下顺序排查：

- [ ] **后端服务已重启**（最常见原因）
- [ ] 所有 button 都有 `name` 属性
- [ ] 所有 button 的 `value` 都是非空对象
- [ ] 所有 input 都有 `name` 属性
- [ ] 卡片顶层没有 `type: "template"`
- [ ] 卡片顶层没有 `data` 字段
- [ ] `json.dumps()` 正确序列化卡片

## 调试工具

### 查看实际发送的 JSON

```python
# 添加日志打印
import json

async def _send_card_message(self, chat_id: str, card: dict[str, Any]) -> bool:
    card = self._ensure_button_names(card)
    
    # 打印最终 JSON
    print("=" * 80)
    print("最终发送的卡片 JSON:")
    print(json.dumps(card, indent=2, ensure_ascii=False))
    print("=" * 80)
    
    # ... 发送逻辑
```

### 验证 Button 格式

```python
# 检查所有 button
for element in card["elements"]:
    if element.get("tag") == "action":
        for action in element["actions"]:
            if action.get("tag") == "button":
                assert "name" in action, "Button 缺少 name 属性"
                assert action.get("value"), "Button value 为空"
                assert isinstance(action["value"], dict), "Button value 不是对象"
                assert len(action["value"]) > 0, "Button value 是空对象"
```

## 参考文档

- [飞书卡片消息开发指南](https://open.feishu.cn/document/client-docs/bot-v1/events-and-callbacks)
- [飞书卡片组件规范](https://open.feishu.cn/document/common-capabilities/sheets/web-sheets-introduction)

## 修复记录

| 日期 | 修复内容 | 状态 |
|------|---------|------|
| 2026-03-17 | 添加 `_ensure_button_names()` 自动修复 | ✅ |
| 2026-03-17 | 移除所有卡片的 `type: "template"` | ✅ |
| 2026-03-17 | 验证所有 input 有 name 属性 | ✅ |
| 2026-03-17 | 验证所有 button value 非空 | ✅ |

## 下一步

如果按照本文档修复后仍然报错，请：

1. 重启后端服务
2. 运行测试脚本验证修复
3. 查看后端日志中的详细错误信息
4. 检查飞书开放平台的错误详情
