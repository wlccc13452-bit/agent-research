# 目标价功能测试指南

## 问题描述
用户报告：前端LeftPanel中，"自持股票"和"动态关注股票"栏无法显示UI和目标价相关信息

## 分析结果

### 代码实现状态：✅ 全部完成

**后端：**
- ✅ 数据模型：`target_price`, `change_up_pct`, `change_down_pct` 字段已添加
- ✅ API接口：`PUT /api/holdings/stock/target` 已实现
- ✅ 数据持久化：Markdown HTML comments格式保存
- ✅ 数据库字段：DailyWatchlist表字段已迁移

**前端：**
- ✅ HoldingsPanel：Target图标、Eye/EyeOff按钮、目标价对话框已实现
- ✅ LeftPanel：Target图标、Eye/EyeOff按钮、目标价对话框已实现
- ✅ API服务：`updateStockTarget` 方法已实现

### 根本原因

**第二行信息有条件渲染：**
```typescript
// 只有当至少有一个目标价字段有值时，第二行才显示
const hasTarget = stock.target_price || stock.change_up_pct || stock.change_down_pct;
{showSecondLine && hasTarget && (
  <div>第二行内容</div>
)}
```

当前所有股票的目标价字段都是 `None`，所以：
- ✅ Target图标显示（灰色）
- ✅ Eye/EyeOff按钮显示
- ❌ 第二行信息不显示（因为没有数据）

## 测试步骤

### 方法1：通过UI设置目标价（推荐）

1. 启动后端服务：
   ```bash
   cd backend
   .venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. 启动前端服务：
   ```bash
   cd frontend
   npm run dev
   ```

3. 打开浏览器访问：http://localhost:5173

4. 在"自持股票"或"动态关注股票"栏：
   - 点击股票右侧的 **Target图标** (🎯)
   - 在弹出的对话框中输入：
     - 目标价格：5.50
     - 上涨控制比例：20.00
     - 下跌控制比例：10.00
   - 点击"保存"

5. 验证结果：
   - Target图标变为**黄色**（表示已设置）
   - 点击 **Eye图标** 切换显示/隐藏
   - 第二行显示：
     ```
     目标价: 5.50 (+15.23%)  涨控: +20.00%  跌控: -10.00%
     ```

### 方法2：通过API设置目标价

运行测试脚本：
```bash
cd backend
.venv\Scripts\python.exe test_set_target.py
```

## UI元素说明

| 元素 | 位置 | 功能 | 显示条件 |
|------|------|------|----------|
| Target图标 | 股票行右侧 | 设置目标价 | 始终显示 |
| Eye/EyeOff按钮 | 栏目标题右侧 | 切换第二行显示 | 始终显示 |
| 第二行信息 | 股票行下方 | 显示目标价详情 | showSecondLine=true **且** hasTarget=true |

## 已验证功能

✅ 后端API正常工作（测试通过）
✅ 数据库字段存在
✅ 前端代码逻辑正确
✅ 图标正确导入
✅ 数据持久化正常

## 结论

**功能实现完整，代码无误。**

用户看到的现象是**预期行为**：
- 当股票没有设置目标价时，第二行不显示
- 点击Target图标可以设置目标价
- 设置后，第二行会自动显示

**建议操作：**
点击任意股票的Target图标，设置目标价，即可看到完整的UI功能。
