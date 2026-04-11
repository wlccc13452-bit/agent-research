# NanoClaw Container 模块概览

## 模块架构图

```
nanoclaw/container/
├── Dockerfile              # 容器镜像定义
├── build.sh                # 构建脚本
├── skills/                 # Skill 文件
│   └── agent-browser.md
└── agent-runner/           # Agent 运行器
    ├── package.json
    ├── tsconfig.json
    └── src/
        ├── index.ts        # 主入口
        └── ipc-mcp.ts      # IPC MCP Server
```

## 模块详解

---

### 1. Dockerfile - 容器镜像

**职责**：定义隔离的运行环境。

```dockerfile
FROM node:22-slim

# 安装系统依赖（Chromium）
RUN apt-get update && apt-get install -y \
    chromium \
    fonts-liberation \
    libnss3 \
    ...

# 设置 Chromium 路径
ENV AGENT_BROWSER_EXECUTABLE_PATH=/usr/bin/chromium

# 安装全局工具
RUN npm install -g agent-browser @anthropic-ai/claude-code

# 创建工作目录
RUN mkdir -p /workspace/group /workspace/ipc/messages /workspace/ipc/tasks

# 非 root 用户
USER node

# 入口脚本
ENTRYPOINT ["/app/entrypoint.sh"]
```

**关键设计**：
- 基于 Node.js 22
- 内置 Chromium（浏览器自动化）
- 非 root 用户运行（安全）
- 工作区挂载点

---

### 2. agent-runner/ - Agent 运行器

**职责**：执行 Agent 任务，管理会话。

```
agent-runner/
├── src/
│   ├── index.ts        # 主入口
│   └── ipc-mcp.ts      # MCP Server
├── package.json        # 依赖
└── tsconfig.json       # TypeScript 配置
```

#### 2.1 index.ts - 主入口

**核心功能**：

| 函数 | 功能 |
|------|------|
| `main()` | 读取输入，启动 Agent |
| `readStdin()` | 读取 JSON 输入 |
| `writeOutput()` | 输出 JSON 结果 |
| `createPreCompactHook()` | 会话压缩前归档 |
| `parseTranscript()` | 解析会话记录 |
| `formatTranscriptMarkdown()` | 格式化 Markdown |

**Agent 执行流程**：

```typescript
async function main() {
    // 1. 读取输入
    const input = JSON.parse(await readStdin());
    
    // 2. 创建 MCP Server
    const ipcMcp = createIpcMcp({...});
    
    // 3. 执行 Agent
    for await (const message of query({
        prompt: input.prompt,
        options: {
            resume: input.sessionId,
            allowedTools: [...],
            mcpServers: { nanoclaw: ipcMcp },
            hooks: { PreCompact: [...] }
        }
    })) {
        // 4. 处理消息
        if ('result' in message) {
            result = message.result;
        }
    }
    
    // 5. 输出结果
    writeOutput({ status: 'success', result });
}
```

#### 2.2 ipc-mcp.ts - IPC MCP Server

**核心功能**：通过 IPC 文件实现容器与宿主机的通信。

**MCP 工具列表**：

| 工具 | 功能 |
|------|------|
| `send_message` | 发送消息到 WhatsApp |
| `schedule_task` | 创建定时任务 |
| `list_tasks` | 列出所有任务 |
| `pause_task` | 暂停任务 |
| `resume_task` | 恢复任务 |
| `cancel_task` | 取消任务 |
| `register_group` | 注册新群组 |

**IPC 文件格式**：

```typescript
// 消息文件
{
    "type": "message",
    "chatJid": "120363336345536173@g.us",
    "text": "早安！",
    "groupFolder": "family-chat",
    "timestamp": "2026-02-26T09:00:00.000Z"
}

// 任务文件
{
    "type": "schedule_task",
    "prompt": "查看天气并发送提醒",
    "schedule_type": "cron",
    "schedule_value": "0 9 * * *",
    "context_mode": "group",
    "groupFolder": "family-chat"
}
```

---

### 3. skills/ - Skill 文件

**职责**：定义 Agent 能力。

```
skills/
└── agent-browser.md
```

#### agent-browser.md

**功能**：浏览器自动化。

**核心命令**：

| 命令 | 功能 |
|------|------|
| `open` | 打开页面 |
| `snapshot` | 获取页面快照 |
| `click` | 点击元素 |
| `fill` | 填写输入框 |
| `screenshot` | 截图 |
| `get text` | 获取文本 |
| `wait` | 等待条件 |

**使用示例**：

```bash
# 登录流程
agent-browser open https://example.com/login
agent-browser snapshot -i
agent-browser fill @e1 "username"
agent-browser fill @e2 "password"
agent-browser click @e3
agent-browser wait --url "**/dashboard"
```

---

### 4. build.sh - 构建脚本

**职责**：构建容器镜像。

```bash
#!/bin/bash

# 构建镜像
docker build -t nanoclaw-agent:latest .

# 或使用 Apple Container
# container build -t nanoclaw-agent:latest .
```

---

## 与宿主机交互

### 挂载点

```bash
docker run \
    -v /path/to/group:/workspace/group \      # 工作区
    -v /path/to/ipc:/workspace/ipc \          # IPC 通信
    -v /path/to/global:/workspace/global \    # 共享资源
    -e ANTHROPIC_API_KEY=... \
    nanoclaw-agent:latest
```

### IPC 通信流程

```
┌─────────────────┐     ┌─────────────────────┐
│   Host Process  │     │  Container (Agent)  │
│                 │     │                     │
│  ┌───────────┐  │     │  ┌───────────────┐  │
│  │  SQLite   │  │     │  │  Agent SDK    │  │
│  └─────┬─────┘  │     │  └───────┬───────┘  │
│        │        │     │          │          │
│        ▼        │     │          ▼          │
│  ┌───────────┐  │     │  ┌───────────────┐  │
│  │PollingLoop│  │     │  │   IPC MCP     │  │
│  └─────┬─────┘  │     │  └───────┬───────┘  │
│        │        │     │          │          │
│        │        │     │          │          │
│        │    ┌───┴────┴───┐      │          │
│        │    │ IPC Files  │      │          │
│        └───►│ /workspace/│◄─────┘          │
│             │    ipc/    │                 │
│             └────────────┘                 │
└─────────────────┘     └─────────────────────┘
```

---

## 与 NanoBot 模块对比

| 模块 | NanoClaw | NanoBot |
|------|----------|---------|
| 核心引擎 | Claude Agent SDK | 自实现 AgentLoop |
| 运行环境 | Docker 容器 | 直接进程 |
| 工具定义 | MCP Server | ToolRegistry |
| 消息通信 | IPC 文件 | asyncio.Queue |
| 会话管理 | SDK 内置 | SessionManager |
| 技能系统 | Markdown | Markdown |

---

## 扩展方式

### 添加新 MCP 工具

```typescript
// ipc-mcp.ts

tool(
    'new_tool',
    'Tool description',
    {
        param: z.string().describe('Parameter description')
    },
    async (args) => {
        // 写入 IPC 文件
        writeIpcFile(TASKS_DIR, {
            type: 'new_tool',
            param: args.param,
            timestamp: new Date().toISOString()
        });
        
        return {
            content: [{ type: 'text', text: 'Tool executed' }]
        };
    }
)
```

### 添加新 Skill

```markdown
---
name: new-skill
description: "Skill description"
allowed-tools: Bash(new-tool:*)
---

# New Skill

Usage instructions...
```

---

## 安全考虑

1. **非 root 用户**：容器以 `node` 用户运行
2. **工具限制**：通过 `allowedTools` 限制可用工具
3. **权限绕过**：`permissionMode: 'bypassPermissions'` 仅在受控环境
4. **隔离存储**：每个群组有独立的工作区
