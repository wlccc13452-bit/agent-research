# 数据诊断工具使用说明

## 文件列表

### 诊断脚本
- `diagnose_data_issue.py` - 完整的诊断脚本，检查所有数据获取问题
- `check_db_structure.py` - 检查数据库表结构
- `check_us_indices.py` - 检查美股指数数据

### 运行脚本
- `run_diagnose.bat` - Windows批处理脚本，一键运行诊断

### 诊断报告
- `DIAGNOSIS_RESULT.md` - 最终诊断结果（推荐阅读）
- `FINAL_DIAGNOSTIC_SUMMARY.md` - 详细技术方案
- `DIAGNOSTIC_REPORT.md` - 初步诊断报告

### 原始日志
- `console.md` - 后端运行日志，包含错误信息

---

## 快速开始

### 方法1: 使用批处理脚本（推荐）
双击运行 `run_diagnose.bat`

### 方法2: 命令行运行
```bash
cd d:\play-ground\股票研究\stock-peg\test\console-md
d:\play-ground\股票研究\stock-peg\backend\.venv\Scripts\python.exe diagnose_data_issue.py
```

---

## 诊断结果摘要

### 发现的问题

#### ❌ 问题1: 美股数据查询失败
- **原因**: 数据库列名是 `us_stock_code`，代码使用 `symbol`
- **影响**: 无法获取美股指数数据
- **修复**: 替换列名

#### ❌ 问题2: A股指数获取失败
- **原因**: 代码格式不兼容（`000001.SH` vs `sh000001`）
- **影响**: headbar上的A股指数无法显示
- **修复**: 添加代码格式转换

#### ⚠️ 问题3: VIX数据更新不及时
- **原因**: 数据源获取失败
- **影响**: VIX数据不是最新
- **修复**: 优化数据源

---

## 数据库状态

### 美股指数数据
```
✓ ^DJI (道琼斯): 2026-03-09, 47501.55点, -0.95%
✓ ^GSPC (标普500): 2026-03-09, 6740.02点, -1.33%
✓ ^IXIC (纳斯达克): 2026-03-09, 22387.68点, -1.59%
✓ ^VIX (恐慌指数): 2026-03-08, 15点, -2%
```

### 财务数据
- 记录数: 1286条
- 状态: 正常

---

## 下一步行动

### 1. 修复美股数据查询（5分钟）
修改 `backend/services/us_market_analyzer.py`:
```python
# 将所有 'symbol' 替换为 'us_stock_code'
```

### 2. 修复A股指数格式（10分钟）
在相关服务中添加代码格式转换函数

### 3. 测试验证（5分钟）
```bash
# 测试美股指数
curl http://localhost:8000/api/us-market/indices

# 测试A股指数
curl http://localhost:8000/api/stock/index/realtime?codes=000001.SH,399001.SZ
```

---

## 详细信息

- **完整诊断结果**: 查看 `DIAGNOSIS_RESULT.md`
- **技术方案**: 查看 `FINAL_DIAGNOSTIC_SUMMARY.md`
- **错误日志**: 查看 `console.md`

---

**创建时间**: 2026-03-09
