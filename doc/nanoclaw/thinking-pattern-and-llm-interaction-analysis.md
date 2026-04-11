# NanoClaw 思维模式与 LLM 交互分析

## 一、功能实现

### 1.1 核心功能

| 功能 | 实现方式 | 入口 |
|------|----------|------|
| WhatsApp I/O | baileys 库连接 WhatsApp Web 协议 | `src/index.ts` |
| 群组隔离 | 每个群组独立文件夹和 CLAUDE.md | `groups/{name}/` |
| Main Channel | 自聊频道，拥有管理员权限 | `groups/main/` |
| 定时任务 | Cron/Interval/Once 三种类型 | `src/task-scheduler.ts` |
| Web 访问 | WebSearch + WebFetch 工具 | Agent SDK 内置 |
| 容器隔离 | Apple Container / Docker | `src/container-runner.ts` |

### 1.2 迭代流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                         HOST PROCESS                                │
│  ┌─────────────┐                                                    │
│  │ WhatsApp    │──────┐                                             │
│  │ Connection  │      │                                             │
│  └─────────────┘      ▼                                             │
│               ┌─────────────┐                                       │
│               │   SQLite    │◄──── Message Loop (2s)                │
│               │  Database   │◄──── Scheduler Loop (60s)             │
│               └──────┬──────┘◄──── IPC Watcher (1s)                 │
│                      │                                              │
│                      ▼                                              │
│               ┌─────────────┐                                       │
│               │  Routing    │                                       │
│               │  Decision   │                                       │
│               └──────┬──────┘                                       │
│                      │                                              │
├──────────────────────┼──────────────────────────────────────────────┤
│                      ▼                                              │
│               ┌─────────────┐                                       │
│               │  Container  │                                       │
│               │   Agent     │                                       │
│               │  (Claude)   │                                       │
│               └──────┬──────┘                                       │
│                      │                                              │
│                      ▼                                              │
│               ┌─────────────┐                                       │
│               │    IPC      │                                       │
│               │   Output    │                                       │
│               └──────┬──────┘                                       │
└──────────────────────┼──────────────────────────────────────────────┘
                       │
                       ▼
               WhatsApp Response
```

---

## 二、思维模式

### 2.1 核心模式：容器隔离 + 群组上下文

```
Container Isolation + Group Context = Secure Multi-Tenant Agent
```

**特点**：
1. **物理隔离**：每个群组的 Agent 在独立容器中运行
2. **上下文绑定**：Agent 的 cwd 设置为群组文件夹
3. **内存分离**：每个群组有独立的 CLAUDE.md 和会话

### 2.2 思维链维持机制

**会话连续性**：
```typescript
// data/sessions.json
{
  "main": "session-abc123",
  "family-chat": "session-def456"
}

// 容器执行时传递 sessionId
query({
  options: {
    resume: input.sessionId  // 恢复之前的对话上下文
  }
})
```

**对话归档机制**：
```typescript
// PreCompact Hook - 在会话压缩前归档
function createPreCompactHook(): HookCallback {
  return async (input) => {
    const transcriptPath = preCompact.transcript_path;
    const messages = parseTranscript(content);
    
    // 归档到 conversations/ 文件夹
    const filePath = path.join(conversationsDir, `${date}-${name}.md`);
    fs.writeFileSync(filePath, markdown);
    
    return {};
  };
}
```

**上下文传递**：
```
消息到达 → 获取上次 Agent 交互后的所有消息 → 格式化为 XML → 传给 Claude
```

```xml
<messages>
  <message sender="John" time="2026-01-31T14:32:00">hey everyone</message>
  <message sender="Sarah" time="2026-01-31T14:33:00">sounds good</message>
  <message sender="John" time="2026-01-31T14:35:00">@Andy what do you think?</message>
</messages>
```

### 2.3 群组隔离思维

**权限分层**：

| 层级 | 权限 | 实现方式 |
|------|------|----------|
| **Global** | 所有群组只读 | `groups/global/CLAUDE.md` |
| **Main** | 读写所有，管理群组 | `/workspace/project` 挂载 |
| **Group** | 只能访问自己 | `/workspace/group` 挂载 |

**隔离边界**：
```
Main Group Container:
  /workspace/project/  → 完整项目 (rw)
  /workspace/group/    → groups/main/ (rw)

Other Group Container:
  /workspace/group/    → groups/{name}/ (rw)
  /workspace/global/   → groups/global/ (ro)
  # 无 /workspace/project/ 访问
```

---

## 三、LLM 交互设计

### 3.1 交互架构

```
┌────────────────────────────────────────────────────────────────────┐
│                         LLM (Claude)                                │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  System Prompt (from CLAUDE.md)                              │  │
│  │  - Role definition (Andy)                                    │  │
│  │  - Capabilities list                                         │  │
│  │  - Memory indexing                                           │  │
│  │  - WhatsApp formatting rules                                 │  │
│  │  - Admin context (if main)                                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Tools                                                       │  │
│  │  - Bash (sandboxed in container)                             │  │
│  │  - Read/Write/Edit/Glob/Grep (file operations)               │  │
│  │  - WebSearch/WebFetch (internet)                             │  │
│  │  - mcp__nanoclaw__* (scheduler, messaging)                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

### 3.2 MCP 工具交互

**IPC 机制**：
```typescript
// Agent 调用 MCP 工具
await mcp__nanoclaw__send_message({ text: "Hello!" })

// 工具实现写入文件
function writeIpcFile(dir: string, data: object): string {
  const filename = `${Date.now()}-${Math.random()}.json`;
  const tempPath = `${filepath}.tmp`;
  fs.writeFileSync(tempPath, JSON.stringify(data));
  fs.renameSync(tempPath, filepath);  // 原子操作
  return filename;
}

// Host 轮询读取
const files = fs.readdirSync(messagesDir);
for (const file of files) {
  const data = JSON.parse(fs.readFileSync(file));
  if (data.type === 'message' && data.chatJid) {
    await sock.sendMessage(data.chatJid, { text: data.text });
  }
  fs.unlinkSync(file);
}
```

**工具定义示例**：
```typescript
tool(
  'schedule_task',
  `Schedule a recurring or one-time task...
   
   CONTEXT MODE - Choose based on task type:
   • "group": Task runs with chat history and memory
   • "isolated": Task runs in fresh session
   
   SCHEDULE VALUE FORMAT:
   • cron: "0 9 * * *"
   • interval: "3600000" (milliseconds)
   • once: "2026-02-01T15:30:00" (no Z suffix!)`,
  {
    prompt: z.string(),
    schedule_type: z.enum(['cron', 'interval', 'once']),
    schedule_value: z.string(),
    context_mode: z.enum(['group', 'isolated']).default('group'),
    target_group: z.string().optional()
  },
  async (args) => { ... }
)
```

### 3.3 交互特点

**优点**：
| 特点 | 描述 |
|------|------|
| 物理隔离 | 容器级别的安全边界 |
| 会话连续 | sessionId 恢复对话上下文 |
| 异步 IPC | 文件系统通信，解耦容器和宿主 |
| 权限分层 | Main/Group 不同的挂载和权限 |
| 对话归档 | PreCompact Hook 保存历史 |

**不足**：
| 问题 | 描述 |
|------|------|
| 无状态验证 | 没有验证 Agent 输出的正确性 |
| IPC 延迟 | 文件轮询有 1s 延迟 |
| 无并行能力 | 同一时刻只能处理一个群组的消息 |
| 会话膨胀 | 长对话会导致上下文窗口压力 |

---

## 四、迭代循环

### 4.1 主循环

```
┌─────────────────────────────────────────────────────────────────┐
│                      Main Loop (infinite)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  while (true) {                                                  │
│    // 1. 消息处理                                                │
│    messages = getNewMessages(jids, lastTimestamp)               │
│    for (msg of messages) {                                       │
│      await processMessage(msg)                                   │
│      lastTimestamp = msg.timestamp                               │
│      saveState()                                                 │
│    }                                                             │
│                                                                  │
│    await sleep(POLL_INTERVAL)  // 2s                             │
│  }                                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 调度循环

```
┌─────────────────────────────────────────────────────────────────┐
│                    Scheduler Loop (infinite)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  while (true) {                                                  │
│    dueTasks = getDueTasks()  // SELECT WHERE next_run <= now    │
│    for (task of dueTasks) {                                      │
│      currentTask = getTaskById(task.id)                         │
│      if (currentTask?.status === 'active') {                     │
│        await runTask(currentTask)                                │
│      }                                                           │
│    }                                                             │
│                                                                  │
│    await sleep(SCHEDULER_POLL_INTERVAL)  // 60s                  │
│  }                                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 IPC 循环

```
┌─────────────────────────────────────────────────────────────────┐
│                      IPC Watcher (infinite)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  while (true) {                                                  │
│    for (groupFolder of fs.readdirSync(ipcBaseDir)) {             │
│      // 处理消息                                                 │
│      for (file of messagesDir) {                                 │
│        data = JSON.parse(fs.readFileSync(file))                  │
│        if (authorized(data, groupFolder)) {                      │
│          await sock.sendMessage(data.chatJid, data.text)        │
│        }                                                         │
│        fs.unlinkSync(file)                                       │
│      }                                                           │
│                                                                  │
│      // 处理任务指令                                             │
│      for (file of tasksDir) {                                    │
│        await processTaskIpc(data, sourceGroup, isMain)          │
│        fs.unlinkSync(file)                                       │
│      }                                                           │
│    }                                                             │
│                                                                  │
│    await sleep(IPC_POLL_INTERVAL)  // 1s                         │
│  }                                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 五、系统潜在问题

### 5.1 架构问题

| 问题 | 描述 | 影响 |
|------|------|------|
| 单点故障 | 单一 Node 进程，崩溃后全部停止 | 可用性低 |
| 无事务回滚 | 任务执行失败无法回滚 | 数据一致性风险 |
| 隐性依赖 | 依赖 Apple Container/Docker 启动 | 初始化依赖 |
| 轮询开销 | 三个轮询循环持续运行 | CPU 占用 |

### 5.2 安全问题

| 问题 | 描述 | 风险等级 |
|------|------|----------|
| Prompt 注入 | WhatsApp 消息可能包含恶意指令 | 中（容器隔离缓解） |
| 凭证暴露 | CLAUDE_CODE_OAUTH_TOKEN 挂载到容器 | 中 |
| IPC 伪造 | 容器内可尝试写入其他群组 IPC | 低（已验证 groupFolder） |

### 5.3 LLM 问题

| 问题 | 描述 | 影响 |
|------|------|------|
| 无输出验证 | Agent 输出直接发送 | 可能发送错误内容 |
| 上下文膨胀 | 长对话导致 token 超限 | 会话中断 |
| 无记忆持久化策略 | CLAUDE.md 手动管理 | 记忆碎片化 |

### 5.4 功能问题

| 问题 | 描述 | 影响 |
|------|------|------|
| 单 WhatsApp 通道 | 不支持其他 IM 平台 | 扩展受限 |
| 无多用户支持 | 设计为单用户 | 不适合团队 |
| 无管理界面 | 只能通过 CLI/WhatsApp 管理 | 运维困难 |

---

## 六、与其他系统对比

### 6.1 思维模式对比

| 维度 | NanoClaw | Agentic Finance Review | Kilocode |
|------|----------|------------------------|----------|
| **核心模式** | 容器隔离 + 群组上下文 | 专业化代理 + Hook 验证 | 任务驱动 + 工具链 |
| **验证机制** | ❌ 无 | ✅ Hook 验证器 | ❌ 无 |
| **迭代模式** | 三循环并行 | 顺序流水线 | 请求-响应 |
| **状态管理** | 文件 + SQLite | 文件系统 | VS Code 状态 |

### 6.2 LLM 交互对比

| 维度 | NanoClaw | OpenClaw | Kilocode |
|------|----------|----------|----------|
| **交互方式** | IPC 文件系统 | 多通道适配器 | VS Code API |
| **工具扩展** | MCP Server | Skill 系统 | MCP 协议 |
| **上下文传递** | 群组 CLAUDE.md | 多通道共享 | 工作区设置 |
| **会话管理** | sessionId | 通道绑定 | 工作区绑定 |

---

## 七、改进建议

### 7.1 架构改进

1. **添加输出验证**：类似 Agentic Finance Review 的 Hook 机制
2. **并行处理**：支持同时处理多个群组消息
3. **健康检查**：添加心跳和自动恢复机制

### 7.2 安全改进

1. **凭证隔离**：使用环境变量注入而非文件挂载
2. **IPC 签名**：为 IPC 消息添加签名验证
3. **审计日志**：记录所有敏感操作

### 7.3 功能改进

1. **多通道支持**：通过 Skill 系统添加 Telegram/Slack
2. **管理界面**：Web Dashboard 管理群组和任务
3. **记忆管理**：自动总结和压缩长对话
