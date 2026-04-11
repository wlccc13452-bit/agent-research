# NanoClaw 架构与框架研究

## 一、项目概述

**NanoClaw** 是一个轻量级个人 AI 助手，通过 WhatsApp 交互，使用容器隔离运行。核心理念："小到可以理解，安全通过隔离，AI 原生设计"。

**对比 OpenClaw**：
| 维度 | OpenClaw | NanoClaw |
|------|----------|----------|
| 代码量 | 52+ 模块 | 10 个源文件 |
| 依赖数 | 45+ | ~10 |
| 通道支持 | 15 种 | 仅 WhatsApp |
| 安全模型 | 应用级权限 | OS 容器隔离 |
| 进程模型 | 单进程共享内存 | 单进程 + 容器隔离 |

---

## 二、核心架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        HOST (macOS/Linux)                           │
│                   (Main Node.js Process)                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐                     ┌────────────────────┐        │
│  │  WhatsApp    │────────────────────▶│   SQLite Database  │        │
│  │  (baileys)   │◀────────────────────│   (messages.db)    │        │
│  └──────────────┘   store/send        └─────────┬──────────┘        │
│                                                  │                   │
│         ┌────────────────────────────────────────┘                   │
│         │                                                            │
│         ▼                                                            │
│  ┌──────────────────┐    ┌──────────────────┐    ┌───────────────┐  │
│  │  Message Loop    │    │  Scheduler Loop  │    │  IPC Watcher  │  │
│  │  (polls SQLite)  │    │  (checks tasks)  │    │  (file-based) │  │
│  └────────┬─────────┘    └────────┬─────────┘    └───────────────┘  │
│           │                       │                                  │
│           └───────────┬───────────┘                                  │
│                       │ spawns container                             │
│                       ▼                                              │
├─────────────────────────────────────────────────────────────────────┤
│                  APPLE CONTAINER / DOCKER (Linux VM)                │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    AGENT RUNNER                               │   │
│  │  (Claude Agent SDK 0.2.29)                                    │   │
│  │                                                                │   │
│  │  Working directory: /workspace/group                          │   │
│  │  Tools: Bash, Read, Write, Edit, Glob, Grep, WebSearch,       │   │
│  │         WebFetch, mcp__nanoclaw__* (scheduler tools via IPC)  │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

### 2.2 技术栈

| 组件 | 技术 | 用途 |
|------|------|------|
| WhatsApp 连接 | @whiskeysockets/baileys | 连接 WhatsApp Web 协议 |
| 消息存储 | SQLite (better-sqlite3) | 存储消息、任务、日志 |
| 容器运行时 | Apple Container / Docker | 隔离的 Linux VM |
| Agent SDK | @anthropic-ai/claude-agent-sdk | 运行 Claude 工具链 |
| 运行时 | Node.js 20+ | 主进程路由和调度 |

---

## 三、核心模块

### 3.1 主进程模块 (`src/index.ts`)

**职责**：
- WhatsApp 连接管理
- 消息路由
- IPC 监控
- 容器生命周期管理

**关键数据结构**：
```typescript
// 注册群组配置
interface RegisteredGroup {
  name: string;           // 显示名称
  folder: string;         // 文件夹名
  trigger: string;        // 触发词
  added_at: string;       // 添加时间
  containerConfig?: ContainerConfig;  // 容器配置
}

// 会话状态
interface Session {
  [folder: string]: string;  // folder → sessionId
}
```

### 3.2 容器运行器 (`src/container-runner.ts`)

**职责**：
- 构建容器挂载点
- 执行容器并传递输入
- 解析容器输出

**挂载策略**：
```typescript
// Main Group 挂载
[
  { hostPath: projectRoot, containerPath: '/workspace/project', readonly: false },
  { hostPath: groups/main, containerPath: '/workspace/group', readonly: false }
]

// 非 Main Group 挂载
[
  { hostPath: groups/{name}, containerPath: '/workspace/group', readonly: false },
  { hostPath: groups/global, containerPath: '/workspace/global', readonly: true }
]

// 共享挂载
[
  { hostPath: data/sessions/{group}/.claude, containerPath: '/home/node/.claude', readonly: false },
  { hostPath: data/ipc/{group}, containerPath: '/workspace/ipc', readonly: false }
]
```

### 3.3 任务调度器 (`src/task-scheduler.ts`)

**职责**：
- 轮询到期任务
- 执行容器 Agent
- 更新任务状态

**任务类型**：
| 类型 | 值格式 | 示例 |
|------|--------|------|
| cron | Cron 表达式 | `0 9 * * 1` (周一 9am) |
| interval | 毫秒数 | `3600000` (每小时) |
| once | ISO 时间戳 | `2024-12-25T09:00:00Z` |

### 3.4 数据库层 (`src/db.ts`)

**表结构**：
```sql
-- 聊天元数据
CREATE TABLE chats (
  jid TEXT PRIMARY KEY,
  name TEXT,
  last_message_time TEXT
);

-- 消息存储
CREATE TABLE messages (
  id TEXT,
  chat_jid TEXT,
  sender TEXT,
  sender_name TEXT,
  content TEXT,
  timestamp TEXT,
  is_from_me INTEGER,
  PRIMARY KEY (id, chat_jid)
);

-- 定时任务
CREATE TABLE scheduled_tasks (
  id TEXT PRIMARY KEY,
  group_folder TEXT NOT NULL,
  chat_jid TEXT NOT NULL,
  prompt TEXT NOT NULL,
  schedule_type TEXT NOT NULL,
  schedule_value TEXT NOT NULL,
  next_run TEXT,
  status TEXT DEFAULT 'active'
);
```

---

## 四、Agent Runner (容器内)

### 4.1 入口点 (`container/agent-runner/src/index.ts`)

**职责**：
- 从 stdin 读取输入
- 调用 Claude Agent SDK
- 输出结果到 stdout

**关键配置**：
```typescript
query({
  prompt,
  options: {
    cwd: '/workspace/group',
    resume: input.sessionId,
    allowedTools: [
      'Bash', 'Read', 'Write', 'Edit', 'Glob', 'Grep',
      'WebSearch', 'WebFetch', 'mcp__nanoclaw__*'
    ],
    permissionMode: 'bypassPermissions',
    settingSources: ['project'],
    mcpServers: { nanoclaw: ipcMcp }
  }
})
```

### 4.2 IPC MCP Server (`container/agent-runner/src/ipc-mcp.ts`)

**工具列表**：
| 工具 | 用途 |
|------|------|
| `send_message` | 发送 WhatsApp 消息 |
| `schedule_task` | 创建定时任务 |
| `list_tasks` | 列出任务 |
| `pause_task` | 暂停任务 |
| `resume_task` | 恢复任务 |
| `cancel_task` | 取消任务 |
| `register_group` | 注册新群组 (仅 Main) |

**IPC 机制**：
```
Container Agent → write file → /workspace/ipc/{group}/messages/*.json
                                    ↓
Host IPC Watcher → read file → send WhatsApp message
```

---

## 五、安全模型

### 5.1 信任模型

| 实体 | 信任级别 | 理由 |
|------|----------|------|
| Main Group | 可信 | 私人自聊，管理员控制 |
| 非 Main Group | 不可信 | 其他用户可能恶意 |
| 容器 Agent | 沙箱 | 隔离执行环境 |
| WhatsApp 消息 | 用户输入 | 潜在 Prompt 注入 |

### 5.2 安全边界

**1. 容器隔离（主要边界）**：
- 进程隔离：容器进程无法影响宿主机
- 文件系统隔离：只有显式挂载的目录可见
- 非 root 执行：以 `node` 用户 (uid 1000) 运行
- 临时容器：每次调用使用新环境 (`--rm`)

**2. 挂载安全**：
- 外部白名单：`~/.config/nanoclaw/mount-allowlist.json`
- 永不挂载到容器，无法被 Agent 修改
- 默认阻止敏感路径：`.ssh`, `.aws`, `.gnupg`, `id_rsa` 等

**3. 会话隔离**：
- 每个群组独立会话目录：`data/sessions/{group}/.claude/`
- 群组间无法看到彼此的对话历史

**4. IPC 授权**：
| 操作 | Main Group | 非 Main Group |
|------|------------|---------------|
| 发消息到自己群 | ✓ | ✓ |
| 发消息到其他群 | ✓ | ✗ |
| 为自己调度任务 | ✓ | ✓ |
| 为他人调度任务 | ✓ | ✗ |
| 管理其他群组 | ✓ | ✗ |

---

## 六、数据流

### 6.1 消息流

```
1. WhatsApp 消息到达
   ↓
2. Baileys 接收 → 存入 SQLite
   ↓
3. Message Loop 轮询 (2s)
   ↓
4. 检查: 已注册群组? 触发词?
   ↓
5. 获取上次 Agent 交互后的所有消息
   ↓
6. 格式化为 XML prompt
   ↓
7. 启动容器 Agent
   ↓
8. Agent 处理 → 返回结果
   ↓
9. 发送 WhatsApp 响应
```

### 6.2 IPC 流

```
Container Agent
   ↓ mcp__nanoclaw__send_message()
writeIpcFile(/workspace/ipc/{group}/messages/*.json)
   ↓
Host IPC Watcher (1s 轮询)
   ↓
验证群组身份
   ↓
sock.sendMessage() to WhatsApp
```

---

## 七、目录结构

```
nanoclaw/
├── src/                    # 主进程源码
│   ├── index.ts            # WhatsApp + 路由
│   ├── container-runner.ts # 容器执行
│   ├── task-scheduler.ts   # 任务调度
│   ├── db.ts               # 数据库操作
│   ├── mount-security.ts   # 挂载安全验证
│   └── ...
├── container/
│   ├── agent-runner/       # 容器内 Agent 代码
│   │   └── src/
│   │       ├── index.ts    # Agent 入口
│   │       └── ipc-mcp.ts  # IPC MCP Server
│   ├── Dockerfile
│   └── build.sh
├── groups/
│   ├── global/             # 全局内存
│   ├── main/               # Main Group
│   └── {group-name}/       # 其他群组
├── data/                   # 应用状态
│   ├── sessions.json       # 会话 ID
│   ├── registered_groups.json
│   └── ipc/                # IPC 通信
└── store/
    ├── auth/               # WhatsApp 认证
    └── messages.db         # SQLite 数据库
```

---

## 八、与 OpenClaw/Kilocode 对比

| 维度 | NanoClaw | OpenClaw | Kilocode |
|------|----------|----------|----------|
| **平台** | CLI + WhatsApp | CLI + 多通道 | VS Code Extension |
| **代码复杂度** | 极简 (10 文件) | 复杂 (52+ 模块) | 中等 |
| **安全模型** | 容器隔离 | 应用级权限 | VS Code 沙箱 |
| **扩展机制** | Skill 变换 | 插件系统 | MCP 协议 |
| **验证机制** | ❌ 无 | ❌ 无 | ❌ 无 |
| **会话管理** | 群组隔离 | 多通道共享 | 工作区绑定 |
