# 故障排查指南

## 🚨 常见问题：前端卡在"正在后台加载自持股票数据..."

### 根本原因
**后端进程冲突** + **前端无超时保护** = 前端永久卡住

### 完整因果链
```
后端进程冲突（多个进程监听同一端口）
  ↓
API 无法连接（ConnectionRefusedError）
  ↓
前端 useQuery 等待 API 响应（无超时）
  ↓
queryFn 永不完成
  ↓
initialData 永远是 undefined
  ↓
holdingsReady 永远是 false
  ↓
前端显示"正在后台加载..."永不消失
```

---

## 🛡️ 预防措施（三层防护）

### 第一层：启动脚本防护
✅ **已增强 `start.bat`**
- 自动清理旧进程（包括僵尸进程）
- 清理卡住的网络连接（CLOSE_WAIT/FIN_WAIT）
- 等待端口完全释放
- 验证启动成功

**使用方法**：
```bash
# 正常启动
start.bat
```

### 第二层：停止脚本防护
✅ **新增 `stop.bat`**
- 彻底停止所有服务
- 清理所有相关进程
- 清理网络连接

**使用方法**：
```bash
# 停止所有服务
stop.bat
```

### 第三层：前端防护
✅ **已添加三层兜底机制**
1. **API 超时保护**（3秒）
2. **loading 完成时强制解锁**
3. **终极兜底**：5秒后强制显示界面

---

## 🔧 诊断工具

### 1. 健康检查
```bash
check-health.bat
```
检查后端/前端服务状态和进程数

### 2. 手动检查进程
```bash
# 检查端口占用
netstat -ano | findstr :8000
netstat -ano | findstr :5173

# 检查 Python 进程
tasklist | findstr python.exe

# 检查 Node 进程
tasklist | findstr node.exe
```

### 3. 手动清理进程
```bash
# 强制杀掉进程
taskkill /F /PID <进程ID>

# 杀掉所有 Python 进程
taskkill /F /IM python.exe

# 杀掉所有 Node 进程
taskkill /F /IM node.exe
```

---

## 📋 操作规范

### ✅ 正确流程
1. **启动前**：运行 `stop.bat` 确保完全停止
2. **启动**：运行 `start.bat`
3. **停止**：运行 `stop.bat`

### ❌ 错误操作
- ❌ 多次运行 `start.bat`（会导致进程冲突）
- ❌ 直接关闭终端窗口（进程不会停止）
- ❌ 手动杀进程（可能留下僵尸进程）

---

## 🚀 性能监控

### 正常状态
- Python 进程数：1-2 个
- Node 进程数：1-2 个
- 端口 8000：LISTENING（单个进程）
- 端口 5173：LISTENING（单个进程）

### 异常状态
- Python 进程数 > 3：存在僵尸进程
- Node 进程数 > 3：存在僵尸进程
- 多个进程监听同一端口：端口冲突

---

## 🔄 紧急恢复

如果遇到问题，按以下步骤恢复：

1. **完全停止**
   ```bash
   stop.bat
   ```

2. **检查进程**
   ```bash
   check-health.bat
   ```

3. **手动清理（如果需要）**
   ```bash
   taskkill /F /IM python.exe
   taskkill /F /IM node.exe
   ```

4. **等待 5 秒**
   ```bash
   ping 127.0.0.1 -n 6 > nul
   ```

5. **重新启动**
   ```bash
   start.bat
   ```

---

## 💡 设计原则

**Non-Blocking Principle**：
- ✅ 后端立即返回本地数据（不等待外部 API）
- ✅ 前端立即显示界面（不等待后端完成）
- ✅ 数据通过 WebSocket 异步推送更新

**前端三层保护**：
- ✅ API 超时保护（3秒）
- ✅ loading 完成时解锁
- ✅ 5秒强制解锁

---

## 📝 故障记录

### 2026-03-18 问题
- **症状**：前端卡在"正在后台加载自持股票数据..."
- **原因**：后端进程冲突（两个进程监听端口 8000）
- **解决**：增强 start.bat，添加 stop.bat，前端添加超时保护
- **预防**：三层防护机制

---

## 🎯 总结

**记住**：遇到问题先运行 `stop.bat`，再运行 `start.bat`！

**三剑客**：
- `start.bat` - 启动并自动清理
- `stop.bat` - 彻底停止
- `check-health.bat` - 健康检查
