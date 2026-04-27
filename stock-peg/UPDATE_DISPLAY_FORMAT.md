# 目标价信息显示格式优化

## 用户反馈

前端LeftPanel中，"自持股票"和"动态关注股票"栏显示的目标价相关信息不完整，应完整显示"涨跌控制比例"。

## 优化内容

### Before (优化前)

```typescript
{stock.target_price && (
  <span>目标价: {stock.target_price.toFixed(2)}</span>
)}
{stock.change_up_pct && (
  <span>涨控: +{stock.change_up_pct.toFixed(2)}%</span>
)}
{stock.change_down_pct && (
  <span>跌控: -{stock.change_down_pct.toFixed(2)}%</span>
)}
```

**问题：**
1. ❌ 字段名缩写（"涨控"、"跌控"）不够清晰
2. ❌ 字段条件渲染，部分字段不显示
3. ❌ 没有占位符，信息显示不完整

### After (优化后)

```typescript
<span className="mr-3">
  目标价: <span>{stock.target_price ? stock.target_price.toFixed(2) : '--'}</span>
  {targetChangePct !== null && (
    <span>({targetChangePct > 0 ? '+' : ''}{targetChangePct.toFixed(2)}%)</span>
  )}
</span>
<span className="mr-3">
  上涨控制: <span>{stock.change_up_pct ? `+${stock.change_up_pct.toFixed(2)}%` : '--'}</span>
</span>
<span className="mr-3">
  下跌控制: <span>{stock.change_down_pct ? `-${stock.change_down_pct.toFixed(2)}%` : '--'}</span>
</span>
```

**改进：**
1. ✅ 字段名完整（"上涨控制"、"下跌控制"）
2. ✅ 所有字段始终显示，信息完整
3. ✅ 无数据时显示"--"占位符
4. ✅ 保持颜色区分（红色上涨、绿色下跌、黄色目标价）

## 显示示例

### 完整数据情况

```
目标价: 5.50 (+15.23%)  上涨控制: +20.00%  下跌控制: -10.00%
```

### 部分数据情况

```
目标价: 5.50  上涨控制: +20.00%  下跌控制: --
```

### 无数据情况

```
目标价: --  上涨控制: --  下跌控制: --
```

## 修改文件

| 文件 | 行号 | 修改内容 |
|------|------|----------|
| `frontend/src/components/HoldingsPanel.tsx` | 307-335 | 完善目标价信息显示格式 |
| `frontend/src/components/LeftPanel.tsx` | 405-433 | 完善目标价信息显示格式 |

## 代码质量

- ✅ 无TypeScript编译错误
- ✅ 无ESLint警告
- ✅ 保持原有样式风格
- ✅ 逻辑清晰完整

## 用户体验改进

| 场景 | 优化前 | 优化后 |
|------|--------|--------|
| 字段标签 | 缩写（"涨控"） | 完整（"上涨控制"） |
| 字段显示 | 条件渲染 | 始终显示 |
| 无数据时 | 字段消失 | 显示"--"占位符 |
| 信息完整性 | 部分显示 | 完整显示 |

---

**优化状态：** ✅ 完成
**编译状态：** ✅ 无错误
**准备部署：** ✅ 是
