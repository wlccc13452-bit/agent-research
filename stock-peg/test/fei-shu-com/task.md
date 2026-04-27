测试目的：改造PegBot卡片功能为button-based布局，取消Input输入功能

测试文件：
- test_input_card.py: Input组件测试（已完成）
- test_button_cards.py: Button-based卡片结构验证（已完成）
- test_send_button_cards.py: 发送实际卡片到飞书测试（已完成）
- restart_and_test.bat: 重启服务并测试（推荐使用）

## 完成情况

### 第一阶段：Input组件测试 ✅
- ✅ 已修复 backend/services/feishu_bot.py 中缺少 asyncio 导入的问题
- ✅ 已修复 Input 组件格式问题（添加 action_type 和 value 字段）
- ✅ 已移除所有 emoji 字符（解决 Windows GBK 编码问题）
- ✅ 已实现 Input 回调处理（feishu_long_connection_service.py 第 1420-1432 行）

### 第二阶段：Button-Based卡片改造 ✅
- ✅ 改造持仓卡片为button-based布局
   - 每个股票一行，包含3个按钮：股票名称(primary)、查询(default)、删除(danger)
   - 股票名称按钮：查询价格 (action: query_stock_price)
   - 查询按钮：查询详情 (action: query_stock_detail)
   - 删除按钮：删除股票 (action: delete_stock_from_holdings)
   - 文件：feishu_card_service.py `_create_holdings_display_card()`

- ✅ 改造关注列表卡片为button-based布局
   - 每个股票一行，包含3个按钮：股票名称(primary)、查询(default)、删除(danger)
   - 股票名称按钮：查询价格 (action: query_stock_price)
   - 查询按钮：查询详情 (action: query_stock_detail)
   - 删除按钮：删除股票 (action: delete_stock_from_watchlist)
   - 文件：feishu_card_service.py `_create_watchlist_display_card()`

### 第三阶段：Action处理实现 ✅
- ✅ 实现删除股票功能
   - _handle_delete_stock_async方法：处理删除操作
   - 支持从持仓删除：调用HoldingsManager.remove_stock()
   - 支持从关注列表删除：调用DailyWatchlistManager.delete_stocks()
   - 删除后自动刷新卡片显示
   - 文件：feishu_long_connection_service.py

- ✅ 添加新查询action支持
   - query_stock_price: 查询股票价格
   - query_stock_detail: 查询股票详情
   - 已添加到query_actions列表
   - 已在handle_card_callback中添加处理逻辑
   - 文件：feishu_card_service.py, feishu_long_connection_service.py

### 第四阶段：代码修复 ✅
- ✅ 修复缩进错误：删除feishu_card_service.py中的重复代码
- ✅ 修复JSON序列化错误：date对象转换为字符串
- ✅ 修复GBK编码错误：移除emoji字符
- ✅ 修复导入错误：使用正确的数据库session方法
- ✅ 修复stock_code缺失问题：添加股票名称到代码的映射
- ✅ 修复data_dir属性错误：使用settings.data_dir

### 第五阶段：测试验证 ✅
- ✅ test_button_cards.py: 验证button-based卡片结构
   - Holdings: 11只股票，每只3个按钮，结构正确
   - Watchlist: 2只股票，每只3个按钮，结构正确
   - Stock code mapping: 已正确映射
- ✅ test_send_button_cards.py: 发送实际卡片到飞书测试
   - 卡片发送逻辑正确
   - 错误处理完善
- ✅ restart_and_test.bat: 一键重启并测试脚本

## 测试方法

### 推荐方法：通过飞书聊天测试
1. 启动后端服务：`restart_backend.bat` 或 `python backend/main.py`
2. 在飞书中发送：`持仓` 或 `查看关注`
3. 测试按钮功能：
   - 点击股票名称 → 查询价格
   - 点击"查询" → 查询详情
   - 点击"删除" → 删除股票

### API测试方法
```bash
# 查询持仓卡片
curl -X POST http://localhost:8000/api/feishu/test/send-holdings \
  -H "Content-Type: application/json" \
  -d '{"chat_id": "你的chat_id"}'

# 查询关注列表卡片
curl -X POST http://localhost:8000/api/feishu/test/send-watchlist \
  -H "Content-Type: application/json" \
  -d '{"chat_id": "你的chat_id"}'
```

## 代码修改总结

### 关键修改
1. **feishu_card_service.py**
   - `_create_holdings_display_card()`: button-based持仓卡片
   - `_create_watchlist_display_card()`: button-based关注列表卡片
   - `handle_card_callback()`: 新增query_stock_price和query_stock_detail处理
   - `send_watchlist_display_card()`: 修复date序列化问题

2. **feishu_long_connection_service.py**
   - `_handle_delete_stock_async()`: 删除股票处理方法
   - `query_actions`: 添加query_stock_price和query_stock_detail
   - 删除动作处理逻辑

3. **测试文件**
   - test_button_cards.py: 卡片结构验证
   - test_send_button_cards.py: 飞书发送测试
   - BUTTON_CARD_TEST_GUIDE.md: 测试指南文档

### 第六阶段：Schema 2.0 格式修复 ✅
- ✅ 发现并修复 Schema 2.0 格式问题
   - 移除 input 组件的 `required` 属性（不支持）
   - 移除 `action` 标签（Schema 2.0 不支持）
   - 移除 `note` 标签（Schema 2.0 不支持）
   - 按钮直接放在 elements 中
   - 使用 div 代替 note
- ✅ 更新 backend/services/feishu_card_service.py
   - `_create_stock_query_card()` 使用正确格式
   - `_ensure_button_names()` 支持 Schema 2.0
- ✅ 创建独立测试脚本
   - test_input_standalone.py
   - 成功发送测试卡片到飞书
- ✅ 创建正确格式示例文件
   - test_cards/production_card_v2.json
   - SCHEMA2_FORMAT_SOLUTION.md

## Schema 2.0 关键格式

**必须**:
- `"schema": "2.0"` 声明
- `"body": {"elements": [...]}` 结构
- 按钮直接在 elements 中（不包裹在 action 中）
- 使用 div 代替 note

**不支持**:
- input 组件的 `required` 属性
- `action` 标签
- `note` 标签
- 旧版 elements 直接在根级别

## 下一步

### 需要用户测试
- [ ] 在飞书中测试所有按钮功能
- [ ] 验证删除功能是否正常工作
- [ ] 验证查询功能是否返回正确数据
- [ ] 检查用户体验是否流畅

### 可选优化
- [ ] 添加确认对话框（删除操作）
- [ ] 添加更多功能按钮
- [ ] 优化卡片布局和样式
- [ ] 添加股票价格实时更新

运行命令：
D:\play-ground\股票研究\stock-peg\backend\.venv\Scripts\python.exe d:\play-ground\股票研究\stock-peg\test\fei-shu-com\test_input_card.py

测试步骤：
1. 运行测试脚本发送卡片到飞书
2. 在手机飞书打开卡片，应该能看到输入框
3. 点击输入框，输入内容（如：中国神华）
4. 点击「提交测试」按钮
5. 查看 backend 控制台日志，搜索 🧪[TEST_INPUT] 查看输入内容


