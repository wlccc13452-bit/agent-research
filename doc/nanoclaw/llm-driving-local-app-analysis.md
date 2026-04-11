# NanoClaw LLM 驱动本地 APP 分析

## 一、核心机制概述

NanoClaw 通过**容器隔离**实现 LLM 驱动本地应用，而非直接在宿主机执行。这是与 OpenClaw/Kilocode 的关键区别。

```
传统模式:
  LLM → 直接执行命令 → 宿主机

NanoClaw 模式:
  LLM → 容器内执行 → 挂载目录 → 宿主机文件
```

---

## 二、驱动架构

### 2.1 三层架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Layer 1: Host Process                            │
│  (Node.js 主进程 - 消息路由、容器管理、IPC 监控)                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │
│  │ WhatsApp       │  │ Scheduler      │  │ IPC Watcher    │         │
│  │ Connection     │  │ Loop           │  │                │         │
│  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘         │
│          │                   │                   │                  │
│          └───────────────────┼───────────────────┘                  │
│                              │                                      │
│                              ▼                                      │
│                    ┌─────────────────┐                              │
│                    │ Container       │                              │
│                    │ Runner          │                              │
│                    └────────┬────────┘                              │
│                             │                                       │
├─────────────────────────────┼───────────────────────────────────────┤
│                             ▼                                       │
│                    Layer 2: Container Runtime                       │
│  (Apple Container / Docker - Linux VM 隔离环境)                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    Layer 3: Agent                              │ │
│  │  (Claude Agent SDK - LLM 执行环境)                             │ │
│  │                                                                │ │
│  │  Tools:                                                        │ │
│  │  • Bash (沙箱内执行)                                           │ │
│  │  • Read/Write/Edit (挂载目录)                                  │ │
│  │  • WebSearch/WebFetch (网络访问)                               │ │
│  │  • mcp__nanoclaw__* (IPC 通信)                                 │ │
│  │                                                                │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 2.2 挂载策略

**Main Group 挂载**：
```typescript
mounts = [
  // 完整项目访问 - 可管理所有群组
  { hostPath: projectRoot, containerPath: '/workspace/project', readonly: false },
  
  // 群组工作目录
  { hostPath: groups/main, containerPath: '/workspace/group', readonly: false },
  
  // 会话持久化
  { hostPath: data/sessions/main/.claude, containerPath: '/home/node/.claude', readonly: false },
  
  // IPC 通信
  { hostPath: data/ipc/main, containerPath: '/workspace/ipc', readonly: false }
]
```

**普通 Group 挂载**：
```typescript
mounts = [
  // 只能访问自己的群组目录
  { hostPath: groups/{name}, containerPath: '/workspace/group', readonly: false },
  
  // 全局内存只读
  { hostPath: groups/global, containerPath: '/workspace/global', readonly: true },
  
  // 会话持久化
  { hostPath: data/sessions/{name}/.claude, containerPath: '/home/node/.claude', readonly: false },
  
  // IPC 通信
  { hostPath: data/ipc/{name}, containerPath: '/workspace/ipc', readonly: false }
]
```

**额外挂载（安全验证）**：
```typescript
// 外部白名单配置
// ~/.config/nanoclaw/mount-allowlist.json
{
  "allowedRoots": [
    { "path": "~/projects", "allowReadWrite": true },
    { "path": "~/Documents/work", "allowReadWrite": false }
  ],
  "blockedPatterns": [".ssh", ".aws", ".gnupg", "id_rsa"],
  "nonMainReadOnly": true
}

// 验证流程
function validateMount(mount: AdditionalMount, isMain: boolean) {
  // 1. 检查容器路径有效性
  if (!isValidContainerPath(mount.containerPath)) return REJECTED;
  
  // 2. 解析并验证宿主路径
  const realPath = getRealPath(expandPath(mount.hostPath));
  
  // 3. 检查阻止模式
  if (matchesBlockedPattern(realPath, blockedPatterns)) return REJECTED;
  
  // 4. 检查允许根目录
  const allowedRoot = findAllowedRoot(realPath, allowedRoots);
  if (!allowedRoot) return REJECTED;
  
  // 5. 确定只读状态
  const effectiveReadonly = 
    (!isMain && allowlist.nonMainReadOnly) ||
    !allowedRoot.allowReadWrite;
  
  return { allowed: true, effectiveReadonly };
}
```

---

## 三、执行流程

### 3.1 容器执行流程

```
1. 消息到达 → processMessage()
   │
   ▼
2. 构建挂载配置
   │  buildVolumeMounts(group, isMain)
   │  - 项目目录 (Main only)
   │  - 群组目录
   │  - 会话目录
   │  - IPC 目录
   │  - 额外挂载 (验证后)
   │
   ▼
3. 启动容器
   │  spawn('container', ['run', '-i', '--rm', ...])
   │
   ▼
4. 写入输入 JSON
   │  container.stdin.write(JSON.stringify(input))
   │  - prompt: 消息内容
   │  - sessionId: 会话 ID
   │  - groupFolder: 群组标识
   │  - chatJid: WhatsApp JID
   │  - isMain: 权限标识
   │
   ▼
5. 容器内执行 (agent-runner)
   │  a. 读取 stdin JSON
   │  b. 创建 IPC MCP Server
   │  c. 调用 Claude Agent SDK
   │  d. Agent 使用工具执行任务
   │  e. 输出结果到 stdout
   │
   ▼
6. 解析容器输出
   │  - 提取 JSON (使用 Sentinel 标记)
   │  - 解析结果和新的 sessionId
   │
   ▼
7. 发送响应
   │  sock.sendMessage(jid, `${ASSISTANT_NAME}: ${response}`)
```

### 3.2 容器内 Agent 执行

```typescript
// agent-runner/src/index.ts
async function main() {
  // 1. 读取输入
  const stdinData = await readStdin();
  const input = JSON.parse(stdinData);
  
  // 2. 创建 IPC MCP Server
  const ipcMcp = createIpcMcp({
    chatJid: input.chatJid,
    groupFolder: input.groupFolder,
    isMain: input.isMain
  });
  
  // 3. 调用 Claude Agent SDK
  for await (const message of query({
    prompt: input.prompt,
    options: {
      cwd: '/workspace/group',           // 工作目录
      resume: input.sessionId,           // 恢复会话
      allowedTools: [                    // 允许的工具
        'Bash', 'Read', 'Write', 'Edit', 'Glob', 'Grep',
        'WebSearch', 'WebFetch',
        'mcp__nanoclaw__*'               // IPC 工具
      ],
      permissionMode: 'bypassPermissions',
      settingSources: ['project'],       // 加载 CLAUDE.md
      mcpServers: { nanoclaw: ipcMcp }
    }
  })) {
    if (message.type === 'system' && message.subtype === 'init') {
      newSessionId = message.session_id;
    }
    if ('result' in message) {
      result = message.result;
    }
  }
  
  // 4. 输出结果
  console.log(OUTPUT_START_MARKER);
  console.log(JSON.stringify({ status: 'success', result, newSessionId }));
  console.log(OUTPUT_END_MARKER);
}
```

---

## 四、工具能力

### 4.1 Bash 命令执行

**安全特性**：
- 命令在容器内执行，不影响宿主机
- 以非 root 用户 (node:1000) 运行
- 只能访问挂载的目录

**示例用法**：
```bash
# Agent 在容器内执行
# 查看文件
ls -la /workspace/group/

# 搜索内容
grep -r "important" /workspace/group/

# 执行脚本
node /workspace/group/scripts/process.js

# 安装依赖 (临时，容器销毁后消失)
npm install some-package
```

### 4.2 文件操作

**Read/Write/Edit**：
- 读写挂载目录中的文件
- Main Group 可以管理所有群组配置
- 普通 Group 只能操作自己的目录

**示例**：
```typescript
// 读取群组配置 (Main only)
const config = await Read('/workspace/project/data/registered_groups.json');

// 写入群组内存
await Write('/workspace/group/CLAUDE.md', memoryContent);

// 编辑会话记录
await Edit('/workspace/group/conversations/history.md', oldText, newText);
```

### 4.3 IPC 通信工具

**send_message**：
```typescript
// Agent 发送消息到 WhatsApp
await mcp__nanoclaw__send_message({ 
  text: "Task completed successfully!" 
});
```

**schedule_task**：
```typescript
// 创建定时任务
await mcp__nanoclaw__schedule_task({
  prompt: "Send daily summary",
  schedule_type: "cron",
  schedule_value: "0 9 * * *",
  context_mode: "group"
});
```

**register_group** (Main only)：
```typescript
// 注册新群组
await mcp__nanoclaw__register_group({
  jid: "120363336345536173@g.us",
  name: "Family Chat",
  folder: "family-chat",
  trigger: "@Andy"
});
```

---

## 五、安全机制

### 5.1 多层防护

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Security Layers                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Layer 1: 外部白名单                                                 │
│  ~/.config/nanoclaw/mount-allowlist.json                            │
│  - 不挂载到容器，无法被 Agent 修改                                    │
│  - 定义允许的挂载根目录                                               │
│  - 定义阻止的路径模式                                                 │
│                                                                      │
│  Layer 2: 容器隔离                                                   │
│  - 进程隔离 (容器进程无法影响宿主)                                     │
│  - 文件系统隔离 (只有挂载目录可见)                                     │
│  - 非 root 用户 (uid 1000)                                          │
│  - 临时容器 (--rm 自动清理)                                          │
│                                                                      │
│  Layer 3: 权限分层                                                   │
│  - Main Group: 完整项目访问                                          │
│  - 普通 Group: 只能访问自己目录                                       │
│  - IPC 授权验证                                                      │
│                                                                      │
│  Layer 4: IPC 验证                                                   │
│  - 验证来源群组身份                                                   │
│  - 阻止跨群组操作                                                    │
│  - 记录审计日志                                                      │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 5.2 挂载安全验证流程

```typescript
// 1. 加载外部白名单
const allowlist = loadMountAllowlist();  // 从 ~/.config/nanoclaw/

// 2. 验证每个挂载请求
for (const mount of requestedMounts) {
  // 2.1 验证容器路径
  if (!isValidContainerPath(mount.containerPath)) {
    reject("Invalid container path");
  }
  
  // 2.2 解析真实路径
  const realPath = fs.realpathSync(expandPath(mount.hostPath));
  
  // 2.3 检查阻止模式
  if (matchesBlockedPattern(realPath, ['.ssh', '.aws', '.gnupg'])) {
    reject("Path matches blocked pattern");
  }
  
  // 2.4 检查允许根目录
  const allowedRoot = findAllowedRoot(realPath, allowlist.allowedRoots);
  if (!allowedRoot) {
    reject("Path not under allowed root");
  }
  
  // 2.5 确定只读状态
  const effectiveReadonly = 
    (!isMain && allowlist.nonMainReadOnly) ||
    !allowedRoot.allowReadWrite;
  
  // 3. 添加到挂载列表
  validatedMounts.push({
    hostPath: realPath,
    containerPath: `/workspace/extra/${mount.containerPath}`,
    readonly: effectiveReadonly
  });
}
```

### 5.3 IPC 授权验证

```typescript
// 处理 IPC 消息时验证权限
async function processIpcFile(data, sourceGroup, isMain) {
  // 消息发送验证
  if (data.type === 'message') {
    const targetGroup = registeredGroups[data.chatJid];
    if (!isMain && targetGroup.folder !== sourceGroup) {
      logger.warn('Unauthorized IPC message attempt blocked');
      return;
    }
    await sendMessage(data.chatJid, data.text);
  }
  
  // 任务调度验证
  if (data.type === 'schedule_task') {
    if (!isMain && data.groupFolder !== sourceGroup) {
      logger.warn('Unauthorized schedule_task attempt blocked');
      return;
    }
    createTask(data);
  }
  
  // 群组管理验证 (仅 Main)
  if (data.type === 'register_group') {
    if (!isMain) {
      logger.warn('Unauthorized register_group attempt blocked');
      return;
    }
    registerGroup(data);
  }
}
```

---

## 六、与其他系统对比

### 6.1 驱动模式对比

| 维度 | NanoClaw | OpenClaw | Kilocode |
|------|----------|----------|----------|
| **隔离级别** | 容器 (OS级) | 应用级权限 | VS Code 沙箱 |
| **执行位置** | Linux VM | 宿主机进程 | VS Code 扩展进程 |
| **安全模型** | 物理隔离 | 白名单检查 | VS Code 权限 |
| **命令执行** | 容器内 Bash | 宿主机命令 | 宿主机命令 |
| **文件访问** | 挂载目录 | 白名单路径 | 工作区文件 |

### 6.2 安全性对比

| 风险 | NanoClaw | OpenClaw | Kilocode |
|------|----------|----------|----------|
| 恶意命令 | ✅ 隔离在容器 | ⚠️ 需要白名单 | ⚠️ 需要确认 |
| 文件泄露 | ✅ 只有挂载可见 | ⚠️ 白名单可控 | ⚠️ 工作区限制 |
| 凭证暴露 | ⚠️ 挂载到容器 | ⚠️ 环境变量 | ⚠️ 配置文件 |
| Prompt 注入 | ✅ 容器隔离 | ⚠️ 应用层防护 | ⚠️ 应用层防护 |

---

## 七、实际应用示例

### 7.1 文件操作示例

```typescript
// 用户: "@Andy 查看今天的日志并总结"

// Agent 在容器内执行:
const logFiles = await Glob('/workspace/group/logs/*.log');
const todayLogs = logFiles.filter(f => f.includes(today));
const content = await Read(todayLogs[0]);

// 总结后发送
await mcp__nanoclaw__send_message({ 
  text: `今日日志摘要:\n• 处理了 15 条消息\n• 完成了 3 个定时任务` 
});
```

### 7.2 定时任务示例

```typescript
// 用户: "@Andy 每天早上9点发送天气预报"

// Agent 创建任务:
await mcp__nanoclaw__schedule_task({
  prompt: "获取天气预报并通过 send_message 发送给用户",
  schedule_type: "cron",
  schedule_value: "0 9 * * *",
  context_mode: "isolated"
});
```

### 7.3 群组管理示例 (Main only)

```typescript
// 用户: "@Andy 把 Family Chat 加进来"

// Agent 执行:
// 1. 查询数据库找到群组 JID
const groups = JSON.parse(await Read('/workspace/ipc/available_groups.json'));
const familyChat = groups.groups.find(g => g.name === "Family Chat");

// 2. 注册群组
await mcp__nanoclaw__register_group({
  jid: familyChat.jid,
  name: "Family Chat",
  folder: "family-chat",
  trigger: "@Andy"
});

// 3. 创建群组文件夹
await Bash('mkdir -p /workspace/project/groups/family-chat');
await Write('/workspace/project/groups/family-chat/CLAUDE.md', 
  '# Family Chat\n\nFamily conversation assistant.');
```

---

## 八、改进建议

### 8.1 安全改进

1. **凭证隔离**：
   - 使用 Vault 或 Secrets Manager
   - 不将凭证挂载到容器

2. **网络隔离**：
   - 配置容器网络策略
   - 限制出站连接

3. **审计增强**：
   - 记录所有容器执行日志
   - 实现操作追踪

### 8.2 功能改进

1. **容器复用**：
   - 复用容器减少启动延迟
   - 实现容器池

2. **并行执行**：
   - 支持同时运行多个容器
   - 实现任务队列

3. **资源限制**：
   - 配置 CPU/内存限制
   - 实现超时强制终止

### 8.3 开发体验改进

1. **调试工具**：
   - 容器内调试支持
   - 日志实时查看

2. **开发模式**：
   - 本地开发跳过容器
   - 热重载支持

3. **测试框架**：
   - 容器环境测试
   - 模拟 WhatsApp 消息
