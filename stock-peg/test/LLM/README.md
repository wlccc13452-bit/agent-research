# LLM智能评估报告测试方案

## 测试目标

验证LLM智能评估报告功能的可行性，包括：
1. 数据收集（K线、技术指标、指数、财务、新闻）
2. 数据组织（JSON格式）
3. LLM调用（智谱AI）
4. 报告生成（Markdown格式）
5. 文件保存

## 测试步骤

### 第一步：数据收集测试
- 测试获取20天K线数据
- 测试获取技术指标（MA/EMA/MACD）
- 测试获取指数数据
- 测试获取财务数据
- 测试获取新闻数据

### 第二步：LLM调用测试
- 构建测试数据JSON
- 调用智谱AI API
- 验证返回结果

### 第三步：报告生成测试
- 解析LLM返回结果
- 生成Markdown格式报告
- 保存到文件

## 运行测试

```bash
cd d:/2026projects/stocks-research/stock-peg/test/LLM
d:/2026projects/stocks-research/stock-peg/backend/.venv/Scripts/python.exe test_llm_report.py
```

## 预期结果

1. 成功收集所有数据
2. 成功调用LLM API
3. 生成完整的Markdown报告
4. 报告保存在 `backend/data/llm_reports/` 目录
