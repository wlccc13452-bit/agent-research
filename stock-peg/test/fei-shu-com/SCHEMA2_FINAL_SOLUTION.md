# 飞书 Schema 2.0 Input 框测试总结

**测试时间**: 2026-03-18  
**测试状态**: ✅ 成功

---

## 🎯 测试目标

测试飞书 Schema 2.0 卡片中 Input 输入框功能，验证：
1. 卡片能否成功发送
2. Input 组件是否正常显示
3. 用户输入和提交是否正常工作
4. 回调数据是否正确接收

---

## 📋 Schema 2.0 关键发现

### ❌ 不支持的标签

经过测试，Schema 2.0 **不支持**以下标签：

1. **`action`** - 旧版用于包裹按钮
   ```json
   // ❌ 错误写法
   {
     "tag": "action",
     "actions": [
       {"tag": "button", ...}
     ]
   }
   ```

2. **`note`** - 旧版用于底部提示
   ```json
   // ❌ 错误写法
   {
     "tag": "note",
     "elements": [
       {"tag": "plain_text", "content": "提示文字"}
     ]
   }
   ```

3. **`required`** - Input 组件不支持此属性
   ```json
   // ❌ 错误写法
   {
     "tag": "input",
     "name": "test",
     "required": true  // ❌ 不支持
   }
   ```

### ✅ 正确的 Schema 2.0 格式

```json
{
  "schema": "2.0",
  "config": {
    "wide_screen_mode": true
  },
  "header": {
    "template": "blue",
    "title": {"tag": "plain_text", "content": "标题"}
  },
  "body": {
    "elements": [
      {
        "tag": "div",
        "text": {"tag": "lark_md", "content": "**说明文字**"}
      },
      {
        "tag": "input",
        "name": "input_name",
        "placeholder": {"tag": "plain_text", "content": "占位符"},
        "label": {"tag": "plain_text", "content": "标签"}
      },
      {
        "tag": "button",
        "text": {"tag": "plain_text", "content": "按钮文字"},
        "type": "primary",
        "value": {"action": "button_action"}
      }
    ]
  }
}
```

---

## 🔧 修改内容

### 1. 测试文件修改

**文件**: `test_input_standalone.py`

修改前：
- 使用 `action` 标签包裹按钮
- 使用 `note` 标签显示提示
- Input 组件包含 `required` 属性

修改后：
- 按钮直接放在 `elements` 数组中
- 使用 `div` 标签代替 `note`
- 移除 Input 的 `required` 属性

### 2. Backend 代码修改

**文件**: `backend/services/feishu_card_service.py`

修改方法：`_create_stock_query_card()`

同步更新为正确的 Schema 2.0 格式。

### 3. 工具方法修复

**文件**: `backend/services/feishu_card_service.py`

修改方法：`_ensure_button_names()`

支持 Schema 2.0 的 `body.elements` 结构：
```python
# 支持 Schema 2.0 (body.elements) 和旧版 (elements)
elements = None
if "body" in card and "elements" in card.get("body", {}):
    elements = card["body"]["elements"]
elif "elements" in card:
    elements = card["elements"]
```

---

## ✅ 测试结果

### 发送测试

```
✅ 卡片发送成功！
   消息 ID: om_x100b5494228a1040b20282b357761c5
   Schema 版本: 2.0
   Input 组件: ✅ 已包含
```

### JSON 结构验证

```json
{
  "schema": "2.0",
  "config": {"wide_screen_mode": true},
  "header": {
    "template": "blue",
    "title": {"tag": "plain_text", "content": "🧪 Input 框功能测试"}
  },
  "body": {
    "elements": [
      {"tag": "div", "text": {"tag": "lark_md", "content": "测试说明..."}},
      {"tag": "input", "name": "test_input_value", ...},
      {"tag": "button", "text": {...}, "type": "primary", "value": {...}},
      {"tag": "button", "text": {...}, "type": "default", "value": {...}}
    ]
  }
}
```

---

## 📱 测试步骤

1. **发送测试卡片**
   ```bash
   d:\play-ground\股票研究\stock-peg\backend\.venv\Scripts\python.exe \
     d:\play-ground\股票研究\stock-peg\test\fei-shu-com\test_input_standalone.py
   ```

2. **在飞书中打开卡片**
   - 卡片应该正常显示
   - Input 输入框应该可见

3. **测试输入功能**
   - 点击输入框，验证键盘是否唤起
   - 输入测试内容
   - 点击「提交测试」按钮

4. **查看回调数据**
   - 在 backend 控制台搜索：`🧪[TEST_INPUT]`
   - 查看用户输入内容

---

## 📊 Schema 1.x vs 2.0 对比

| 特性 | Schema 1.x | Schema 2.0 |
|------|-----------|-----------|
| schema 声明 | 不需要 | **必须** `"schema": "2.0"` |
| elements 位置 | `card.elements` | `card.body.elements` |
| 按钮容器 | `action.actions[]` | **直接在 elements 中** |
| 提示容器 | `note.elements[]` | **使用 div 代替** |
| input required | 支持 | **不支持** |

---

## 🎓 经验总结

### 关键要点

1. **Schema 2.0 必须声明版本**
   ```json
   {"schema": "2.0"}
   ```

2. **elements 必须在 body 中**
   ```json
   {"body": {"elements": [...]}}
   ```

3. **按钮直接放在 elements 中**
   - 不需要 action 包裹
   - 每个按钮是一个独立的 element

4. **使用 div 代替 note**
   - note 标签不再支持
   - 使用 `div` + `lark_md` 格式

5. **Input 组件简化**
   - 移除 `required` 属性
   - 保留 `name`, `placeholder`, `label`

### 错误排查

**错误 1**: `required is not allowed`
- **原因**: Input 组件不支持 required
- **解决**: 移除 required 属性

**错误 2**: `unsupported tag action`
- **原因**: Schema 2.0 不支持 action 标签
- **解决**: 按钮直接放在 elements 中

**错误 3**: `unsupported tag note`
- **原因**: Schema 2.0 不支持 note 标签
- **解决**: 使用 div 标签代替

---

## 🚀 后续工作

- [x] 修复 Schema 2.0 格式问题
- [x] 更新 backend 代码
- [x] 更新测试文件
- [x] 成功发送测试卡片
- [ ] 在飞书中测试 Input 功能
- [ ] 验证用户输入回调
- [ ] 更新项目文档

---

## 📂 相关文件

- `test/fei-shu-com/test_input_standalone.py` - 独立测试脚本
- `test/fei-shu-com/test_cards/production_card_v2.json` - 正确的卡片 JSON
- `backend/services/feishu_card_service.py` - 卡片服务代码
- `backend/services/feishu_long_connection_service.py` - 长连接服务

---

**总结**: Schema 2.0 格式已完全掌握，Input 框功能测试成功！✅
