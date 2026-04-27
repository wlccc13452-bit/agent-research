# 目标价设置数据接口诊断报告

## 问题现象

用户在前端设置目标价后，界面无法显示目标价相关信息。

## 诊断步骤

### 1. 检查后端代码

#### API路由 (`backend/routers/holding.py` 第274-291行)

```python
@router.put("/stock/target")
async def update_stock_target(request: UpdateStockTargetRequest):
    """更新股票目标价和涨跌控制比例"""
    success = await holding_manager.update_stock_target(
        request.sector_name,
        request.stock_name,
        request.target_price,
        request.change_up_pct,
        request.change_down_pct
    )
    if success:
        return {"message": f"成功更新股票 {request.stock_name} 的目标价设置"}
    else:
        raise HTTPException(status_code=400, detail="更新股票目标价失败")
```

**状态:** ✅ 代码正确

#### 服务层 (`backend/services/holding_manager.py` 第430-454行)

```python
async def update_stock_target(self, sector_name: str, stock_name: str,
                               target_price: Optional[float] = None,
                               change_up_pct: Optional[float] = None,
                               change_down_pct: Optional[float] = None) -> bool:
    # 1. 查找股票
    sector = next((s for s in self.holdings.sectors if s.name == sector_name), None)
    stock = next((s for s in sector.stocks if s.name == stock_name), None)

    # 2. 更新内存中的数据
    stock.target_price = target_price
    stock.change_up_pct = change_up_pct
    stock.change_down_pct = change_down_pct

    # 3. 保存到文件
    return await self.save_holdings(self.holdings)
```

**状态:** ✅ 代码正确

#### 保存逻辑 (`backend/services/holding_manager.py` 第240-270行)

```python
async def save_holdings(self, holdings: Holdings) -> bool:
    content = "# 自持股票\n\n"
    for sector in holdings.sectors:
        content += f"## {sector.name}\n"
        for stock in sector.stocks:
            if stock.target_price or stock.change_up_pct or stock.change_down_pct:
                extra_info = []
                if stock.target_price is not None:
                    extra_info.append(f"target_price:{stock.target_price}")
                if stock.change_up_pct is not None:
                    extra_info.append(f"change_up_pct:{stock.change_up_pct}")
                if stock.change_down_pct is not None:
                    extra_info.append(f"change_down_pct:{stock.change_down_pct}")
                content += f"    {stock.name} <!-- {', '.join(extra_info)} -->\n"
            else:
                content += f"    {stock.name}\n"

    # 写入文件
    await aiofiles.open(temp_path, 'w', encoding='utf-8').write(content)
    await asyncio.to_thread(temp_path.replace, self.file_path)

    # 更新内存
    self.holdings = holdings
    return True
```

**状态:** ✅ 代码正确

### 2. 检查数据文件

**文件路径:** `backend/data/自持股票.md`

**当前内容:**
```markdown
# 自持股票

## 铝
    南山铝业
    中国神华

## 光伏
    隆基绿能
...
```

**状态:** ❌ **文件中没有目标价HTML注释！**

### 3. 前端API调用

**HoldingsPanel.tsx (第94-108行):**

```typescript
const updateTargetMutation = useMutation({
  mutationFn: () => holdingsApi.updateStockTarget({
    sector_name: targetForm.sectorName,
    stock_name: targetForm.stockName,
    target_price: targetForm.targetPrice ? parseFloat(targetForm.targetPrice) : null,
    change_up_pct: targetForm.changeUpPct ? parseFloat(targetForm.changeUpPct) : null,
    change_down_pct: targetForm.changeDownPct ? parseFloat(targetForm.changeDownPct) : null,
  }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['initial-data'] });
    queryClient.invalidateQueries({ queryKey: ['holdings'] });
    setShowTargetDialog(false);
  },
});
```

**状态:** ✅ 代码正确

## 根本原因分析

### 可能原因1: 前端输入框为空

**问题:** 如果用户在目标价对话框中没有输入任何值，`targetForm.targetPrice` 为空字符串 `''`。

**代码:**
```typescript
target_price: targetForm.targetPrice ? parseFloat(targetForm.targetPrice) : null
```

**结果:**
- 空字符串 → `parseFloat('')` → `NaN` → falsy → `null`
- 所有字段都是 `null`

**影响:** `hasTarget = false`，界面不显示第二行

### 可能原因2: 后端服务未重启

如果代码修改后后端服务没有重启，可能使用的是旧代码。

## 解决方案

### 方案1: 确保输入验证（推荐）

修改前端对话框，确保至少有一个字段有值：

```typescript
const handleSave = () => {
  if (!targetForm.targetPrice && !targetForm.changeUpPct && !targetForm.changeDownPct) {
    alert('请至少填写一个字段');
    return;
  }
  updateTargetMutation.mutate();
};
```

### 方案2: 添加测试数据

直接通过API设置测试数据：

**PowerShell命令:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/holdings/stock/target" `
  -Method Put `
  -ContentType "application/json" `
  -Body '{"sector_name":"铝","stock_name":"南山铝业","target_price":5.50,"change_up_pct":20.0,"change_down_pct":10.0}'
```

**验证:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/holdings/" -Method Get
```

### 方案3: 重启后端服务

1. 停止当前后端服务（Ctrl+C）
2. 重新启动：
   ```bash
   cd backend
   .venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

## 测试步骤

### 1. 重启后端服务

确保使用最新代码。

### 2. 在前端设置目标价

1. 打开浏览器开发者工具（F12）
2. 切换到Network标签
3. 点击股票的Target图标🎯
4. 填写数据：
   - 目标价格: 5.50
   - 上涨控制比例: 20.00
   - 下跌控制比例: 10.00
5. 点击"保存"
6. 观察Network面板中的请求：
   - PUT `/api/holdings/stock/target` → 状态码应为200
   - GET `/api/holdings/` → 响应中应包含目标价数据

### 3. 验证文件

检查 `backend/data/自持股票.md` 文件：
```markdown
## 铝
    南山铝业 <!-- target_price:5.5, change_up_pct:20.0, change_down_pct:10.0 -->
```

## 预期结果

✅ 设置目标价后：
- 文件中包含HTML注释
- API返回数据包含目标价字段
- 前端显示完整的目标价信息

## 排查清单

- [ ] 后端服务是否重启
- [ ] 输入框是否填写数据
- [ ] Network面板请求是否成功
- [ ] 文件是否更新
- [ ] API响应是否包含目标价

---

**诊断时间:** 2026-03-20
**状态:** 等待用户测试验证
