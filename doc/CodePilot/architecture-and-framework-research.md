# CodePilot 计算架构与框架研究

## 项目概述

CodePilot 是一个面向 Claude Code 的桌面 GUI 客户端，基于 Electron + Next.js 构建，为用户提供了通过可视化界面与 Claude Code 进行对话、编码和项目管理的能力，而非传统的终端交互方式。

## 技术栈

| 层级 | 技术 |
|---|---|
| 框架 | Next.js 16 (App Router) |
| 桌面外壳 | Electron 40 |
| UI 组件 | Radix UI + shadcn/ui |
| 样式 | Tailwind CSS 4 |
| 动画 | Motion (Framer Motion) |
| AI 集成 | Claude Agent SDK |
| 数据库 | better-sqlite3 (嵌入式、用户级) |
| Markdown | react-markdown + remark-gfm + rehype-raw + Shiki |
| 流式传输 | Vercel AI SDK helpers + Server-Sent Events |
| 图标 | Hugeicons + Lucide |
| 测试 | Playwright |
| CI/CD | GitHub Actions |
| 构建/打包 | electron-builder + esbuild |

## 核心架构

### 1. 分层架构

```
┌─────────────────────────────────────────┐
│         Electron 桌面外壳                │
│  - 窗口管理                             │
│  - 系统集成 (菜单、托盘、系统托盘)        │
│  - 本地进程管理                         │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│        Next.js 后端服务                  │
│  - API Routes (REST + SSE)              │
│  - Claude Agent SDK 集成                 │
│  - SQLite 数据库操作                     │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│        Next.js 前端 (React)              │
│  - ChatView 聊天界面                     │
│  - 流式消息渲染                          │
│  - 权限审批 UI                          │
│  - 文件树/项目面板                       │
└─────────────────────────────────────────┘
```

### 2. Electron 主进程 (electron/main.ts)

Electron 主进程负责：
- 创建和管理 BrowserWindow
- 启动嵌入式 Next.js 服务器
- 处理系统级事件（安装向导、自动更新）
- 进程生命周期管理

关键特性：
- 自动端口分配：主进程会启动 Next.js 服务器并连接到随机可用端口
- 优雅关闭：实现优雅的进程终止逻辑
- WAL 模式：SQLite 使用 WAL 模式实现并发读取

### 3. Claude Agent SDK 集成 (src/lib/claude-client.ts)

核心文件 `claude-client.ts` 是整个应用的关键，它：

1. **查询函数封装**
   - 使用 `@anthropic-ai/claude-agent-sdk` 的 `query()` 函数
   - 将用户消息和历史记录传递给 Claude Code CLI
   - 支持会话恢复 (resume) 功能

2. **流式响应处理**
   - 将 Claude Agent SDK 的响应转换为 SSE 事件
   - 支持多种事件类型：`text`, `tool_use`, `tool_result`, `tool_output`, `status`, `result`, `permission_request`, `tool_timeout`, `mode_changed`, `task_update`, `error`

3. **消息类型处理**
   - `SDKAssistantMessage`: AI 助手消息，包含文本和工具调用块
   - `SDKUserMessage`: 用户消息，包含工具执行结果
   - `SDKSystemMessage`: 系统消息，用于初始化和状态更新
   - `SDKToolProgressMessage`: 工具执行进度
   - `SDKResultMessage`: 最终结果，包含 token 使用统计

### 4. API 路由架构 (src/app/api/)

```
/api/
├── chat/
│   ├── route.ts              # 核心聊天接口，支持 SSE 流式
│   ├── messages/             # 消息 CRUD
│   ├── mode/                 # 模式切换 (code/plan/ask)
│   ├── permission/           # 权限审批
│   └── sessions/            # 会话管理
├── files/
│   ├── browse/               # 文件树浏览
│   ├── preview/             # 文件预览
│   └── raw/                  # 原始文件内容
├── plugins/
│   └── mcp/                  # MCP 服务器配置
├── skills/                   # Skill 管理
├── settings/                 # 设置管理
└── tasks/                    # 任务跟踪
```

### 5. 数据库架构 (src/lib/db.ts)

SQLite 数据库 `~/.codepilot/codepilot.db` 包含以下表：

```sql
-- 会话表
chat_sessions (
  id, title, created_at, updated_at, 
  model, system_prompt, working_directory, sdk_session_id
)

-- 消息表
messages (
  id, session_id, role (user/assistant), 
  content, created_at, token_usage
)

-- 设置表
settings (id, key, value)

-- 任务表
tasks (
  id, session_id, title, status, 
  description, created_at, updated_at
)

-- API Provider 表
api_providers (...)

-- 权限请求表
permission_requests (...)

-- 图像任务表
media_jobs, media_job_items, media_context_events
```

### 6. 客户端流式处理 (src/lib/stream-session-manager.ts)

使用 `globalThis` 模式在 Next.js HMR 环境下保持状态：

```typescript
// 全局单例模式
const GLOBAL_KEY = '__streamSessionManager__';
function getStreamsMap(): Map<string, ActiveStream> {
  if (!globalThis[GLOBAL_KEY]) {
    globalThis[GLOBAL_KEY] = new Map();
  }
  return globalThis[GLOBAL_KEY];
}
```

流式会话管理器维护：
- 活跃的流会话
- 消息快照 (SessionStreamSnapshot)
- 事件监听器集合
- 空闲超时和垃圾回收计时器

### 7. SSE 事件流 (src/hooks/useSSEStream.ts)

客户端使用 SSE 事件与后端通信，事件类型包括：

| 事件类型 | 描述 |
|---|---|
| `text` | 实时文本流 |
| `tool_use` | 工具调用开始 |
| `tool_result` | 工具执行结果 |
| `tool_output` | 工具输出（实时） |
| `tool_progress` | 工具执行进度 |
| `status` | 状态消息 |
| `result` | 最终结果（含 token 使用） |
| `permission_request` | 权限请求 |
| `tool_timeout` | 工具超时 |
| `mode_changed` | 模式变更 |
| `task_update` | 任务更新 |
| `error` | 错误消息 |

### 8. 权限系统 (src/lib/permission-registry.ts)

权限注册表管理工具使用的审批流程：

- 使用 `globalThis` 跨模块实例共享待处理权限
- 5 分钟超时自动拒绝
- 支持中止信号处理客户端断开连接
- 双重写入：先持久化到数据库，再解决内存中的 Promise

## MCP 集成

CodePilot 支持 Model Context Protocol (MCP) 服务器：

```typescript
// MCP 配置类型
type MCPServerConfig = {
  type: 'stdio' | 'sse' | 'http';
  command?: string;
  args?: string[];
  env?: Record<string, string>;
  url?: string;
  headers?: Record<string, string>;
}
```

支持三种传输类型：
- **stdio**: 标准输入/输出通信
- **sse**: Server-Sent Events
- **http**: HTTP 请求

## Skills 系统

CodePilot 复用 Claude Code 的 skills 系统：

```typescript
// Skill 来源
type SkillSource = "global" | "project" | "plugin" | "installed";

// Skill 目录
- ~/.claude/commands (全局)
- .claude/commands (项目级)
- ~/.claude/plugins/marketplaces/*/commands (插件)
- ~/.agents/skills (已安装)
- ~/.claude/skills (Claude 官方)
```

## 关键设计模式

### 1. 会话锁定机制

使用数据库锁防止并发请求冲突：

```typescript
acquireSessionLock(session_id, lockId, `chat-${process.pid}`, 600)
```

### 2. 环境变量净化

处理 Windows 上的环境变量问题：

```typescript
// 移除空字节和控制字符
function sanitizeEnvValue(value: string): string {
  return value.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '');
}
```

### 3. Claude 路径解析

Windows 上的 npm CLI 包装器解析：

```typescript
// 解析 .cmd 包装器获取真实 .js 脚本路径
function resolveScriptFromCmd(cmdPath: string): string | undefined
```

## 构建与发布

- **macOS**: DMG (arm64 + x64)
- **Windows**: NSIS 安装包 (x64 + arm64)
- **Linux**: AppImage, deb, rpm

CI 自动构建并发布到 GitHub Releases。
