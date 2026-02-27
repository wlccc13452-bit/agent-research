# TinyClaw 架构与框架研究

## 项目概述

**TinyClaw** 是一个从 OpenClaw 提取的精简版 AI 助手平台，约 **11K 行 TypeScript** 代码，功能齐全。

| 维度 | 数据 |
|------|------|
| **源文件数** | 99 个 `.ts` 文件 |
| **代码行数** | ~11,000 行 |
| **模块数** | 18 个子系统 |
| **测试文件** | 24 个 |
| **依赖** | 核心依赖 12 个，可选依赖 4 个 |

---

## 核心架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              TinyClaw                                   │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────────────────────┐  │
│  │   CLI   │   │ Gateway │   │ Channels│   │       Plugins           │  │
│  │ (REPL)  │   │ (HTTP)  │   │ (WA/TG) │   │   (User Extensions)     │  │
│  └────┬────┘   └────┬────┘   └────┬────┘   └───────────┬─────────────┘  │
│       │             │             │                    │                │
│       └─────────────┴──────┬──────┴────────────────────┘                │
│                            ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                      Pipeline (pipeline.ts)                     │    │
│  │  dispatch → finalizeInbound → processDirectives → orchestrate   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                            │                                            │
│                            ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    Agent Runner (runner.ts)                     │    │
│  │      runAgent → createTinyClawSession → retry loop              │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                            │                                            │
│                            ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                 pi-coding-agent (External SDK)                  │    │
│  │            AgentSession + SessionManager + Tools                │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                            │                                            │
│                            ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    AI Providers (Anthropic/OpenAI)              │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 子系统详解

### 1. 消息管道 (Pipeline)

**文件**: `src/pipeline/pipeline.ts` (~730 行)

核心入口点，处理所有消息流：

```typescript
export async function dispatch(params: {
  source: MsgContext["source"];  // "cli" | "gateway" | "channel"
  body: string;
  config: TinyClawConfig;
  channelId?: string;
  peerId?: string;
  // ...
}): Promise<PipelineResult>
```

**处理流程**:

```
dispatch()
  ├── isDuplicate()           // 消息去重 (60s TTL)
  ├── collectBuffer()         // 收集模式 (批量快速消息)
  ├── finalizeInbound()       // 解析会话键、注入检测
  ├── processDirectives()     // 处理 ++think, ++model 指令
  ├── processCommand()        // 处理 /new, /compact, /status
  ├── orchestrate()           // 运行 Agent
  ├── deliver()               // 分块发送到频道
  └── TTS                     // 可选语音合成
```

### 2. Agent Runner

**文件**: `src/agent/runner.ts` (~215 行)

核心 Agent 执行引擎，包含重试逻辑：

```typescript
export async function runAgent(params: {
  config: TinyClawConfig;
  prompt: string;
  sessionName: string;
  workspaceDir: string;
  // ...
}): Promise<RunResult>
```

**重试策略**:

| 错误类型 | 处理方式 |
|---------|---------|
| Context Overflow | 截断工具结果 → 压缩会话 |
| Rate Limit | 指数退避 + 旋转 Key |
| Timeout | 短暂退避，重试同一 Key |
| Auth/Billing | 标记 Key 失败，切换 Fallback 模型 |
| Thinking Error | 降级 thinking level (high→medium→low→off) |
| Format Error | 不重试，直接抛出 |

### 3. 会话管理 (Session)

**文件**: `src/agent/session.ts` (~250 行)

会话生命周期管理，包含文件锁和崩溃修复：

**核心特性**:

1. **文件锁** (`acquireSessionLock`)
   - 使用 `O_CREAT | O_EXCL` 独占创建
   - 检测陈旧锁 (>30min 或进程已死)
   - 支持递归锁

2. **崩溃修复** (`repairSessionFileIfNeeded`)
   - 逐行解析 JSONL
   - 丢弃无法解析的行
   - 自动备份损坏文件

3. **多 Agent 会话键解析**
   ```typescript
   // 格式: "agentId:channelId:accountId:peerId"
   export function parseSessionKey(input: string): SessionKey
   ```

### 4. 安全层 (Security)

**文件**: `src/security/security.ts` (~276 行)

**10 层策略引擎**:

| 优先级 | 层级 | 说明 |
|-------|------|------|
| 1 | Hardcoded Deny | `eval`, `exec_raw`, `system` 永久禁止 |
| 2 | Config deniedTools | 配置文件禁止列表 |
| 3 | Config elevatedTools | 需要确认的工具 |
| 4 | Per-agent allowlist | 每个 Agent 的工具白名单 |
| 5 | Per-channel restrictions | 频道级别限制 |
| 6 | Max tool calls | 单轮最大调用次数 (默认 50) |
| 7 | Exec approval | 命令执行审批 |
| 8 | SSRF check | 私有 IP 阻断 |
| 9 | Tool policy mode | auto/interactive/strict |
| 10 | Default allow | 默认允许 |

**SSRF 防护**:

```typescript
const PRIVATE_IP_RANGES = [
  /^127\./, /^10\./, /^172\.(1[6-9]|2\d|3[01])\./, /^192\.168\./,
  /^169\.254\./, /^0\./, /^::1$/, /^fc/i, /^fd/i, /^fe80:/i,
];
```

**注入检测**:

```typescript
const INJECTION_PATTERNS = [
  /ignore\s+(all\s+)?previous\s+instructions/i,
  /you\s+are\s+now\s+(a|an)\s+/i,
  /system\s*prompt\s*[:=]/i,
  // ...
];
```

### 5. Docker 沙箱 (Sandbox)

**文件**: `src/sandbox/sandbox.ts` (~235 行)

使用 `child_process.spawn("docker", ...)` 无额外依赖：

```typescript
export interface SandboxConfig {
  enabled: boolean;
  image: string;           // 默认: "tinyclaw-sandbox"
  scope: "session" | "shared";
  memoryLimit: string;     // 默认: "512m"
  cpuLimit: string;        // 默认: "1"
  networkMode: "none" | "bridge";
  mountWorkspace: boolean;
  timeoutSec: number;      // 默认: 300
}
```

**容器命名规则**:

```typescript
export function containerName(sessionKey: string): string {
  const slug = sessionKey
    .replace(/[^a-zA-Z0-9_.-]/g, "-")
    .replace(/-+/g, "-")
    .slice(0, 60);
  return `tinyclaw-sandbox-${slug}`;
}
```

### 6. Gateway 服务器

**文件**: `src/gateway/gateway.ts` (~544 行)

HTTP + WebSocket 服务器，支持 23 个 RPC 方法：

**架构**:

```
┌─────────────────────────────────────────────────┐
│                  Gateway Server                  │
├─────────────────────────────────────────────────┤
│  HTTP Server                                     │
│  ├── /webhook/whatsapp  (WhatsApp Webhook)      │
│  ├── /webhook/telegram  (Telegram Webhook)      │
│  ├── /webhook/generic   (Generic Webhook)       │
│  ├── /v1/chat/completions (OpenAI Compatible)   │
│  ├── /v1/models                                 │
│  ├── /health                                    │
│  └── / or /chat (WebChat UI)                    │
├─────────────────────────────────────────────────┤
│  WebSocket Server (JSON-RPC 2.0)                │
│  ├── chat.send / chat.stream                    │
│  ├── sessions.list / get / clear                │
│  ├── config.get / reload                        │
│  ├── cron.list / add / remove                   │
│  ├── exec.pending / approve / deny              │
│  └── presence.list / upsert                     │
└─────────────────────────────────────────────────┘
```

**Presence 系统**:

```typescript
export interface PresenceEntry {
  id: string;
  role: "ui" | "cli" | "webchat" | "node" | "backend";
  connectedAt: number;
  lastSeen: number;
}
// TTL: 5 分钟无心跳自动清理
```

---

## 数据流

### 消息处理流程

```
用户消息
    │
    ▼
┌─────────────────┐
│    Channel      │ ← WhatsApp/Telegram/Discord/Slack
│   (Adapter)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Gateway      │ ← HTTP Webhook / WebSocket
│   (Server)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Pipeline     │ ← dispatch()
│  (Dispatcher)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Agent Runner   │ ← runAgent()
│   (Executor)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  pi-coding-agent│ ← 外部 SDK
│   (Session)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   AI Provider   │ ← Anthropic/OpenAI/Google
│   (LLM API)     │
└─────────────────┘
```

---

## 配置系统

**配置文件位置**: `~/.config/tinyclaw/config.json5`

**热重载机制**:

```typescript
// config/watcher.ts
const watcher = startConfigWatcher(configPath, async () => {
  const newConfig = loadConfig();
  const changed = diffConfig(ctx.config, newConfig);
  if (requiresRestart(changed)) {
    log.warn("Config change requires restart: ...");
  }
  ctx.config = newConfig;
  broadcast(ctx, "config.reload", { changed });
}, config.gateway?.reload?.debounceMs ?? 2000);
```

---

## 工具系统

**内置工具** (19 个):

| 类别 | 工具 |
|------|------|
| **文件操作** | `read`, `write`, `edit`, `glob`, `grep` |
| **执行** | `bash` (可沙箱化) |
| **浏览器** | `browser_navigate`, `browser_click`, `browser_type`, `browser_screenshot`, `browser_snapshot` |
| **Web** | `web_search`, `web_fetch` |
| **记忆** | `memory_search`, `memory_store` |
| **定时** | `cron_list`, `cron_set`, `cron_delete` |
| **消息** | `message_send`, `message_react`, `message_typing` |
| **其他** | `tts_speak`, `image_generate`, `apply_patch`, `session_*` |

**参数别名** (兼容不同模型):

```typescript
const PARAM_ALIASES: Record<string, Record<string, string>> = {
  read:  { file_path: "path", filePath: "path" },
  write: { file_path: "path", filePath: "path" },
  edit:  { file_path: "path", old_string: "oldText", ... },
};
```

---

## 插件系统

**文件**: `src/plugin/plugin.ts`

**4 种发现源**:

1. Bundled (内置)
2. Config (配置文件)
3. User Directory (`~/.config/tinyclaw/plugins/`)
4. Workspace (`.tinyclaw/plugins/`)

**10 种注册方法**:

```typescript
interface TinyClawPluginApi {
  registerTool(tool: AgentTool): void;
  registerHook(event: HookEvent, handler: HookHandler): void;
  registerChannel(def: ChannelDef): void;
  registerHttpRoute(path: string, method: string, handler: HttpHandler): void;
  registerService(name: string, start: () => Promise<void>, stop: () => Promise<void>): void;
  registerCron(job: CronJob): void;
  registerMemoryBackend(backend: MemoryBackend): void;
  registerModelResolver(resolver: ModelResolver): void;
  registerAuthProvider(provider: AuthProvider): void;
  registerCommand(name: string, handler: CommandHandler): void;
}
```

---

## 与其他项目对比

| 维度 | TinyClaw | NanoClaw | OpenClaw |
|------|----------|----------|----------|
| **代码规模** | ~11K 行 | ~2K 行 | ~50K+ 行 |
| **架构风格** | 单体模块化 | 容器隔离 | 微服务 |
| **消息渠道** | 4 种 (完整实现) | WhatsApp | 4+ 种 |
| **沙箱机制** | Docker | 容器级 | Docker |
| **插件系统** | ✅ 10 种注册 | ❌ | ✅ 更丰富 |
| **网关服务** | ✅ HTTP+WS | ❌ | ✅ |
| **会话持久化** | JSONL + 文件锁 | SQLite | 多种后端 |
| **安全层级** | 10 层策略 | 基础 | 更复杂 |
| **外部依赖** | pi-coding-agent SDK | Claude Agent SDK | 自建框架 |

---

## 关键设计模式

### 1. 单文件模块

每个子系统自包含在一个文件中：

```
src/agent/runner.ts     // 所有 runner 相关类型 + 实现
src/pipeline/pipeline.ts // 所有 pipeline 逻辑
src/security/security.ts // 所有安全相关功能
```

**优点**: 易于理解，减少导航成本

### 2. 懒加载

重型依赖延迟加载：

```typescript
// 仅在需要时加载
const { createAgentSession } = await import("@mariozechner/pi-coding-agent");
const { launchBrowser } = await import("../browser/browser.js");
```

### 3. 配置驱动

几乎所有行为可通过配置调整：

```typescript
// Zod Schema 定义配置类型
export const TinyClawConfigSchema = z.object({
  agent: z.object({ ... }).optional(),
  session: z.object({ ... }).optional(),
  gateway: z.object({ ... }).optional(),
  // ...
});
```

### 4. XDG 路径规范

所有持久化数据存储在标准位置：

```
~/.config/tinyclaw/
├── config.json5          # 主配置
├── sessions/             # 会话文件
├── memory.db             # 记忆数据库
├── exec-allowlist.json   # 命令白名单
├── auth-state.json       # 认证状态
├── plugins/              # 用户插件
└── skills/               # 用户技能
```

---

## 总结

TinyClaw 是一个**高度精简但功能完整**的 AI 助手平台：

1. **架构简洁**: 单文件模块化，易于理解
2. **功能完整**: 4 种消息渠道 + 19 种工具 + 23 个 RPC 方法
3. **安全可靠**: 10 层安全策略 + 文件锁 + 崩溃修复
4. **可扩展**: 插件系统 + 热重载
5. **容器隔离**: Docker 沙箱保护

相比 NanoClaw 的极简和 OpenClaw 的复杂，TinyClaw 在**功能与复杂度之间取得平衡**。
