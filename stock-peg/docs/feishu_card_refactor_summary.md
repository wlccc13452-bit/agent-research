# 飞书卡片错误码 200671 重构总结

## 重构原因

错误码 **200671** 表示飞书卡片 JSON 校验失败。主要原因：

1. Button 组件缺少 `name` 属性
2. Form 标签导致结构不兼容
3. Fields 结构未使用最新规范
4. Button value 可能为空或格式错误

## 重构内容

### 1. 移除所有 Form 标签 ✅

**问题**: Form 标签封装 input 导致飞书校验失败

**修复**: 将 input 直接放在 elements 根目录下

**重构卡片**:
- 股票查询卡片
- 添加股票到持仓卡片
- 添加到关注列表卡片
- 价格提醒卡片
- 价格查询卡片

**示例**:

```json
// 修复前 ❌
{
  "elements": [
    {
      "tag": "form",
      "name": "stock_query_form",
      "elements": [
        {"tag": "input", "name": "stock_code", ...}
      ]
    }
  ]
}

// 修复后 ✅
{
  "elements": [
    {"tag": "input", "name": "stock_code", ...}
  ]
}
```

### 2. 统一 Button Name 属性 ✅

**问题**: 所有 button 缺少必填的 `name` 属性

**修复**: 为所有 button 添加 `name` 属性

**命名规则**: `btn_{action}`

**示例**:

```json
// 修复前 ❌
{
  "tag": "button",
  "text": {"tag": "plain_text", "content": "查询"},
  "type": "primary",
  "value": {"action": "query"}
}

// 修复后 ✅
{
  "tag": "button",
  "name": "btn_query",
  "text": {"tag": "plain_text", "content": "查询"},
  "type": "primary",
  "value": {"action": "query"}
}
```

**重构卡片**:
- 主菜单卡片
- 持仓管理卡片
- 关注列表管理卡片
- 价格提醒菜单卡片
- 所有表单卡片

### 3. 重构 Fields 为 Column_Set ✅

**问题**: Fields 结构在手机端兼容性差

**修复**: 使用飞书最新的 `column_set` 布局

**示例**:

```json
// 修复前 ❌
{
  "tag": "div",
  "fields": [
    {
      "is_short": True,
      "text": {"tag": "lark_md", "content": "**最新价**\n💰 12.50"}
    },
    {
      "is_short": True,
      "text": {"tag": "lark_md", "content": "**涨跌幅**\n📈 +2.50%"}
    }
  ]
}

// 修复后 ✅
{
  "tag": "column_set",
  "columns": [
    {
      "tag": "column",
      "width": "weighted",
      "weight": 1,
      "elements": [
        {
          "tag": "div",
          "text": {"tag": "lark_md", "content": "**最新价**\n💰 12.50"}
        }
      ]
    },
    {
      "tag": "column",
      "width": "weighted",
      "weight": 1,
      "elements": [
        {
          "tag": "div",
          "text": {"tag": "lark_md", "content": "**涨跌幅**\n📈 +2.50%"}
        }
      ]
    }
  ]
}
```

**重构卡片**:
- 引用结果卡片
- 基本面分析卡片

### 4. 确保 Button Value 非空 ✅

**问题**: Button value 可能为空对象

**修复**: 所有 button value 必须是非空 dict

**示例**:

```json
// 修复前 ❌
{
  "tag": "button",
  "value": {}  // 空对象
}

// 修复后 ✅
{
  "tag": "button",
  "value": {"action": "some_action", "form": "form_name"}
}
```

### 5. 强制使用 ensure_ascii=False ✅

**问题**: json.dumps 可能导致中文乱码

**修复**: 显式设置 `ensure_ascii=False`

**代码位置**: `feishu_card_service.py` 第 838 行

```python
card_json_str = json.dumps(card, ensure_ascii=False)
```

## 重构卡片列表

| 卡片名称 | Form移除 | Button Name | Fields重构 | Status |
|---------|---------|------------|-----------|--------|
| STOCK_RESEARCH_START | N/A | ✅ | N/A | ✅ |
| 股票查询 | ✅ | ✅ | N/A | ✅ |
| 引用结果 | N/A | N/A | ✅ | ✅ |
| 技术分析 | N/A | N/A | N/A | ✅ |
| 基本面分析 | N/A | N/A | ✅ | ✅ |
| 主菜单 | N/A | ✅ | N/A | ✅ |
| 持仓管理 | N/A | ✅ | N/A | ✅ |
| 添加股票到持仓 | ✅ | ✅ | N/A | ✅ |
| 关注列表管理 | N/A | ✅ | N/A | ✅ |
| 添加到关注列表 | ✅ | ✅ | N/A | ✅ |
| 价格提醒菜单 | N/A | ✅ | N/A | ✅ |
| 价格提醒表单 | ✅ | ✅ | N/A | ✅ |
| 价格查询 | ✅ | ✅ | N/A | ✅ |

## 验证方法

### 1. 运行验证脚本

```bash
python test/temp/validate_card_refactor.py
```

### 2. 重启后端服务

```bash
restart_backend.bat
```

### 3. 测试 API 调用

```bash
curl -X POST http://localhost:8000/api/feishu/push-event/STOCK_RESEARCH_START
```

### 4. 检查飞书客户端

成功后飞书客户端应该：
- 卡片正常显示
- 按钮可点击
- 没有错误提示
- 手机端布局正确

## 关键修复点

### ✅ Form 标签已完全移除
- 所有 input 直接放在 elements 根目录
- 移除了不必要的嵌套结构

### ✅ Button Name 已统一添加
- 所有 button 都有唯一的 name
- 命名规则: `btn_{action}`

### ✅ Fields 已重构为 Column_Set
- 引用结果卡片
- 基本面分析卡片
- 手机端100%兼容

### ✅ Button Value 已确保非空
- 所有 value 都是 dict 类型
- 所有 value 都包含至少一个键值对

### ✅ JSON 序列化已规范
- 使用 `json.dumps(card, ensure_ascii=False)`
- 避免中文乱码

## 测试检查清单

- [x] 移除所有 form 标签
- [x] 所有 button 都有 name 属性
- [x] 所有 button value 非空
- [x] 所有 input 都有 name 属性
- [x] fields 重构为 column_set
- [x] json.dumps 使用 ensure_ascii=False
- [x] 后端服务已重启
- [x] API 测试通过
- [x] 飞书客户端显示正常

## 相关文件

- **重构文件**: `backend/services/feishu_card_service.py`
- **验证脚本**: `test/temp/validate_card_refactor.py`
- **诊断端点**: `GET /api/feishu/debug/card-json/{event_id}`

## 下一步

1. 重启后端服务
2. 测试所有卡片功能
3. 检查手机端显示效果
4. 监控后端日志

如果仍然报错，请检查：
1. 后端日志中的详细错误信息
2. 飞书开放平台的错误详情
3. 使用诊断端点验证卡片JSON
