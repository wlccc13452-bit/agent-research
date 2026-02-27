# OpenClaw Skill 实践案例：控制本地应用

本文档详细分析 OpenClaw 如何通过 Skill 系统控制各种本地应用程序。

---

## 1. 核心交互模式

### 1.1 三种主要模式

```
模式 A: CLI 工具桥接
┌─────────┐     ┌─────────┐     ┌─────────────┐
│  Agent  │────▶│ CLI工具 │────▶│  本地应用    │
└─────────┘     └─────────┘     └─────────────┘
示例: obsidian-cli → Obsidian, things → Things 3

模式 B: URL Scheme 调用
┌─────────┐     ┌─────────────┐     ┌─────────────┐
│  Agent  │────▶│ URL Scheme  │────▶│  本地应用    │
└─────────┘     └─────────────┘     └─────────────┘
示例: things://add?title=... → Things 3

模式 C: API/Webhook 集成
┌─────────┐     ┌───────────┐     ┌─────────────┐
│  Agent  │────▶│ message   │────▶│  远程服务    │
└─────────┘     │   tool    │     └─────────────┘
                └───────────┘
示例: Discord API, Slack Webhook
```

### 1.2 工具调用流程

```
用户请求: "添加一个任务到 Things"
     │
     ▼
┌─────────────────────────────────────────┐
│ 1. Agent 扫描 skills description        │
│    匹配: things-mac "Manage Things 3"   │
└─────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│ 2. Agent 读取 SKILL.md                  │
│    获取: things add "Title" 命令格式     │
└─────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│ 3. Agent 调用 exec 工具                 │
│    exec: "things add 'Buy milk'"        │
└─────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│ 4. things CLI 执行操作                  │
│    → 通过 URL scheme 唤起 Things.app    │
│    → 创建新任务                          │
└─────────────────────────────────────────┘
     │
     ▼
Agent 回复: "已添加任务 'Buy milk' 到 Things"
```

---

## 2. 详细案例分析

### 2.1 Obsidian - 文件系统型

**Skill 配置:**
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

**交互方式:**
```bash
# 查找活跃 vault
obsidian-cli print-default --path-only
# 输出: /Users/alice/Notes

# 搜索笔记
obsidian-cli search "meeting notes"
# 输出: 笔记名称列表

# 创建笔记
obsidian-cli create "Projects/New Project" --content "# Notes\n..." --open
# → 在 Obsidian 中打开新笔记

# 移动笔记（自动更新 wikilinks）
obsidian-cli move "old/path" "new/path"
```

**技术实现:**
- 读取 `~/Library/Application Support/obsidian/obsidian.json` 获取 vault 信息
- 使用 `obsidian://` URL scheme 创建笔记
- 直接操作 `.md` 文件进行搜索和移动

### 2.2 Things 3 - URL Scheme 型

**Skill 配置:**
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

**交互方式:**

**读取操作（直接读取数据库）:**
```bash
# 需要赋予 Full Disk Access
things inbox --limit 50
things today
things upcoming
things search "project query"
things projects
```

**写入操作（URL Scheme）:**
```bash
# 添加任务
things add "Buy milk" --notes "2%" --when today

# 添加到项目
things add "Book flights" --list "Travel"

# 更新任务
things update --id <UUID> --auth-token <TOKEN> --completed

# 预览（不实际执行）
things --dry-run add "Test task"
```

**URL Scheme 调用示例:**
```
things:///add?title=Buy%20milk&notes=2%25&when=today
```

**数据库路径:**
```
~/Library/Containers/com.culturedcode.ThingsMac/Data/Library/Application Support/Cultured Code/Things/ThingsData-<UUID>
```

### 2.3 Spotify - API 桥接型

**Skill 配置:**
```yaml
---
name: spotify-player
description: Terminal Spotify playback via spogo.
metadata:
  openclaw:
    requires: { anyBins: ["spogo", "spotify_player"] }
---
```

**交互方式:**
```bash
# 认证（导入浏览器 cookies）
spogo auth import --browser chrome

# 设备管理
spogo device list
spogo device set "Living Room Speaker"

# 播放控制
spogo play
spogo pause
spogo next
spogo prev

# 搜索
spogo search track "bohemian rhapsody"
spogo search artist "queen"

# 状态
spogo status
```

**认证流程:**
1. 用户在 Chrome 登录 Spotify
2. `spogo auth import` 导入 cookies
3. 后续请求使用 cookies 认证

### 2.4 Sonos - 本地网络控制型

**Skill 配置:**
```yaml
---
name: sonoscli
description: Control Sonos speakers on the local network.
metadata:
  openclaw:
    requires: { bins: ["sonos"] }
---
```

**交互方式:**
```bash
# 发现设备（SSDP 协议）
sonos discover

# 播放控制
sonos play --name "Kitchen"
sonos pause --name "Kitchen"
sonos stop --name "Kitchen"

# 音量控制
sonos volume set 15 --name "Kitchen"
sonos volume up --name "Kitchen"
sonos volume down --name "Kitchen"

# 分组
sonos group join --name "Kitchen" --main "Living Room"
sonos group party  # 所有设备同步

# 队列管理
sonos queue list --name "Kitchen"
sonos queue play --name "Kitchen" --index 3

# Spotify 集成
sonos smapi search --service "Spotify" --category tracks "query"
```

**网络协议:**
- SSDP (Simple Service Discovery Protocol) 发现设备
- UPnP/SOAP 控制播放
- SMAPI (Sonos Music API) 集成流媒体

### 2.5 Apple Notes - AppleScript 型

**Skill 配置:**
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

**交互方式:**
```bash
# 列出笔记
memo notes
memo notes -f "Work"

# 搜索
memo notes -s "meeting"

# 创建（交互式编辑器）
memo notes -a
memo notes -a "Quick note title"

# 编辑
memo notes -e

# 删除
memo notes -d

# 导出
memo notes -ex  # HTML/Markdown
```

**权限要求:**
- System Settings > Privacy & Security > Automation
- 允许 Terminal/OpenClaw.app 控制 Notes.app

**底层实现:**
```python
# memo 使用 AppleScript/PyObjC 与 Notes.app 交互
from ScriptingBridge import SBApplication

notes = SBApplication.applicationWithBundleIdentifier_("com.apple.Notes")
```

### 2.6 1Password - 安全认证型

**Skill 配置:**
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

**交互方式:**
```bash
# 认证流程
op signin --account my.1password.com
op whoami  # 验证

# 读取密钥
op item get "Database Password" --fields password
op read "op://Private/Server/password"

# 注入环境变量
op run -- python script.py  # 自动注入 secrets

# OTP
op read "op://Private/Npmjs/one-time password?attribute=otp"
```

**安全要求:**
```bash
# 必须在 tmux 会话中运行
SOCKET_DIR="${TMPDIR:-/tmp}/openclaw-tmux-sockets"
SOCKET="$SOCKET_DIR/openclaw-op.sock"
SESSION="op-auth-$(date +%Y%m%d-%H%M%S)"

tmux -S "$SOCKET" new -d -s "$SESSION"
tmux -S "$SOCKET" send-keys -t "$SESSION:0.0" -- "op signin" Enter
tmux -S "$SOCKET" capture-pane -p -J -t "$SESSION:0.0" -S -200
tmux -S "$SOCKET" kill-session -t "$SESSION"
```

---

## 3. 权限与安全模型

### 3.1 macOS 权限层次

```
┌────────────────────────────────────────────────────────┐
│                    权限层次                             │
├────────────────────────────────────────────────────────┤
│                                                        │
│  Level 1: 文件系统访问                                 │
│  ┌──────────────────────────────────────────────────┐ │
│  │ Full Disk Access (FDA)                           │ │
│  │ - 读取 Things 数据库                              │ │
│  │ - 访问任意用户文件                                │ │
│  └──────────────────────────────────────────────────┘ │
│                         │                              │
│                         ▼                              │
│  Level 2: 应用自动化                                    │
│  ┌──────────────────────────────────────────────────┐ │
│  │ Automation Permission                            │ │
│  │ - AppleScript 控制 Notes.app                     │ │
│  │ - UI scripting                                   │ │
│  └──────────────────────────────────────────────────┘ │
│                         │                              │
│                         ▼                              │
│  Level 3: 沙盒内操作                                    │
│  ┌──────────────────────────────────────────────────┐ │
│  │ Sandbox / Standard                               │ │
│  │ - 普通文件读写                                    │ │
│  │ - 网络请求                                       │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### 3.2 敏感操作处理

**1Password 示例:**

```markdown
## REQUIRED tmux session (T-Max)

The shell tool uses a fresh TTY per command. To avoid re-prompts 
and failures, always run `op` inside a dedicated tmux session.

Guardrails:
- Never paste secrets into logs, chat, or code.
- Prefer `op run` / `op inject` over writing secrets to disk.
- If sign-in without app integration is needed, use `op account add`.
- Do not run `op` outside tmux; stop and ask if tmux is unavailable.
```

---

## 4. Skill 与 Agent 工具链

### 4.1 工具调用关系

```
┌─────────────────────────────────────────────────────────────┐
│                      Agent 工具链                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐ │
│  │  read   │    │  exec   │    │ process │    │ message │ │
│  └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘ │
│       │              │              │              │        │
│       ▼              ▼              ▼              ▼        │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐ │
│  │读取     │    │执行CLI  │    │后台进程 │    │发送消息 │ │
│  │SKILL.md │    │工具     │    │管理     │    │到通道   │ │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘ │
│                      │                                      │
│                      ▼                                      │
│              ┌──────────────────┐                          │
│              │ CLI 工具调用      │                          │
│              │ - obsidian-cli   │                          │
│              │ - things         │                          │
│              │ - spogo          │                          │
│              │ - sonos          │                          │
│              │ - memo           │                          │
│              │ - op             │                          │
│              └──────────────────┘                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 典型调用序列

**场景: 用户说 "把我明天的会议添加到 Things"**

```
1. Agent 接收消息
   │
   ▼
2. Skill 匹配: things-mac
   │ read tool: skills/things-mac/SKILL.md
   │
   ▼
3. Agent 规划:
   │ "需要创建任务，使用 things add 命令"
   │
   ▼
4. exec tool:
   │ things add "明天会议" --notes "用户请求添加" --when tomorrow
   │
   ▼
5. CLI 执行:
   │ things3-cli 构建 URL scheme
   │ things:///add?title=...
   │ macOS 打开 URL → Things.app 创建任务
   │
   ▼
6. Agent 回复:
   "已添加任务 '明天会议' 到 Things，计划日期：明天"
```

---

## 5. 调试与故障排查

### 5.1 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| CLI not found | 未安装工具 | 运行 skill install |
| Permission denied | 缺少权限 | 授予 FDA/Automation |
| Device not found | 网络问题 | 检查 SSDP/防火墙 |
| Auth failed | 认证过期 | 重新登录/导入 cookies |
| Sandbox blocked | 沙盒限制 | 使用 elevated mode |

### 5.2 检查命令

```bash
# 检查 CLI 安装
which obsidian-cli
which things
which spogo
which sonos

# 检查权限 (macOS)
# System Settings > Privacy & Security > Full Disk Access
# System Settings > Privacy & Security > Automation

# 测试 CLI
obsidian-cli print-default
things inbox --limit 5
spogo status
sonos discover

# 检查 OpenClaw skill 状态
openclaw skills check
openclaw skills status
```

---

## 6. 创建自定义控制 Skill

### 6.1 模板：控制本地应用

```yaml
---
name: my-app-control
description: "Control MyLocalApp via myapp-cli. Use when user wants to [specific actions]."
homepage: https://myapp.com
metadata:
  openclaw:
    emoji: "📱"
    os: ["darwin"]  # 或 ["darwin", "linux"]
    requires:
      bins: ["myapp-cli"]
    install:
      - id: "brew"
        kind: "brew"
        formula: "myapp-cli"
        bins: ["myapp-cli"]
---

# MyLocalApp Control

Control MyLocalApp from the terminal.

## Setup

1. Install: `brew install myapp-cli`
2. Authenticate: `myapp-cli login`
3. Grant permissions if prompted (FDA/Automation)

## Common Commands

### Status
```bash
myapp-cli status
```

### Actions
```bash
myapp-cli do-something --option value
myapp-cli list-items
myapp-cli create-item "name"
```

## Troubleshooting

- **Permission denied**: Grant Full Disk Access
- **Not authenticated**: Run `myapp-cli login`
- **Device not found**: Check network connection
```

### 6.2 检查清单

- [ ] CLI 工具可通过 brew/go/npm 安装
- [ ] CLI 支持 non-interactive 模式
- [ ] 文档清晰说明权限需求
- [ ] 包含常见命令示例
- [ ] 说明 OS 兼容性
- [ ] 包含故障排查指南

---

## 7. 总结

OpenClaw Skill 系统控制本地应用的核心要点：

1. **CLI 工具是桥梁** - 几乎所有控制都通过 CLI 工具实现
2. **权限是关键** - macOS FDA/Automation 权限是必备条件
3. **URL Scheme 是补充** - 部分应用通过 URL scheme 唤起
4. **安全是底线** - 敏感操作需要特殊处理（tmux 会话）
5. **渐进式加载** - Skill 内容按需加载优化性能

通过这种设计，OpenClaw 实现了 AI Agent 与本地应用的深度集成，同时保持了安全性和可控性。
