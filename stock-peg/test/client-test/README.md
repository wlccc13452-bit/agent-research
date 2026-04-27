# K线快速加载测试工具

## 功能说明

本工具用于测试客户端快速加载K线数据的逻辑，验证服务端本地数据可用性。

## 测试内容

1. 从后端API获取自持股票列表
2. 测试所有自持股票的K线快速加载
3. 验证本地数据是否可用
4. 统计加载性能和成功率

## 快速开始

### 步骤1: 运行环境诊断

```bash
# 检查环境是否就绪
diagnose.bat
```

诊断内容：
- ✅ Node.js是否安装
- ✅ 后端服务是否运行
- ✅ API连接是否正常
- ✅ 数据库是否有数据

### 步骤2: 运行测试

```bash
# 默认后端地址 http://localhost:8000
run_test_mjs.bat

# 自定义后端地址
run_test_mjs.bat http://192.168.1.100:8000
```

## 使用方法

### 方式1: 使用批处理脚本（推荐）

```bash
# 默认后端地址 http://localhost:8000
run_test_mjs.bat

# 自定义后端地址
run_test_mjs.bat http://192.168.1.100:8000
```

### 方式2: 直接运行JavaScript

```bash
# 运行测试（需要Node.js 18+）
node test_kline_fast_load.mjs

# 指定后端地址
node test_kline_fast_load.mjs --base=http://localhost:8000
```

## 常见问题

### 问题1: 中文乱码

**原因**: 批处理文件编码问题

**解决**: 已在批处理文件中添加 `chcp 65001` 设置UTF-8编码

### 问题2: "This operation was aborted"

**原因**: 请求超时或后端服务未启动

**解决**: 
1. 运行 `diagnose.bat` 检查环境
2. 确保后端服务正在运行
3. 检查端口8000是否被占用

### 问题3: 测试失败

**可能原因**:
1. 后端服务未启动
2. 数据库无数据
3. 网络连接问题

**解决步骤**:
```bash
# 1. 启动后端服务
cd backend
python main.py

# 2. 检查数据库
# 查看是否有K线数据

# 3. 运行诊断
cd ..\test\client-test
diagnose.bat
```

## 输出说明

测试完成后会输出：

- **总体统计**: 股票总数、成功/失败数量、本地数据可用数量、耗时统计
- **失败详情**: 加载失败的股票及错误原因
- **本地数据不可用详情**: 成功加载但无本地数据的股票
- **成功加载详情**: 所有成功加载的股票详情（数据量、日期范围、耗时等）

## 测试标准

✅ **测试通过条件**:
- 所有自持股票加载成功
- 大部分股票有本地数据可用
- 平均加载耗时 < 500ms

❌ **测试失败条件**:
- 有股票加载失败
- 大部分股票无本地数据
- 平均加载耗时 > 1000ms

## 注意事项

1. 确保后端服务已启动（默认端口8000）
2. 测试使用 `localOnly=true` 参数，只读取本地数据，不触发更新
3. 测试串行执行，避免对服务端造成过大压力
4. 如需测试更新逻辑，可修改代码中的 `localOnly` 参数

## 相关API

测试工具调用的API接口：

- `GET /api/holdings/` - 获取自持股票列表
- `GET /api/stocks/kline-db-fast/{stockCode}` - 快速加载K线数据

## 文件说明

```
test/client-test/
├── test_kline_fast_load.ts  # 主测试文件
├── run_test.bat             # Windows批处理运行脚本
├── README.md                # 本说明文档
└── kline_client_debug.mjs   # 原始调试脚本（参考）
```
