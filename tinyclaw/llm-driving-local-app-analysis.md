# TinyClaw LLM 驱动本地 APP 分析

## 概述

TinyClaw 通过多种方式驱动本地应用：Shell 执行、浏览器自动化、文件操作、Docker 沙箱等。本文详细分析其实现机制。

---

## 核心驱动方式

### 1. Shell 执行 (Bash Tool)

**文件**: `src/exec/exec-tool.ts`

```typescript
// 自定义 Bash 工具替代默认工具
export function createExecTool(options: {
  cwd: string;
  timeoutSec?: number;
  backgroundMs?: number;
  maxOutput?: number;
}): AgentTool {
  return {
    name: "bash",
    description: "Execute shell commands...",
    parameters: z.object({
      command: z.string().describe("The command to execute"),
      timeout: z.number().optional(),
      background: z.boolean().optional(),
    }),
    execute: async (params) => {
      // 检查沙箱配置
      if (sandboxConfig?.enabled) {
        return execInSandbox(container, params.command, { timeoutSec });
      }
      
      // 本地执行
      return execLocal(params.command, { cwd, timeout, maxOutput });
    },
  };
}
```

### 执行流程

```
LLM Tool Call (bash)
    │
    ▼
┌─────────────────────────┐
│   Security Policy       │
│   (10 层检查)           │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│   Exec Approval?        │
│   (interactive mode)    │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│   Sandbox Enabled?      │
├────────────┬────────────┤
│     Yes    │     No     │
│      ▼     │      ▼     │
│  Docker    │   Local    │
│  Sandbox   │   Exec     │
└────────────┴────────────┘
             │
             ▼
        返回结果
```

---

## Docker 沙箱隔离

### 沙箱配置

```typescript
// src/sandbox/sandbox.ts
export interface SandboxConfig {
  enabled: boolean;
  image: string;           // "tinyclaw-sandbox"
  scope: "session" | "shared";
  memoryLimit: string;     // "512m"
  cpuLimit: string;        // "1"
  networkMode: "none" | "bridge";
  mountWorkspace: boolean;
  timeoutSec: number;      // 300
}
```

### 容器生命周期

```typescript
// 创建容器
export async function ensureSandboxContainer(
  sessionKey: string,
  config: Partial<SandboxConfig>,
): Promise<string | null> {
  const name = containerName(sessionKey);
  
  // 检查是否已运行
  const inspect = await runDocker(["inspect", "-f", "{{.State.Running}}", name]);
  if (inspect.stdout.trim() === "true") return name;
  
  // 确保镜像存在
  await ensureSandboxImage(config.image);
  
  // 创建新容器
  const createArgs = [
    "run", "-d",
    "--name", name,
    "--memory", config.memoryLimit,
    "--cpus", config.cpuLimit,
    "--network", config.networkMode,
    "--restart", "no",
    "--label", "tinyclaw=sandbox",
  ];
  
  if (config.mountWorkspace) {
    createArgs.push("-v", `${process.cwd()}:/workspace:rw`);
  }
  
  createArgs.push(config.image);
  await runDocker(createArgs);
  
  return name;
}

// 在容器内执行
export async function execInSandbox(
  containerName: string,
  command: string,
  opts: { timeoutSec?: number; workdir?: string; env?: Record<string, string> },
): Promise<SandboxExecResult> {
  const execArgs = ["exec"];
  if (opts.workdir) execArgs.push("-w", opts.workdir);
  if (opts.env) {
    for (const [k, v] of Object.entries(opts.env)) {
      execArgs.push("-e", `${k}=${v}`);
    }
  }
  execArgs.push(containerName, "bash", "-c", command);
  
  return runDocker(execArgs, opts.timeoutSec * 1000);
}
```

### Dockerfile.sandbox

```dockerfile
FROM ubuntu:22.04

# 基础工具
RUN apt-get update && apt-get install -y \
    curl wget git \
    python3 python3-pip \
    nodejs npm \
    && rm -rf /var/lib/apt/lists/*

# 工作目录
WORKDIR /workspace

# 非特权用户
RUN useradd -m -s /bin/bash tinyclaw
USER tinyclaw

CMD ["sleep", "infinity"]
```

---

## 浏览器自动化

**文件**: `src/browser/browser.ts`

### Playwright 集成

```typescript
import { chromium, type Browser, type Page } from "playwright-core";

export interface BrowserInstance {
  browser: Browser;
  page: Page;
  close: () => Promise<void>;
}

export async function launchBrowser(options: {
  headless?: boolean;
  proxy?: string;
}): Promise<BrowserInstance> {
  const browser = await chromium.launch({
    headless: options.headless ?? true,
    proxy: options.proxy ? { server: options.proxy } : undefined,
  });
  
  const page = await browser.newPage();
  
  return {
    browser,
    page,
    close: async () => {
      await page.close();
      await browser.close();
    },
  };
}
```

### 浏览器工具

```typescript
// 5 个浏览器相关工具
const BROWSER_TOOLS = [
  {
    name: "browser_navigate",
    description: "Navigate to a URL",
    parameters: z.object({ url: z.string() }),
    execute: async (params, ctx) => {
      await ctx.page.goto(params.url);
      return { content: [{ type: "text", text: `Navigated to ${params.url}` }] };
    },
  },
  {
    name: "browser_click",
    description: "Click an element",
    parameters: z.object({ selector: z.string() }),
    execute: async (params, ctx) => {
      await ctx.page.click(params.selector);
      return { content: [{ type: "text", text: "Clicked" }] };
    },
  },
  {
    name: "browser_type",
    description: "Type text into an element",
    parameters: z.object({ selector: z.string(), text: z.string() }),
    execute: async (params, ctx) => {
      await ctx.page.type(params.selector, params.text);
      return { content: [{ type: "text", text: "Typed" }] };
    },
  },
  {
    name: "browser_screenshot",
    description: "Take a screenshot",
    parameters: z.object({ fullPage: z.boolean().optional() }),
    execute: async (params, ctx) => {
      const screenshot = await ctx.page.screenshot({ fullPage: params.fullPage });
      return {
        content: [
          { type: "text", text: "Screenshot taken" },
          { type: "image", data: screenshot.toString("base64"), mimeType: "image/png" },
        ],
      };
    },
  },
  {
    name: "browser_snapshot",
    description: "Get accessibility snapshot",
    parameters: z.object({}),
    execute: async (params, ctx) => {
      const snapshot = await ctx.page.accessibility.snapshot();
      return { content: [{ type: "text", text: JSON.stringify(snapshot, null, 2) }] };
    },
  },
];
```

---

## 文件操作

### 内置工具

```typescript
// 来自 @mariozechner/pi-coding-agent
import { createCodingTools } from "@mariozechner/pi-coding-agent";

const builtinTools = createCodingTools(workspaceDir);
// 返回: [read, write, edit, glob, grep, ls, ...]
```

### 参数规范化

```typescript
// 兼容不同模型的参数命名
const PARAM_ALIASES = {
  read:  { file_path: "path", filePath: "path" },
  write: { file_path: "path", filePath: "path" },
  edit:  { file_path: "path", old_string: "oldText", new_string: "newText" },
  glob:  { file_path: "path", filePath: "path" },
  grep:  { file_path: "path", filePath: "path" },
};

export function normalizeToolParams(toolName: string, params: Record<string, unknown>) {
  const aliases = PARAM_ALIASES[toolName];
  if (!aliases) return params;
  
  const normalized = { ...params };
  for (const [alias, canonical] of Object.entries(aliases)) {
    if (alias in normalized && !(canonical in normalized)) {
      normalized[canonical] = normalized[alias];
      delete normalized[alias];
    }
  }
  return normalized;
}
```

---

## 消息渠道集成

### Channel Adapter 接口

```typescript
// src/channel/channel.ts
export interface ChannelAdapter {
  // 发送文本
  sendText(peerId: string, text: string, accountId?: string): Promise<void>;
  
  // 发送媒体
  sendImage?(peerId: string, url: string, caption?: string): Promise<void>;
  sendDocument?(peerId: string, url: string, filename?: string): Promise<void>;
  sendAudio?(peerId: string, url: string): Promise<void>;
  
  // 交互
  sendTyping?(peerId: string): Promise<void>;
  sendReadReceipt?(messageId: string): Promise<void>;
  react?(messageId: string, emoji: string): Promise<void>;
  
  // 线程支持
  replyInThread?(messageId: string, text: string): Promise<void>;
}

export interface ChannelCapabilities {
  text: boolean;
  image: boolean;
  audio: boolean;
  video: boolean;
  document: boolean;
  reaction: boolean;
  thread: boolean;
  typing: boolean;
  readReceipt: boolean;
}
```

### WhatsApp 适配器

```typescript
// src/channel/whatsapp.ts
export function createWhatsAppChannel(config: WhatsAppConfig): ChannelInstance {
  const client = new WhatsAppClient(config);
  
  return {
    adapter: {
      sendText: async (peerId, text) => {
        await client.messages.create({
          to: peerId,
          type: "text",
          text: { body: text },
        });
      },
      
      sendImage: async (peerId, url, caption) => {
        await client.messages.create({
          to: peerId,
          type: "image",
          image: { link: url },
          text: caption ? { body: caption } : undefined,
        });
      },
      
      sendTyping: async (peerId) => {
        // WhatsApp 不支持原生 typing indicator
        // 使用消息状态模拟
      },
    },
    capabilities: {
      text: true,
      image: true,
      audio: true,
      video: true,
      document: true,
      reaction: true,
      thread: false,
      typing: false,
      readReceipt: true,
    },
  };
}
```

### Telegram 适配器 (grammY)

```typescript
// src/channel/telegram.ts
import { Bot } from "grammy";

export function createTelegramChannel(config: TelegramConfig): ChannelInstance {
  const bot = new Bot(config.botToken);
  
  bot.on("message:text", async (ctx) => {
    const msg: InboundMessage = {
      channelId: "telegram:default",
      peerId: ctx.chat.id.toString(),
      peerName: ctx.from?.first_name,
      body: ctx.message.text,
      messageId: ctx.message.message_id.toString(),
      isGroup: ctx.chat.type === "group" || ctx.chat.type === "supergroup",
    };
    await onMessage(msg);
  });
  
  return {
    adapter: {
      sendText: async (peerId, text) => {
        await bot.api.sendMessage(peerId, text, { parse_mode: "Markdown" });
      },
      
      sendTyping: async (peerId) => {
        await bot.api.sendChatAction(peerId, "typing");
      },
      
      replyInThread: async (messageId, text) => {
        await bot.api.sendMessage(peerId, text, {
          reply_to_message_id: messageId,
        });
      },
    },
    capabilities: {
      text: true,
      image: true,
      audio: true,
      video: true,
      document: true,
      reaction: true,
      thread: true, // Telegram 支持 topics
      typing: true,
      readReceipt: false,
    },
    start: async () => {
      if (config.mode === "polling") {
        bot.start();
      } // webhook mode 在 gateway 中处理
    },
  };
}
```

---

## 安全机制

### 1. SSRF 防护

```typescript
// src/security/security.ts
const PRIVATE_IP_RANGES = [
  /^127\./, /^10\./, /^172\.(1[6-9]|2\d|3[01])\./, /^192\.168\./,
  /^169\.254\./, /^0\./, /^::1$/, /^fc/i, /^fd/i, /^fe80:/i, /^localhost$/i,
];

const CLOUD_METADATA_ENDPOINTS = [
  "metadata.google",
  "169.254.169.254", // AWS/GCP metadata
  "metadata.aws",
];

export function ssrfCheck(url: string, config: TinyClawConfig): { allowed: boolean; reason?: string } {
  if (config.security?.ssrfProtection === false) return { allowed: true };
  
  try {
    const parsed = new URL(url);
    
    // 阻止私有 IP
    if (isPrivateIP(parsed.hostname)) {
      return { allowed: false, reason: `Blocked: private IP (${parsed.hostname})` };
    }
    
    // 阻止非 HTTP(S)
    if (!["http:", "https:"].includes(parsed.protocol)) {
      return { allowed: false, reason: `Blocked: protocol ${parsed.protocol}` };
    }
    
    // 阻止云元数据端点
    if (CLOUD_METADATA_ENDPOINTS.some(p => parsed.hostname.includes(p))) {
      return { allowed: false, reason: "Blocked: cloud metadata endpoint" };
    }
    
    return { allowed: true };
  } catch {
    return { allowed: false, reason: "Invalid URL" };
  }
}
```

### 2. 执行审批

```typescript
// src/security/security.ts
interface PendingApproval {
  id: string;
  command: string;
  timestamp: number;
  resolve: (approved: boolean) => void;
}

const pendingApprovals = new Map<string, PendingApproval>();

export function requestApproval(command: string): { id: string; promise: Promise<boolean> } {
  const id = `approval_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
  
  const promise = new Promise<boolean>((resolve) => {
    pendingApprovals.set(id, { id, command, timestamp: Date.now(), resolve });
    
    // 60 秒超时自动拒绝
    setTimeout(() => {
      const pending = pendingApprovals.get(id);
      if (pending) {
        pending.resolve(false);
        pendingApprovals.delete(id);
      }
    }, 60000);
  });
  
  return { id, promise };
}

// WebSocket 接口
// ws.send(JSON.stringify({ method: "exec.pending" }));
// ws.send(JSON.stringify({ method: "exec.approve", params: { id: "approval_..." } }));
```

### 3. 自动允许列表

```typescript
// 3 次批准后自动允许相同命令模式
const AUTO_ALLOW_THRESHOLD = 3;

export function trackApproval(command: string): void {
  const prefix = command.split(/\s+/).slice(0, 2).join(" ");
  const list = loadAllowlist();
  
  let entry = list.find(e => e.pattern === prefix);
  if (!entry) {
    entry = { pattern: prefix, approvalCount: 0, autoAllowed: false };
    list.push(entry);
  }
  
  entry.approvalCount++;
  if (entry.approvalCount >= AUTO_ALLOW_THRESHOLD) {
    entry.autoAllowed = true;
    log.info(`Auto-allowed exec pattern: "${prefix}"`);
  }
  
  saveAllowlist(list);
}
```

---

## 完整驱动流程示例

### 场景: 用户通过 WhatsApp 请求分析代码

```
1. 用户消息 (WhatsApp)
   "@bot 分析 main.py 的代码质量"
   
2. Webhook 接收 (Gateway)
   POST /webhook/whatsapp
   { "entry": [{ "changes": [{ "value": { "messages": [...] } }] }] }
   
3. 解析消息 (WhatsApp Adapter)
   { channelId: "whatsapp:main", peerId: "1234567890", body: "@bot 分析 main.py 的代码质量" }
   
4. Pipeline 处理
   - 去重检查
   - 移除 @bot 前缀
   - 注入检测 (安全)
   - 构建会话键: "default:whatsapp:main:1234567890"
   
5. Agent 执行
   LLM 决定调用工具:
   - read({ path: "main.py" })
   - bash({ command: "pylint main.py" })
   
6. 安全检查
   - read: allow (默认允许)
   - bash: 进入审批流程 (如果 execApproval: "interactive")
   
7. 工具执行
   - read: 读取文件内容
   - bash: 等待审批 → 执行 → 返回结果
   
8. 响应分块
   - 1200 字符一块
   - 段落/句子边界优先
   
9. 发送到 WhatsApp
   - 分块发送 (800-2500ms 延迟)
   - 带响应前缀 (如果配置)
```

---

## 与其他项目对比

| 维度 | TinyClaw | NanoClaw | OpenClaw |
|------|----------|----------|----------|
| **Shell 执行** | ✅ 本地 + Docker | ✅ 仅容器 | ✅ 多种后端 |
| **浏览器自动化** | ✅ Playwright | ❌ | ✅ |
| **消息渠道** | 4 种完整实现 | WhatsApp | 4+ 种 |
| **沙箱隔离** | Docker | 容器级 | Docker |
| **执行审批** | ✅ 自动白名单 | ❌ | ✅ |
| **SSRF 防护** | ✅ 完整 | ❌ | ✅ |
| **注入检测** | ✅ 模式匹配 | ❌ | ✅ |

---

## 总结

### TinyClaw 驱动本地 APP 的特点

1. **多种执行环境**: 本地 Shell + Docker 沙箱
2. **丰富的工具集**: 19 种内置工具 + 插件扩展
3. **完善的安全机制**: 10 层策略 + 执行审批 + SSRF 防护
4. **多渠道集成**: 4 种主流消息平台完整实现
5. **浏览器自动化**: Playwright 支持完整 CDP 操作

### 关键实现亮点

- **自动允许列表**: 3 次审批后自动信任相同命令模式
- **分块发送**: 智能段落/句子边界分割，模拟人工输入节奏
- **会话隔离**: 每个用户/群组/线程独立会话
- **配对机制**: DM 安全验证，防止未授权访问
