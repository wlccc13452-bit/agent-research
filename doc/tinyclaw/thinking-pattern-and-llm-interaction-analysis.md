# TinyClaw 思维模式与 LLM 交互分析

## 概述

TinyClaw 使用 **@mariozechner/pi-coding-agent** 外部 SDK 作为 Agent 核心，自身不实现思维链逻辑。本文分析其交互设计特点。

---

## Agent 核心架构

### 外部 SDK 依赖

```typescript
// package.json
{
  "dependencies": {
    "@mariozechner/pi-agent-core": "0.52.8",
    "@mariozechner/pi-ai": "0.52.8",
    "@mariozechner/pi-coding-agent": "0.52.8"
  }
}
```

**关键类型来源**:

```typescript
import type { ThinkingLevel } from "@mariozechner/pi-agent-core";
import type { AgentSession, AgentSessionEvent } from "@mariozechner/pi-coding-agent";
```

### 会话创建流程

```typescript
// src/agent/session.ts
export async function createTinyClawSession(params: {
  config: TinyClawConfig;
  sessionName: string;
  workspaceDir: string;
  // ...
}): Promise<TinyClawSession> {
  // 1. 解析模型
  const resolved = resolveModel(provider, modelId, config);
  
  // 2. 组装工具
  const { builtinTools, customTools } = assembleTinyClawTools(workspaceDir, config);
  
  // 3. 创建 SessionManager
  if (ephemeral) {
    sessionManager = SessionManager.inMemory();
  } else {
    const sessionFile = resolveSessionFile(sessionName);
    await acquireSessionLock(sessionFile);
    sessionManager = SessionManager.open(sessionFile);
  }
  
  // 4. 创建 AgentSession (外部 SDK)
  const result = await createAgentSession({
    cwd: workspaceDir,
    model: resolved.model,
    thinkingLevel,
    tools: builtinTools,
    customTools: customTools,
    authStorage: resolved.authStorage,
    modelRegistry: resolved.modelRegistry,
    sessionManager,
  });
  
  // 5. 构建系统提示
  const systemPrompt = buildSystemPrompt({ ... });
  result.session.agent.setSystemPrompt(systemPrompt);
  
  return { session, resolved, sessionManager, ... };
}
```

---

## LLM 交互流程

### 1. 消息发送

```typescript
// src/agent/runner.ts
export async function runAgent(params): Promise<RunResult> {
  const { session } = tinyClawSession;
  
  // 订阅事件
  const unsubscribe = session.subscribe((event: AgentSessionEvent) => {
    if (event.type === "message_update") {
      // 文本增量更新
      const ame = event.assistantMessageEvent;
      if (ame.type === "text_delta") {
        responseText += ame.delta;
        options.onText?.(ame.delta);
      }
    }
    
    if (event.type === "tool_execution_start") {
      options.onToolEvent?.({ type: "start", toolName: event.toolName, ... });
    }
    
    if (event.type === "tool_execution_end") {
      options.onToolEvent?.({ type: "end", toolName: event.toolName, ... });
    }
  });
  
  // 发送消息
  await session.prompt(prompt);
  
  return { text: responseText, tinyClawSession };
}
```

### 2. 事件类型

```typescript
type AgentSessionEvent =
  | { type: "message_update"; assistantMessageEvent: TextDeltaEvent }
  | { type: "message_end"; usage: UsageInfo }
  | { type: "tool_execution_start"; toolName: string; args: unknown }
  | { type: "tool_execution_end"; toolName: string; result: unknown }
  | { type: "auto_compaction_start" }
  | { type: "auto_compaction_end"; result: CompactionResult }
  | { type: "thinking_start" | "thinking_delta" | "thinking_end" };
```

### 3. 流式响应

```
LLM API
    │
    ▼ Stream
pi-coding-agent (AgentSession)
    │
    ▼ Events (subscribe)
TinyClaw Runner (onText, onToolEvent)
    │
    ▼ Callbacks
Pipeline (onChunk)
    │
    ▼ Channel Adapter
用户 (分块显示)
```

---

## 重试与错误处理

### 错误分类

```typescript
// src/auth/keys.ts
export type FailureReason = "auth" | "rate_limit" | "billing" | "timeout" | "format";

export function classifyFailoverReason(error: unknown): FailureReason {
  const msg = describeError(error).toLowerCase();
  
  if (msg.includes("rate limit") || msg.includes("429")) return "rate_limit";
  if (msg.includes("unauthorized") || msg.includes("401") || msg.includes("invalid api key")) return "auth";
  if (msg.includes("billing") || msg.includes("insufficient") || msg.includes("quota")) return "billing";
  if (msg.includes("timeout") || msg.includes("etimedout")) return "timeout";
  if (msg.includes("invalid") || msg.includes("format") || msg.includes("parse")) return "format";
  
  return "auth"; // 默认
}
```

### 重试策略

```typescript
// src/agent/runner.ts
while (retries <= MAX_RETRIES) {
  try {
    await session.prompt(prompt);
    markKeySuccess(provider, modelId);
    return { text: responseText, tinyClawSession };
    
  } catch (error) {
    const reason = classifyFailoverReason(error);
    
    // 1. Context Overflow → 先截断工具结果，再压缩会话
    if (isContextOverflowError(error)) {
      if (!truncatedToolResults) {
        const { truncated } = truncateOversizedToolResults(messages);
        if (truncated > 0) { truncatedToolResults = true; continue; }
      }
      await compactSession(session);
      compacted = true;
      continue;
    }
    
    // 2. Rate Limit → 指数退避
    if (reason === "rate_limit") {
      const delayMs = Math.min(1000 * Math.pow(2, retries), 30000);
      markKeyFailed(provider, modelId, reason);
      await sleep(delayMs + jitter);
      continue;
    }
    
    // 3. Timeout → 短暂退避
    if (reason === "timeout") {
      await sleep(Math.min(500 * Math.pow(2, retries), 5000));
      continue;
    }
    
    // 4. Auth/Billing → 切换 Fallback 模型
    if (reason === "auth" || reason === "billing") {
      markKeyFailed(provider, modelId, reason);
      const next = resolveNextFallback(fallbackIdx, fallbackChain);
      if (next) {
        tinyClawSession = await createTinyClawSession({ provider: next.provider, ... });
        continue;
      }
      throw error;
    }
    
    // 5. Thinking Error → 降级
    if (errMsg.includes("thinking")) {
      thinkingLevel = downgradeThinking(thinkingLevel);
      continue;
    }
    
    throw error;
  }
}
```

### Thinking Level 降级

```typescript
const THINKING_FALLBACK: ThinkingLevel[] = ["high", "medium", "low", "off"];

function downgradeThinking(current: ThinkingLevel): ThinkingLevel {
  const idx = THINKING_FALLBACK.indexOf(current);
  return THINKING_FALLBACK[Math.min(idx + 1, THINKING_FALLBACK.length - 1)];
}
```

---

## 认证弹性 (Auth Resilience)

### 多 Key 轮换

```typescript
// src/auth/keys.ts

// Key 池管理
const keyPools = new Map<string, { keys: ApiKey[]; currentIndex: number }>();
const cooldowns = new Map<string, CooldownState>();

export function resolveApiKey(provider: string, modelId: string): { apiKey: string } {
  const pool = keyPools.get(provider);
  if (!pool) return { apiKey: process.env.ANTHROPIC_API_KEY ?? "" };
  
  // 轮换到下一个可用的 Key
  for (let i = 0; i < pool.keys.length; i++) {
    const key = pool.keys[pool.currentIndex];
    const state = cooldowns.get(key.id);
    
    // 检查冷却状态
    if (!state || state.cooldownUntil < Date.now()) {
      pool.currentIndex = (pool.currentIndex + 1) % pool.keys.length;
      return { apiKey: key.value };
    }
    
    pool.currentIndex = (pool.currentIndex + 1) % pool.keys.length;
  }
  
  // 所有 Key 都在冷却，使用最早恢复的
  return findEarliestRecovery(pool);
}
```

### 持久化冷却

```typescript
// 冷却状态保存到文件
const AUTH_STATE_FILE = "~/.config/tinyclaw/auth-state.json";

interface CooldownState {
  keyId: string;
  reason: FailureReason;
  cooldownUntil: number;
  failureCount: number;
}

// 冷却时间递增
const COOLDOWN_SCHEDULE = {
  rate_limit: [60000, 300000, 1500000, 3600000],  // 1min → 5min → 25min → 1hr
  billing: [18000000, 36000000, 72000000, 86400000], // 5hr → 10hr → 20hr → 24hr
};
```

---

## 会话持久化

### JSONL 格式

```
# ~/.config/tinyclaw/sessions/session-name.jsonl
{"type":"user","content":"Hello","timestamp":"2026-02-25T10:00:00Z"}
{"type":"assistant","content":"Hi! How can I help?","timestamp":"2026-02-25T10:00:05Z"}
{"type":"tool_call","tool":"bash","args":{"command":"ls"},"timestamp":"..."}
{"type":"tool_result","tool":"bash","output":"file1.txt\nfile2.txt","timestamp":"..."}
```

### 文件锁机制

```typescript
// src/agent/session.ts

export async function acquireSessionLock(sessionFile: string, timeoutMs = 10000): Promise<void> {
  const lockPath = sessionFile + ".lock";
  const deadline = Date.now() + timeoutMs;
  
  while (Date.now() < deadline) {
    try {
      // 独占创建锁文件
      const fd = fs.openSync(lockPath, O_WRONLY | O_CREAT | O_EXCL);
      fs.writeSync(fd, JSON.stringify({ pid: process.pid, createdAt: Date.now() }));
      fs.closeSync(fd);
      return;
      
    } catch (err: any) {
      if (err.code !== "EEXIST") throw err;
      
      // 检查陈旧锁
      const { pid, createdAt } = JSON.parse(fs.readFileSync(lockPath, "utf-8"));
      const stale = (Date.now() - createdAt > 30 * 60 * 1000) || !isPidAlive(pid);
      if (stale) {
        fs.unlinkSync(lockPath);
        continue;
      }
      
      // 指数退避重试
      await sleep(delay);
      delay = Math.min(delay * 2, 1000);
    }
  }
  
  throw new Error(`Failed to acquire session lock within ${timeoutMs}ms`);
}
```

### 崩溃修复

```typescript
export function repairSessionFileIfNeeded(sessionFile: string): void {
  const raw = fs.readFileSync(sessionFile, "utf-8");
  const lines = raw.split("\n");
  const valid: string[] = [];
  let repaired = false;
  
  for (const line of lines) {
    try {
      JSON.parse(line.trim());
      valid.push(line);
    } catch {
      repaired = true;
      log.warn(`Dropping unparseable session line: ${line.slice(0, 80)}...`);
    }
  }
  
  if (repaired) {
    // 备份损坏文件
    fs.copyFileSync(sessionFile, `${sessionFile}.bak-${process.pid}-${Date.now()}`);
    // 写入修复后的内容
    fs.writeFileSync(sessionFile, valid.join("\n"));
  }
}
```

---

## 消息处理管道

### Pipeline 阶段

```typescript
// src/pipeline/pipeline.ts

export async function dispatch(params): Promise<PipelineResult> {
  // 1. 去重
  if (isDuplicate(channelId, messageId)) return { sessionKey: "", reply: undefined };
  
  // 2. 收集模式 (批量快速消息)
  if (collectMode) {
    return collectBuffer(key, body, windowMs, async (combined) => {
      return dispatch({ ...params, body: combined, _collected: true });
    });
  }
  
  // 3. 构建上下文
  const ctx: MsgContext = { ... };
  
  // 4. 确定入站
  await finalizeInbound(ctx);
  
  // 5. 配对检查
  if (pairingRequired && !store.isAllowed(channelId, peerId)) {
    return sendPairingCode(ctx);
  }
  
  // 6. 处理指令 (++think, ++model)
  processDirectives(ctx);
  
  // 7. 处理命令 (/new, /compact)
  const cmdResult = await processCommand(ctx);
  if (cmdResult) return { reply: cmdResult };
  
  // 8. 运行 Agent
  const result = await orchestrate(ctx, onChunk);
  
  // 9. 分块发送
  if (ctx.channel && result.chunks?.length) {
    await deliver(ctx, result.chunks);
  }
  
  return result;
}
```

### 指令处理

```typescript
const DIRECTIVE_RE = /^(?:\+\+|\/)(\w+)\s+(\S+)/gm;

function processDirectives(ctx: MsgContext): void {
  const matches = [...ctx.body.matchAll(DIRECTIVE_RE)];
  
  for (const [, key, value] of matches) {
    switch (key) {
      case "think":
        if (["off", "low", "medium", "high"].includes(value)) {
          ctx.directives.thinkOverride = value;
        }
        break;
      case "model":
        ctx.directives.modelOverride = value;
        break;
      case "exec":
        ctx.directives.execOverride = value; // auto | interactive | deny
        break;
    }
  }
  
  // 指令持久化到会话
  sessionDirectives.set(ctx.sessionKey, { ...ctx.directives });
  
  // 从消息体中移除指令
  ctx.body = ctx.body.replace(DIRECTIVE_RE, "").trim();
}
```

---

## 系统提示构建

### Bootstrap 文件加载

```typescript
// src/agent/system-prompt.ts

const BOOTSTRAP_ORDER = [
  "SOUL.md", "IDENTITY.md", "USER.md", "TOOLS.md",
  "TINYCLAW.md", "CLAUDE.md", "AGENTS.md", "BOOTSTRAP.md",
  ".tinyclaw", ".claude"
];

export function loadBootstrapContent(workspaceDir: string): string {
  for (const name of BOOTSTRAP_ORDER) {
    const path = join(workspaceDir, name);
    if (fs.existsSync(path)) {
      return fs.readFileSync(path, "utf-8");
    }
  }
  return "";
}
```

### 系统提示组装

```typescript
export function buildSystemPrompt(params: SystemPromptParams): string {
  const parts: string[] = [];
  
  // 1. Bootstrap 内容 (SOUL.md 等)
  if (params.bootstrapContent) {
    parts.push(params.bootstrapContent);
  }
  
  // 2. 工具指导
  if (params.toolNames.length > 0) {
    parts.push(`Available tools: ${params.toolNames.join(", ")}`);
  }
  
  // 3. 工作目录
  parts.push(`Working directory: ${params.workspaceDir}`);
  
  // 4. 模型信息
  parts.push(`Model: ${params.model}`);
  
  // 5. Agent ID (多 Agent 场景)
  if (params.agentId) {
    parts.push(`Agent ID: ${params.agentId}`);
  }
  
  // 6. 配置驱动的个性
  const identity = params.config.agent?.identity;
  if (identity) {
    parts.push(`Identity: ${identity.name ?? "Assistant"}`);
    if (identity.emoji) parts.push(`Emoji: ${identity.emoji}`);
  }
  
  return parts.join("\n\n");
}
```

---

## 潜在问题与不足

### 1. 思维链逻辑外包

**问题**: TinyClaw 不自己实现思维链，完全依赖 `pi-coding-agent` SDK

```typescript
// 思维级别直接传给外部 SDK
await createAgentSession({
  thinkingLevel,  // 直接传递，无自定义逻辑
  ...
});
```

**影响**:
- 无法自定义思维模式
- 依赖外部 SDK 的行为
- 难以调试思维过程

### 2. 无验证机制

**问题**: 没有 Hook 验证或结果验证

```typescript
// NanoClaw 有验证 Hook
// TinyClaw 的 Hook 只能 transform 或 abort，不能验证结果
api.registerHook("message_inbound", async (event, data) => {
  return { transform: { body: data.body.toUpperCase() } };
  return { abort: true, abortMessage: "Blocked" };
  // ❌ 没有验证返回值
});
```

### 3. 消息去重仅 60 秒

```typescript
const DEDUP_TTL_MS = 60_000; // 硬编码

// 短时间内同一消息不会重复处理
// 但超过 60 秒后可能重复处理相同消息
```

### 4. 缺乏事务性

```typescript
// 会话状态更新没有事务保证
tinyClawSession.usage.inputTokens += runUsage.inputTokens;
// 如果这里崩溃，usage 可能不完整
```

### 5. 配置热重载限制

```typescript
// 某些配置需要重启才能生效
if (requiresRestart(changed)) {
  log.warn("Config change requires restart: ...");
  // ❌ 不会自动重启，只记录警告
}
```

---

## 与其他项目对比

| 维度 | TinyClaw | NanoClaw | OpenClaw |
|------|----------|----------|----------|
| **思维链实现** | 外部 SDK | 外部 SDK | 自建 |
| **验证机制** | ❌ | ❌ | ❌ |
| **会话持久化** | JSONL + 文件锁 | SQLite | 多后端 |
| **错误处理** | 完善 (5 种分类) | 基础 | 完善 |
| **Key 轮换** | ✅ 持久化冷却 | ❌ | ✅ |
| **指令系统** | ✅ 丰富 | ❌ | ✅ |
| **多 Agent** | ✅ 会话键路由 | ✅ 容器隔离 | ✅ 更复杂 |

---

## 总结

TinyClaw 的 LLM 交互设计特点：

### 优点

1. **完善的错误处理**: 5 种错误分类 + 针对性重试策略
2. **认证弹性**: 多 Key 轮换 + 持久化冷却状态
3. **会话可靠性**: 文件锁 + 崩溃修复
4. **丰富的指令系统**: `++think`, `++model`, `/new`, `/compact` 等
5. **流式响应**: 完整的事件订阅机制

### 不足

1. **思维链外包**: 依赖外部 SDK，无自定义逻辑
2. **缺乏验证**: 没有 Hook 验证或结果验证机制
3. **硬编码限制**: 去重 TTL 等参数无法配置
4. **无事务性**: 状态更新可能不完整
