# Button-Based Cards 测试指南

## 已完成的改造

### 1. 持仓卡片
- 每个股票一行，包含3个按钮：
  - **股票名称** (primary) → 查询价格
  - **查询** (default) → 查询详情
  - **删除** (danger) → 从持仓删除

### 2. 关注列表卡片
- 每个股票一行，包含3个按钮：
  - **股票名称** (primary) → 查询价格
  - **查询** (default) → 查询详情
  - **删除** (danger) → 从关注列表删除

## 测试步骤

### 方法一：通过飞书聊天测试（推荐）

1. **启动后端服务**
   ```bash
   cd backend
   python main.py
   ```
   或使用批处理脚本：
   ```bash
   restart_backend.bat
   ```

2. **在飞书中测试**
   - 发送：`持仓` 或 `查看持仓`
   - 点击股票名称按钮 → 应该显示股票价格
   - 点击"查询"按钮 → 应该显示股票详情
   - 点击"删除"按钮 → 应该删除股票并刷新列表

   - 发送：`查看关注` 或 `关注`
   - 同样测试3个按钮功能

### 方法二：通过API测试

1. **查询持仓卡片**
   ```bash
   curl -X POST http://localhost:8000/api/feishu/test/send-holdings \
     -H "Content-Type: application/json" \
     -d '{"chat_id": "你的chat_id"}'
   ```

2. **查询关注列表卡片**
   ```bash
   curl -X POST http://localhost:8000/api/feishu/test/send-watchlist \
     -H "Content-Type: application/json" \
     -d '{"chat_id": "你的chat_id"}'
   ```

## 验证点

### 卡片结构
- [x] 每个股票显示为一行
- [x] 每行包含3个按钮：股票名称、查询、删除
- [x] 按钮样式正确：primary/default/danger
- [x] 卡片底部有"添加"和"主菜单"按钮

### 按钮功能
- [ ] 股票名称按钮：显示股票实时价格
- [ ] 查询按钮：显示股票详细信息
- [ ] 删除按钮：删除股票并刷新列表
- [ ] 添加按钮：显示添加股票界面
- [ ] 主菜单按钮：返回主菜单

### 删除功能
- [ ] 从持仓删除：成功删除并刷新持仓卡片
- [ ] 从关注列表删除：成功删除并刷新关注列表卡片
- [ ] 删除不存在的股票：显示错误提示

## 故障排查

### 问题1：按钮点击无响应
- 检查后端服务是否运行
- 检查飞书长连接服务是否正常
- 查看后端日志中的错误信息

### 问题2：删除失败
- 检查数据库连接
- 检查持仓文件是否存在
- 查看后端日志中的错误信息

### 问题3：查询失败
- 检查股票数据服务是否正常
- 检查API是否可用
- 查看后端日志中的错误信息

## 代码修改位置

### 关键文件
1. `backend/services/feishu_card_service.py`
   - `_create_holdings_display_card()`: 创建button-based持仓卡片
   - `_create_watchlist_display_card()`: 创建button-based关注列表卡片
   - `handle_card_callback()`: 处理query_stock_price和query_stock_detail

2. `backend/services/feishu_long_connection_service.py`
   - `_handle_delete_stock_async()`: 处理删除股票操作
   - `query_actions`: 添加了query_stock_price和query_stock_detail

## 下一步

- [ ] 测试所有按钮功能
- [ ] 修复发现的问题
- [ ] 优化用户体验
- [ ] 添加更多功能按钮
