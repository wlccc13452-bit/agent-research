# 飞书卡片表单数据修复报告

## 问题根源

从日志中发现，用户点击按钮后，后端收到的 `form_data` 为 `None`：

```
09:58:08 - WARNING - [DIAG] form_data attribute: None (type: <class 'NoneType'>)
09:58:08 - WARNING - [DIAG] No valid form_data found, using empty dict
09:58:08 - WARNING - [ACTION_INVALID] confirm_create_price_alert: 价格提醒需提供股票代码和至少一个阈值
```

**根本原因**：卡片结构不符合飞书 Schema 2.0 的表单绑定规范，导致表单数据无法正确传递。

## 修复方案

### 1. 建立 Form 强绑定（核心修改）

**修改前**：
```json
{
  "body": {
    "elements": [
      {"tag": "input", "name": "stock_code", ...},
      {"tag": "input", "name": "ref_price", ...},
      {"tag": "button", "value": {"action": "confirm_create_price_alert"}, ...}
    ]
  }
}
```

**修改后**：
```json
{
  "body": {
    "elements": [
      {
        "tag": "form",
        "name": "price_alert_form",
        "elements": [
          {"tag": "input", "name": "stock_code_input", "input_type": "text", ...},
          {"tag": "input", "name": "ref_price", "input_type": "text", ...},
          {
            "tag": "action",
            "actions": [{
              "tag": "button",
              "action_type": "form_submit",
              "value": {"action": "confirm_create_price_alert"},
              ...
            }]
          }
        ]
      }
    ]
  }
}
```

### 2. 核心修改点

#### A. Form 容器包裹
- ✅ 所有 `input` 组件和提交按钮必须包裹在同一个 `{"tag": "form", "name": "..."}` 容器内
- ✅ **严禁**在 `form` 内部使用 `column_set` 或 `actions` 标签包裹 `input` 或 `button`
- ✅ 布局美观服从 form 嵌套结构

#### B. 提交动作声明
- ✅ 提交按钮必须包含 `"action_type": "form_submit"`
- ✅ 按钮的 `value` 必须包含后端识别的 `action` 标识

#### C. 属性白名单校验
- ✅ 所有 `input` 组件必须有 `name` 属性（后端获取数据的 Key）
- ✅ 所有 `input` 组件的 `input_type` 必须强制设为 `"text"`（禁止使用 `number`）

#### D. Schema 2.0 结构
- ✅ 最外层有 `"schema": "2.0"`
- ✅ 所有内容位于 `"body": {"elements": [...]}` 路径下

### 3. 修改文件清单

#### A. 卡片构建器（price_alert_cards.py）

**修改的方法**：
1. `create_monitor_config_card()` - 价格提醒配置卡片
   - 添加 `form` 容器包裹所有输入组件
   - 支持 `stock_select`（下拉选择）和 `stock_code_input`（手动输入）
   - 添加 `input_type="text"` 到所有 input 组件
   - 提交按钮添加 `action_type="form_submit"`

2. `create_price_alert_card()` - 价格提醒卡片
   - 添加 `form` 容器包裹
   - 所有 input 组件添加 `input_type="text"`
   - 提交按钮添加 `action_type="form_submit"`

3. `create_monitor_setup_card()` - 监控设置卡片
   - 添加 `form` 容器包裹
   - 所有 input 组件添加 `input_type="text"`
   - 提交按钮添加 `action_type="form_submit"`

#### B. 卡片构建器（menu_cards.py）

**修改的方法**：
1. `create_monitor_setup_card()` - 监控设置卡片
   - 添加 `form` 容器包裹
   - 所有 input 组件添加 `input_type="text"`
   - 提交按钮添加 `action_type="form_submit"`

#### C. 业务逻辑处理（stock_business_service.py）

**修改的方法**：
1. `_handle_price_alert_submission()` - 价格提醒提交处理
   - 支持多来源获取股票代码：
     - `stock_select`（下拉选择）
     - `stock_code_input`（手动输入）
     - `stock_code`（兼容旧字段）
   - 支持多种字段名的兼容处理：
     - `change_rate`（涨跌幅阈值）
     - `ref_price`（参考价格）
   - 添加详细的字段提取逻辑和日志

### 4. 验证方法

#### A. 前端验证
1. 发送 `/start` 命令打开主菜单
2. 点击"价格提醒" → "Create Alert" 或 "Create Monitor"
3. 填写表单：
   - 从下拉列表选择股票 或 手动输入股票代码
   - 填写涨跌幅阈值 或 目标价格
   - 点击"Confirm"或"Create Alert"按钮

#### B. 后端日志验证
期望看到以下日志：

```
✅ 成功情况：
[DIAG] action_data.value: {'action': 'confirm_create_price_alert'}
[DIAG] form_data attribute: {'stock_select': '000001', 'ref_price': '15.5', ...}
[OK] Card sent successfully

❌ 失败情况（修复前）：
[DIAG] form_data attribute: None (type: <class 'NoneType'>)
[WARNING] No valid form_data found
[ACTION_INVALID] 价格提醒需提供股票代码和至少一个阈值
```

#### C. 功能测试
- ✅ 下拉选择股票能够正确传递股票代码
- ✅ 手动输入股票代码能够正确传递
- ✅ 所有输入字段（涨跌幅、参考价格、备注）都能正确传递
- ✅ 表单提交后能正确创建价格提醒

### 5. 兼容性说明

#### A. 字段名称映射

| 功能 | 新字段名 | 旧字段名 | 说明 |
|------|---------|---------|------|
| 股票选择 | `stock_select` | - | 下拉选择 |
| 股票输入 | `stock_code_input` | `stock_code` | 手动输入 |
| 参考价格 | `ref_price` | - | 可选 |
| 涨幅阈值 | `change_up_pct` | - | 可选 |
| 跌幅阈值 | `change_down_pct` | - | 可选 |
| 涨跌幅阈值 | `change_rate` | - | 上下涨跌幅相同 |
| 目标价格 | `target_price` | - | 可选 |
| 备注 | `notes` | - | 可选 |

#### B. 后端兼容处理

```python
# 优先级：stock_select > stock_code_input > stock_code
stock_code = form_data.get('stock_select', '').strip()
if not stock_code:
    stock_code = form_data.get('stock_code_input', '').strip()
if not stock_code:
    stock_code = form_data.get('stock_code', '').strip()

# 兼容 change_rate 字段
if change_rate and not change_up_decimal and not change_down_decimal:
    rate_decimal = Decimal(change_rate)
    change_up_decimal = rate_decimal
    change_down_decimal = rate_decimal
```

### 6. 技术要点总结

#### 飞书 Schema 2.0 表单绑定规范（重要）

1. **必须包裹在 form 标签内**：
   ```json
   {"tag": "form", "name": "form_name", "elements": [...]}
   ```

2. **提交按钮必须有 action_type**：
   ```json
   {"tag": "button", "action_type": "form_submit", "value": {"action": "..."}}
   ```

3. **input 组件必须指定 input_type**：
   ```json
   {"tag": "input", "input_type": "text", "name": "field_name"}
   ```

4. **禁止在 form 内使用 column_set 或 actions**：
   - ❌ 错误：`form > column_set > column > input`
   - ✅ 正确：`form > input`

5. **按钮必须通过 action 标签包裹**：
   ```json
   {
     "tag": "action",
     "actions": [
       {"tag": "button", "action_type": "form_submit", ...},
       {"tag": "button", ...}
     ]
   }
   ```

### 7. 相关文档

- [飞书卡片开发指南 - 表单组件](https://open.feishu.cn/document/ukTMukTMukTM/ucTM5YjL3ETO24yNxkjN)
- [飞书卡片 Schema 2.0 规范](https://open.feishu.cn/document/ukTMukTMukTM/uYjNwUjL2YDM14iN2ATN)
- [飞书机器人交互指南](https://open.feishu.cn/document/ukTMukTMukTM/uYjNwUjL2YDM14iN2ATN)

### 8. 后续优化建议

1. **统一字段命名**：
   - 建议统一使用 `stock_code` 作为股票代码字段名
   - 通过后端逻辑判断是下拉选择还是手动输入

2. **表单验证增强**：
   - 前端添加输入格式校验（如股票代码格式）
   - 后端添加更详细的错误提示

3. **用户体验优化**：
   - 添加加载状态提示
   - 表单提交后显示确认信息
   - 支持表单数据缓存（避免重复输入）

4. **测试覆盖**：
   - 添加单元测试验证表单数据传递
   - 添加集成测试验证完整流程

---

**修复时间**: 2026-03-22
**修复版本**: v1.0
**修复人员**: CodeBuddy AI Assistant
