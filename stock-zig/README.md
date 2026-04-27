# stock-zig

一个使用 Zig 编写的轻量级股票行情 HTTP 服务。

## 功能

- `GET /health`：健康检查
- `GET /api/v1/quote?symbol=000001.SZ`：返回模拟行情数据
- 内置基础单元测试（目标解析与 query 参数解析）

## 环境要求

- Zig `0.15.x`（已在 `0.15.2` 验证）

## 快速开始

在项目根目录执行：

```bash
zig build
```

启动服务：

```bash
zig build run
```

默认监听地址：

- `http://0.0.0.0:8080`

## 使用示例

健康检查：

```bash
curl http://127.0.0.1:8080/health
```

查询行情：

```bash
curl "http://127.0.0.1:8080/api/v1/quote?symbol=600519.SH"
```

PowerShell 示例：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/health" -Method Get
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/quote?symbol=600519.SH" -Method Get
```

示例返回：

```json
{
  "symbol": "600519.SH",
  "price": 23.45,
  "change": 0.18,
  "currency": "CNY",
  "timestamp": 1773542400
}
```

## 测试与校验

运行单元测试：

```bash
zig build test
```

检查代码格式：

```bash
zig fmt --check build.zig src/main.zig
```

## 常见问题

- `zig build` 报 `AccessDenied` 时，通常是已有 `stock-zig.exe` 正在运行占用文件；先结束进程后再重试构建。

## 目录结构

```text
.
├─ build.zig
└─ src/
   └─ main.zig
```
