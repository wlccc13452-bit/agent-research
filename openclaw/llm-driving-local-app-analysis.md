# OpenClaw LLM 驱动本地 APP 分析

## 一、核心机制

### 1.1 驱动模式概览

OpenClaw 通过**三种模式**驱动本地应用：

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LLM 驱动本地应用模式                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  模式 A: CLI 工具桥接                                                │
│  ┌─────────┐     ┌─────────────┐     ┌─────────────┐              │
│  │   LLM   │────▶│  CLI 工具   │────▶│  本地应用    │              │
│  └─────────┘     └─────────────┘     └─────────────┘              │
│  示例: obsidian-cli → Obsidian, things → Things 3                  │
│                                                                     │
│  模式 B: URL Scheme 调用                                            │
│  ┌─────────┐     ┌─────────────┐     ┌─────────────┐              │
│  │   LLM   │────▶│ URL Scheme  │────▶│  本地应用    │              │
│  └─────────┘     └─────────────┘     └─────────────┘              │
│  示例: things://add?title=... → Things 3                           │
│                                                                     │
│  模式 C: API/SDK 集成                                               │
│  ┌─────────┐     ┌─────────────┐     ┌─────────────┐              │
│  │   LLM   │────▶│  SDK/API    │────▶│  本地应用    │              │
│  └─────────┘     └─────────────┘     └─────────────┘              │
│  示例: AppleScript → Notes.app, JXA → Reminders.app               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 工作原理

```
用户请求: "把明天的会议添加到 Things"
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. Skill 匹配                                                    │
│    扫描 <available_skills> 找到 things-mac                       │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. 读取 SKILL.md                                                 │
│    获取 things add 命令格式                                       │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. LLM 生成工具调用                                               │
│    bash: things add "明天的会议" --when tomorrow                  │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Bash 工具执行                                                 │
│    things CLI → URL Scheme → Things.app 创建任务                 │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
用户收到确认: "已添加任务到 Things"
```

---

## 二、Skill 驱动机制

### 2.1 Skill 定义结构

```yaml
# skills/things-mac/SKILL.md
---
name: things-mac
description: Manage Things 3 via the `things` CLI on macOS.
metadata:
  openclaw:
    os: ["darwin"]
    requires:
      bins: ["things"]    # 需要的 CLI 工具
    install:
      - kind: go
        module: "github.com/ossianhempel/things3-cli/cmd/things@latest"
---

# Things 3 CLI

Control Things 3 from the terminal.

## Commands

### Add Task
```bash
things add "Task title" --notes "..." --when today
```

### List Tasks
```bash
things inbox --limit 50
things today
```
```

### 2.2 Skill 加载流程

```typescript
// 1. 扫描 Skill 目录
const skills = loadSkillsFromDir(dir)

// 2. 过滤符合条件的 Skill
const eligible = skills.filter(skill => {
  // OS 检查
  if (skill.os && !skill.os.includes(currentOS)) return false
  
  // CLI 工具检查
  if (skill.requires?.bins) {
    for (const bin of skill.requires.bins) {
      if (!hasBinary(bin)) return false
    }
  }
  
  return true
})

// 3. 构建系统提示
const skillsSection = formatSkillsForPrompt(eligible)
```

### 2.3 Skill 触发机制

```
用户消息 → System Prompt 中的 Skills Section → LLM 选择匹配的 Skill
                                              ↓
                                    读取 SKILL.md 获取详细指令
                                              ↓
                                    执行相应的 CLI 命令
```

---

## 三、具体实现案例

### 3.1 Obsidian - 文件系统型

**Skill 配置：**
```yaml
---
name: obsidian
description: Work with Obsidian vaults via obsidian-cli.
metadata:
  openclaw:
    requires: { bins: ["obsidian-cli"] }
    install:
      - kind: brew
        formula: "yakitrak/yakitrak/obsidian-cli"
---
```

**工作原理：**

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Obsidian 控制流程                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  LLM 生成命令                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ obsidian-cli search "meeting notes"                         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ obsidian-cli 执行                                           │   │
│  │ 1. 读取 ~/Library/Application Support/obsidian/obsidian.json│   │
│  │ 2. 找到活跃 vault 路径                                       │   │
│  │ 3. 在 .md 文件中搜索关键词                                   │   │
│  │ 4. 返回匹配的笔记列表                                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 创建笔记                                                     │   │
│  │ obsidian-cli create "New Note" --content "..." --open       │   │
│  │                                                              │   │
│  │ → 使用 obsidian:// URL scheme 唤起 Obsidian.app             │   │
│  │ → 自动打开新创建的笔记                                       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Things 3 - URL Scheme 型

**Skill 配置：**
```yaml
---
name: things-mac
description: Manage Things 3 via the `things` CLI on macOS.
metadata:
  openclaw:
    os: ["darwin"]
    requires: { bins: ["things"] }
---
```

**工作原理：**

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Things 3 控制流程                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  读取操作（直接读取数据库）                                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ things inbox --limit 50                                     │   │
│  │                                                              │   │
│  │ → 读取 SQLite 数据库                                         │   │
│  │ ~/Library/Containers/com.culturedcode.ThingsMac/            │   │
│  │    Data/Library/Application Support/Cultured Code/          │   │
│  │    Things/ThingsData-<UUID>                                 │   │
│  │                                                              │   │
│  │ ⚠️ 需要 Full Disk Access 权限                                │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  写入操作（URL Scheme）                                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ things add "Buy milk" --when today                          │   │
│  │                                                              │   │
│  │ → 构建 URL: things:///add?title=Buy%20milk&when=today       │   │
│  │ → macOS 打开 URL → Things.app 接收并创建任务                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.3 Spotify - API 桥接型

**Skill 配置：**
```yaml
---
name: spotify-player
description: Terminal Spotify playback via spogo.
metadata:
  openclaw:
    requires: { anyBins: ["spogo", "spotify_player"] }
---
```

**工作原理：**

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Spotify 控制流程                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  认证流程                                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ spogo auth import --browser chrome                          │   │
│  │                                                              │   │
│  │ → 从 Chrome 导入 Spotify cookies                            │   │
│  │ → 存储到 ~/.config/spogo/credentials.json                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  播放控制                                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ spogo play / spogo pause / spogo next                       │   │
│  │                                                              │   │
│  │ → 使用 Spotify Web API                                      │   │
│  │ → 通过 cookies 认证                                          │   │
│  │ → 控制指定设备的播放状态                                      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  设备管理                                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ spogo device list                                           │   │
│  │ spogo device set "Living Room Speaker"                      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.4 Sonos - 本地网络控制型

**Skill 配置：**
```yaml
---
name: sonoscli
description: Control Sonos speakers on the local network.
metadata:
  openclaw:
    requires: { bins: ["sonos"] }
---
```

**工作原理：**

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Sonos 控制流程                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  设备发现                                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ sonos discover                                              │   │
│  │                                                              │   │
│  │ → 使用 SSDP (Simple Service Discovery Protocol)             │   │
│  │ → 广播 discovery 消息到 239.255.255.250:1900                │   │
│  │ → 接收本地网络中 Sonos 设备的响应                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  播放控制                                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ sonos play --name "Kitchen"                                 │   │
│  │                                                              │   │
│  │ → 使用 UPnP/SOAP 协议                                        │   │
│  │ → 向设备发送 HTTP POST 请求                                  │   │
│  │ → 调用 Play() UPnP action                                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  音量控制                                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ sonos volume set 15 --name "Kitchen"                        │   │
│  │                                                              │   │
│  │ → UPnP RenderingControl service                             │   │
│  │ → SetVolume(InstanceID=0, Channel=Master, DesiredVolume=15) │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.5 Apple Notes - AppleScript 型

**Skill 配置：**
```yaml
---
name: apple-notes
description: Manage Apple Notes via the `memo` CLI on macOS.
metadata:
  openclaw:
    os: ["darwin"]
    requires: { bins: ["memo"] }
---
```

**工作原理：**

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Apple Notes 控制流程                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  LLM 生成命令                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ memo notes -s "meeting"                                     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ memo CLI 执行                                                │   │
│  │                                                              │   │
│  │ → 使用 PyObjC / ScriptingBridge                             │   │
│  │ → 调用 Apple Events                                          │   │
│  │ → 与 Notes.app 通信                                          │   │
│  │                                                              │   │
│  │ from ScriptingBridge import SBApplication                   │   │
│  │ notes = SBApplication.applicationWithBundleIdentifier_(     │   │
│  │     "com.apple.Notes"                                       │   │
│  │ )                                                           │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 权限要求                                                     │   │
│  │ System Settings > Privacy & Security > Automation           │   │
│  │ → 允许 Terminal/OpenClaw.app 控制 Notes.app                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.6 1Password - 安全敏感型

**Skill 配置：**
```yaml
---
name: 1password
description: Set up and use 1Password CLI (op).
metadata:
  openclaw:
    emoji: "🔐"
    requires: { bins: ["op"] }
---
```

**安全机制：**

```
┌─────────────────────────────────────────────────────────────────────┐
│                    1Password 安全机制                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ⚠️ 必须在 tmux 会话中运行                                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ # 创建专用 tmux 会话                                         │   │
│  │ SOCKET_DIR="${TMPDIR}/openclaw-tmux-sockets"                │   │
│  │ SOCKET="$SOCKET_DIR/openclaw-op.sock"                       │   │
│  │ SESSION="op-auth-$(date +%Y%m%d-%H%M%S)"                    │   │
│  │                                                              │   │
│  │ tmux -S "$SOCKET" new -d -s "$SESSION"                      │   │
│  │ tmux -S "$SOCKET" send-keys -t "$SESSION" -- "op signin"    │   │
│  │ tmux -S "$SOCKET" capture-pane -p -J -t "$SESSION"          │   │
│  │ tmux -S "$SOCKET" kill-session -t "$SESSION"                │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  安全原则                                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 1. 永不在日志中暴露密钥                                       │   │
│  │ 2. 使用 op run / op inject 而非写入文件                      │   │
│  │ 3. 不在 tmux 外运行 op                                       │   │
│  │ 4. 使用桌面应用集成认证                                       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  典型操作                                                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ # 读取密钥                                                   │   │
│  │ op item get "Database Password" --fields password           │   │
│  │                                                              │   │
│  │ # 注入环境变量运行脚本                                        │   │
│  │ op run -- python script.py                                  │   │
│  │                                                              │   │
│  │ # 获取 OTP                                                   │   │
│  │ op read "op://Private/Npmjs/one-time password?attribute=otp"│   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 四、权限与安全模型

### 4.1 macOS 权限层次

```
┌─────────────────────────────────────────────────────────────────────┐
│                    macOS 权限层次                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Level 1: 文件系统访问 (Full Disk Access)                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ • 读取 Things 数据库                                         │   │
│  │ • 访问任意用户文件                                           │   │
│  │ • 读取应用配置文件                                           │   │
│  │                                                              │   │
│  │ 授予方式: System Settings > Privacy > Full Disk Access      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  Level 2: 应用自动化 (Automation)                                   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ • AppleScript 控制 Notes.app                                 │   │
│  │ • UI scripting                                               │   │
│  │ • 发送 Apple Events                                          │   │
│  │                                                              │   │
│  │ 授予方式: System Settings > Privacy > Automation            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  Level 3: 沙盒内操作 (Sandbox)                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ • 普通文件读写                                               │   │
│  │ • 网络请求                                                   │   │
│  │ • URL Scheme 调用                                            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 权限检查流程

```typescript
async function checkPermissions(operation: Operation): Promise<boolean> {
  // 1. 检查文件访问权限
  if (operation.requiresFileAccess) {
    const hasFDA = await checkFullDiskAccess()
    if (!hasFDA) {
      promptUserToGrantPermission("Full Disk Access")
      return false
    }
  }
  
  // 2. 检查自动化权限
  if (operation.requiresAutomation) {
    const hasAutomation = await checkAutomationPermission(operation.targetApp)
    if (!hasAutomation) {
      promptUserToGrantPermission("Automation", operation.targetApp)
      return false
    }
  }
  
  return true
}
```

---

## 五、工具调用链

### 5.1 完整调用链

```
用户请求
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ OpenClaw Core                                                   │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 1. Skill 匹配                                                │ │
│ │    扫描 description 找到匹配的 Skill                         │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                           │                                     │
│                           ▼                                     │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 2. 读取 SKILL.md                                             │ │
│ │    获取 CLI 命令格式和参数                                    │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                           │                                     │
│                           ▼                                     │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 3. LLM 生成 bash 工具调用                                    │ │
│ │    tool_use: bash                                            │ │
│ │    command: things add "Task" --when today                   │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                           │                                     │
│                           ▼                                     │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 4. Bash 工具执行                                             │ │
│ │    exec("things add ...")                                    │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ CLI 工具 (things)                                               │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 1. 解析命令行参数                                            │ │
│ │ 2. 构建 URL Scheme 或调用 API                               │ │
│ │ 3. 执行操作                                                  │ │
│ │ 4. 返回结果                                                  │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 本地应用 (Things.app)                                           │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 1. 接收 URL Scheme / Apple Event                            │ │
│ │ 2. 执行操作（创建任务）                                       │ │
│ │ 3. 更新 UI                                                   │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 错误处理

```typescript
async function executeWithRetry(command: string, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const result = await exec(command)
      return result
    } catch (error) {
      // 检查错误类型
      if (isPermissionError(error)) {
        return { error: "Permission denied. Please grant Full Disk Access." }
      }
      if (isNotFoundError(error)) {
        return { error: "CLI tool not found. Please install it first." }
      }
      if (isNetworkError(error) && i < maxRetries - 1) {
        await delay(1000 * (i + 1))
        continue
      }
      throw error
    }
  }
}
```

---

## 六、总结

### 6.1 驱动模式对比

| 模式 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| CLI 桥接 | 灵活、可扩展 | 需要安装 CLI | 大多数应用 |
| URL Scheme | 无需额外安装 | 功能有限 | macOS/iOS 应用 |
| API/SDK | 功能完整 | 实现复杂 | 系统级集成 |

### 6.2 关键依赖

| 依赖 | 用途 |
|------|------|
| CLI 工具 | 命令行接口 |
| macOS 权限 | 文件访问、自动化 |
| URL Scheme | 应用唤起 |
| 网络协议 | 设备发现、API 调用 |

### 6.3 设计亮点

1. **Skill 系统模块化** - 知识注入与代码分离
2. **渐进式加载** - 优化 token 使用
3. **自动依赖管理** - 支持 brew/npm/go 安装
4. **安全机制** - tmux 会话、权限检查

### 6.4 改进方向

1. **内置验证** - 添加操作结果验证
2. **并行执行** - 支持多个工具并行
3. **沙箱隔离** - 更安全的执行环境
4. **跨平台兼容** - 扩展 Windows/Linux 支持
