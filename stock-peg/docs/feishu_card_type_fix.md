# 飞书卡片错误码200671最终修复方案

## 问题根源

**错误码**: 200671  
**根本原因**: 卡片JSON格式错误 - 使用了不正确的混合格式

### 具体问题

1. ❌ **错误的混合格式**:
```json
{
  "type": "template",        // ❌ 有type字段
  "config": {...},
  "elements": [...]
  // ❌ 但没有template_id
}
```

2. ✅ **正确的内联卡片格式**:
```json
{
  "config": {...},
  "elements": [...]
  // ✅ 直接发送卡片内容，不需要type字段
}
```

## 飞书卡片消息格式说明

### 格式1: 内联卡片（推荐）

直接发送完整的卡片JSON：

```json
{
  "config": {
    "wide_screen_mode": true
  },
  "elements": [
    {
      "tag": "div",
      "text": {
        "tag": "lark_md",
        "content": "**标题**"
      }
    },
    {
      "tag": "action",
      "actions": [
        {
          "tag": "button",
          "name": "btn_action",
          "text": {"tag": "plain_text", "content": "按钮"},
          "type": "primary",
          "value": {"action": "test"}
        }
      ]
    }
  ]
}
```

### 格式2: 模板卡片（需要template_id）

使用预定义的模板：

```json
{
  "type": "template",
  "data": {
    "template_id": "YOUR_TEMPLATE_ID",
    "template_variable": {
      "title": "标题",
      "content": "内容"
    }
  }
}
```

**注意**: 如果使用模板，必须提供有效的 `template_id`！

## 修复内容

### 修复前 ❌

所有卡片都包含错误的结构：

```python
card = {
    "type": "template",      # ❌ 错误
    "data": {...},          # ❌ 多余
    "config": {...},
    "elements": [...]
}
```

### 修复后 ✅

移除了 `type` 和 `data` 字段：

```python
card = {
    "config": {...},
    "elements": [...]
}
```

## 受影响的卡片

已修复所有卡片定义：

1. ✅ 主菜单卡片
2. ✅ 股票查询卡片
3. ✅ 行情结果卡片
4. ✅ 技术分析卡片
5. ✅ 基本面分析卡片
6. ✅ 错误提示卡片
7. ✅ 持仓管理卡片
8. ✅ 添加股票卡片
9. ✅ 关注列表卡片
10. ✅ 价格提醒卡片
11. ✅ STOCK_RESEARCH_START事件卡片

## Button组件规范

同时修复了button组件缺失name属性的问题：

```json
{
  "tag": "button",
  "name": "btn_action",        // ✅ 必填
  "text": {
    "tag": "plain_text",
    "content": "按钮文本"
  },
  "type": "primary",
  "value": {
    "action": "test"
  }
}
```

## 部署步骤

### 1. 重启后端服务

**重要**: 必须重启服务才能加载新代码！

```bash
# 停止当前服务 (Ctrl+C)
# 然后重新启动
cd d:/2026projects/stocks-research/stock-peg
python backend/main.py
```

### 2. 验证修复

```bash
curl -X POST http://localhost:8000/api/feishu/push-event/STOCK_RESEARCH_START
```

### 3. 预期响应

成功：
```json
{
  "status": "ok",
  "message": "Event card STOCK_RESEARCH_START sent successfully",
  "event_id": "STOCK_RESEARCH_START",
  "chat_id": "oc_xxxxx"
}
```

失败（如果仍有错误）：
```json
{
  "detail": "发送卡片失败: 错误码200671"
}
```

## 常见问题

### Q1: 修改后仍然报200671错误？

**A**: 请确保：
1. 已重启后端服务
2. 使用的是最新代码
3. 检查飞书机器人权限配置

### Q2: 如何查看实际发送的JSON？

**A**: 在 `_send_card_message` 方法中添加日志：

```python
logger.info(f"Sending card: {json.dumps(card, ensure_ascii=False, indent=2)}")
```

### Q3: 是否需要重新配置飞书机器人？

**A**: 不需要，只需确保机器人有发送消息的权限即可。

## 相关文档

- [Button组件规范](./feishu_card_button_specification.md)
- [事件推送使用指南](./pegbot_event_push.md)
- [飞书官方文档](https://open.feishu.cn/document/server-docs/im-v1/message/create)

## 更新日志

- **2026-03-17 02:00**: 修复button缺少name属性问题
- **2026-03-17 02:10**: 移除错误的type字段，使用正确的内联卡片格式
