# 飞书卡片重构 - 修复手机端 200671 错误

**日期**: 2026-03-17
**任务**: 根据飞书最新规范重构 feishu_card_service.py，修复手机端 200671 错误

## 问题根源

飞书卡片在手机端报 200671 错误（卡片 JSON 校验失败），主要问题：

1. **Input Label 格式错误**: 使用了 `{"tag": "plain_text", "content": "..."}` 对象结构，应该直接使用字符串
2. **Button Value 嵌套过深**: 包含不必要的 `form` 字段嵌套
3. **冗余字段**: `_ensure_button_names` 函数添加不必要的 `name` 字段
4. **缺少 Header**: 卡片没有规范的 header 部分

## 解决方案

### 1. 移除 `_ensure_button_names` 函数

- 删除了 `_ensure_button_names` 函数定义（原第 28-54 行）
- 移除了 `_send_card_message` 方法中对该函数的调用（原第 835 行）
- 原因：飞书 API 已不强制要求按钮必须有 `name` 字段

### 2. 修正 Input Label 格式

将所有 input 组件的 label 从对象结构改为字符串：

```python
# 修改前
{
    "tag": "input",
    "name": "stock_code",
    "label": {
        "tag": "plain_text",
        "content": "股票代码"
    }
}

# 修改后
{
    "tag": "input",
    "name": "stock_code",
    "label": "股票代码"
}
```

共修改了 **13 个 input 组件**。

### 3. 简化 Button Value 字段

移除了 `form` 字段嵌套，只保留必要的 action 字段：

```python
# 修改前
{
    "tag": "button",
    "value": {
        "action": "query_stock",
        "form": "stock_query"  # 冗余字段
    }
}

# 修改后
{
    "tag": "button",
    "value": {
        "action": "query_stock"
    }
}
```

### 4. 添加规范 Header

给所有卡片添加了 header 部分，包含 template 和 title：

```python
{
    "config": {"wide_screen_mode": True},
    "header": {
        "template": "blue",  # 不同类型卡片使用不同颜色
        "title": {
            "tag": "plain_text",
            "content": "📊 PegBot 股票查询"
        }
    },
    "elements": [...]
}
```

共添加了 **14 个卡片 header**，使用了不同的 template 颜色：
- `blue`: 主要功能卡片
- `purple`: 技术分析卡片
- `green`: 基本面分析卡片
- `red`: 错误卡片
- `orange`: 价格提醒卡片

### 5. 处理 None 值格式化问题

修复了可能导致 JSON 损坏的 None 值格式化问题：

```python
# 修改前（可能出错）
f"**最新价**\n💰 {quote.get('price', 0):.2f}"

# 修改后（安全）
price = quote.get('price', 0) or 0
f"**最新价**\n💰 {price:.2f}"
```

关键修改：
- `_create_quote_result_card`: 处理了 7 个可能的 None 值
- `_create_fundamental_result_card`: 处理了 8 个可能的 None 值

### 6. 确保 JSON 编码正确

确认 `json.dumps` 使用了 `ensure_ascii=False`，避免中文编码问题：

```python
card_json_str = json.dumps(card, ensure_ascii=False)
```

## 验证结果

创建了独立验证脚本 `test/temp/validate_card_standalone.py`，验证结果：

```
[PASS] _ensure_button_names 函数已移除
[PASS] _ensure_button_names 调用已移除
[PASS] 所有 13 个 input.label 都是字符串格式
[PASS] 所有 button.value 已简化（无 form 字段）
[PASS] 发现 14 个卡片有 header.template
[PASS] json.dumps 使用了 ensure_ascii=False
[PASS] 已处理所有可能的 None 值格式化问题

[SUCCESS] 所有卡片符合飞书最新规范！
```

## 修改的卡片列表

1. `_create_stock_query_card` - 股票查询卡片
2. `_create_quote_result_card` - 实时行情结果卡片
3. `_create_technical_result_card` - 技术分析结果卡片
4. `_create_fundamental_result_card` - 基本面分析结果卡片
5. `_create_error_card` - 错误卡片
6. `_create_holdings_menu_card` - 持仓管理菜单卡片
7. `_create_add_stock_to_holdings_card` - 添加股票到持仓卡片
8. `_create_watchlist_menu_card` - 关注列表管理菜单卡片
9. `_create_add_to_watchlist_card` - 添加到关注列表卡片
10. `_create_price_alert_menu_card` - 价格提醒菜单卡片
11. `_create_price_alert_card` - 创建价格提醒卡片
12. `_create_price_query_card` - 价格查询卡片
13. `_create_main_menu_card` - 主菜单卡片
14. `_create_stock_research_start_card` - 股票研究开始事件卡片

## 技术要点

1. **飞书卡片最新规范**:
   - Input label 必须是字符串，不能是对象
   - Button value 建议使用简单的 dict，避免嵌套
   - 建议添加 header 部分，提升卡片视觉效果
   - 确保 `ensure_ascii=False` 避免中文编码问题

2. **None 值处理**:
   - 使用 `or 0` 模式处理可能的 None 值
   - 避免直接对可能为 None 的值进行格式化

3. **验证方法**:
   - 创建独立的验证脚本，不依赖模块导入
   - 使用正则表达式检查关键结构
   - 自动统计问题数量

## 相关文件

- `backend/services/feishu_card_service.py` - 主要修改文件
- `test/temp/validate_card_standalone.py` - 验证脚本
- `test/temp/validate_card_refactor_v2.py` - 完整验证脚本（需要模块导入）

## 后续建议

1. 在发送卡片前，使用验证脚本检查 JSON 结构
2. 监控飞书 API 返回的错误码，及时调整卡片结构
3. 定期查阅飞书官方文档，了解最新规范变化
