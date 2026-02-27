# OpenClaw Skill System Research

## 概述

OpenClaw 的 Skill 系统是一个模块化的扩展机制，允许 AI Agent 获得特定领域的知识、工作流程和工具集成能力。Skill 本质上是"入职指南"，将通用 AI 转变为具有专业知识的专家。

---

## 1. Skill 核心概念

### 1.1 什么是 Skill

Skill 是自包含的模块包，提供：
- **专业化工作流程** - 特定领域的多步骤程序
- **工具集成** - 与特定文件格式或 API 的交互指南
- **领域专业知识** - 公司特定知识、模式、业务逻辑
- **捆绑资源** - 复杂任务的脚本、参考和资产

### 1.2 Skill 目录结构

```
skill-name/
├── SKILL.md (必需)
│   ├── YAML frontmatter 元数据 (必需)
│   │   ├── name: (必需)
│   │   └── description: (必需)
│   └── Markdown 指令 (必需)
└── 捆绑资源 (可选)
    ├── scripts/          - 可执行代码 (Python/Bash 等)
    ├── references/       - 按需加载的参考文档
    └── assets/           - 输出文件 (模板、图标等)
```

### 1.3 渐进式披露设计

Skill 使用三级加载系统来高效管理上下文：

| 级别 | 内容 | 上下文占用 |
|------|------|-----------|
| 1. 元数据 | name + description | ~100 词，始终加载 |
| 2. SKILL.md 主体 | 详细指令 | <5k 词，触发时加载 |
| 3. 捆绑资源 | scripts/references/assets | 按需加载 |

---

## 2. Skill 加载机制

### 2.1 加载源优先级

Skill 从多个来源加载，按优先级合并（后者覆盖前者）：

```
extraDirs < bundled < managed < agents-skills-personal < agents-skills-project < workspace
```

**具体路径：**

| 来源 | 路径 | 说明 |
|------|------|------|
| bundled | `skills/` (项目内) | OpenClaw 内置 skill |
| managed | `~/.openclaw/skills/` | 用户管理的 skill |
| agents-skills-personal | `~/.agents/skills/` | 个人 agent skill |
| agents-skills-project | `<workspace>/.agents/skills/` | 项目级 agent skill |
| workspace | `<workspace>/skills/` | 工作区 skill |
| extraDirs | 配置指定 | 额外 skill 目录 |

### 2.2 核心加载函数

```typescript
// src/agents/skills/workspace.ts
function loadSkillEntries(workspaceDir: string, opts?: {...}): SkillEntry[] {
  // 1. 从各来源加载 skill
  const bundledSkills = loadSkills({ dir: bundledSkillsDir, source: "openclaw-bundled" });
  const managedSkills = loadSkills({ dir: managedSkillsDir, source: "openclaw-managed" });
  const workspaceSkills = loadSkills({ dir: workspaceSkillsDir, source: "openclaw-workspace" });
  
  // 2. 按优先级合并
  const merged = new Map<string, Skill>();
  for (const skill of extraSkills) merged.set(skill.name, skill);
  for (const skill of bundledSkills) merged.set(skill.name, skill);
  // ... 其他来源
  
  // 3. 解析 frontmatter 和元数据
  return skillEntries;
}
```

### 2.3 Skill 过滤逻辑

```typescript
// src/agents/skills/config.ts
function shouldIncludeSkill(params: {...}): boolean {
  // 1. 检查是否被配置禁用
  if (skillConfig?.enabled === false) return false;
  
  // 2. 检查 bundled allowlist
  if (!isBundledSkillAllowed(entry, allowBundled)) return false;
  
  // 3. 检查 OS 兼容性
  if (osList.length > 0 && !osList.includes(currentOS)) return false;
  
  // 4. always=true 的 skill 始终包含
  if (entry.metadata?.always === true) return true;
  
  // 5. 检查运行时依赖
  return evaluateRuntimeRequires({
    requires: entry.metadata?.requires,
    hasBin: hasBinary,
    hasEnv: (envName) => Boolean(process.env[envName]),
    isConfigPathTruthy: (path) => isConfigPathTruthy(config, path),
  });
}
```

---

## 3. Skill 与 System Prompt 集成

### 3.1 Skills Section 构建

```typescript
// src/agents/system-prompt.ts
function buildSkillsSection(params: {...}) {
  return [
    "## Skills (mandatory)",
    "Before replying: scan <available_skills> <description> entries.",
    `- If exactly one skill clearly applies: read its SKILL.md at <location> with read tool, then follow it.`,
    "- If multiple could apply: choose the most specific one.",
    "- If none clearly apply: do not read any SKILL.md.",
    "Constraints: never read more than one skill up front.",
    trimmed,  // 格式化后的 skill 列表
  ];
}
```

### 3.2 Agent 使用 Skill 的流程

```
1. 用户发送消息
2. Agent 扫描 <available_skills> 中的 description
3. 如果匹配：
   a. 使用 read 工具读取 SKILL.md
   b. 按照 SKILL.md 中的指令执行
4. 如果不匹配：直接回复
```

---

## 4. Skill 控制 Local App 的机制

### 4.1 核心模式：CLI 工具桥接

Skill 通过 **CLI 工具** 与本地应用交互，而非直接 API 调用：

```
Agent → Skill 指令 → CLI 工具 → 本地应用
```

### 4.2 典型 Skill 示例

#### Obsidian (笔记应用)
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
        bins: ["obsidian-cli"]
---
```

**操作方式：**
- `obsidian-cli search "query"` - 搜索笔记
- `obsidian-cli create "path/note" --content "..."` - 创建笔记
- `obsidian-cli move "old" "new"` - 移动/重命名

#### Things 3 (任务管理)
```yaml
---
name: things-mac
description: Manage Things 3 via the `things` CLI.
metadata:
  openclaw:
    os: ["darwin"]
    requires: { bins: ["things"] }
    install:
      - kind: go
        module: "github.com/ossianhempel/things3-cli/cmd/things@latest"
---
```

**操作方式：**
- `things inbox --limit 50` - 读取收件箱
- `things add "Buy milk" --notes "..."` - 添加任务
- `things update --id <UUID> --completed` - 完成任务

#### Spotify (音乐播放)
```yaml
---
name: spotify-player
description: Terminal Spotify playback via spogo.
metadata:
  openclaw:
    requires: { anyBins: ["spogo", "spotify_player"] }
---
```

**操作方式：**
- `spogo search track "query"` - 搜索歌曲
- `spogo play|pause|next|prev` - 播放控制
- `spogo device set "<name>"` - 切换设备

#### Sonos (音响控制)
```yaml
---
name: sonoscli
description: Control Sonos speakers.
metadata:
  openclaw:
    requires: { bins: ["sonos"] }
---
```

**操作方式：**
- `sonos discover` - 发现设备
- `sonos play|pause --name "Kitchen"` - 播放控制
- `sonos volume set 15 --name "Kitchen"` - 音量控制

### 4.3 交互方式分类

| 类型 | 示例 Skill | 交互方式 |
|------|-----------|---------|
| 文件系统 | obsidian, notion | 读写本地文件/vault |
| URL Scheme | things-mac | 通过 URL scheme 唤起应用 |
| CLI 工具 | spotify-player, sonoscli | 命令行控制 |
| API 桥接 | discord, slack | 通过 message 工具 |
| 系统集成 | apple-notes, apple-reminders | macOS Automation API |

---

## 5. Skill 安装机制

### 5.1 安装类型

```typescript
type SkillInstallSpec = {
  kind: "brew" | "node" | "go" | "uv" | "download";
  formula?: string;    // brew 公式
  package?: string;    // npm 包
  module?: string;     // go 模块
  bins?: string[];     // 安装后提供的二进制
  os?: string[];       // 支持的操作系统
};
```

### 5.2 安装命令生成

```typescript
// src/agents/skills-install.ts
function buildInstallCommand(spec: SkillInstallSpec, prefs: SkillsInstallPreferences) {
  switch (spec.kind) {
    case "brew":
      return { argv: ["brew", "install", spec.formula] };
    case "node":
      return { argv: buildNodeInstallCommand(spec.package, prefs) };
      // npm/pnpm/yarn/bun install -g
    case "go":
      return { argv: ["go", "install", spec.module] };
    case "uv":
      return { argv: ["uv", "tool", "install", spec.package] };
    case "download":
      // 特殊处理：下载并解压
  }
}
```

### 5.3 自动依赖处理

```typescript
// 自动安装缺失的依赖
async function ensureGoInstalled(params: {...}): Promise<SkillInstallResult | undefined> {
  if (hasBinary("go")) return undefined;
  
  if (brewExe) {
    return runCommandSafely([brewExe, "install", "go"]);
  }
  if (hasBinary("apt-get")) {
    return installGoViaApt();
  }
  // ...
}
```

---

## 6. Skill 元数据详解

### 6.1 Frontmatter 结构

```yaml
---
name: skill-name                    # 必需：skill 名称
description: "..."                  # 必需：触发描述
homepage: https://example.com       # 可选：主页
metadata:
  openclaw:
    emoji: "🎵"                     # 显示图标
    os: ["darwin"]                  # OS 限制
    always: true                    # 始终包含
    skillKey: "custom-key"          # 配置键名
    primaryEnv: "API_KEY"           # 主要环境变量
    requires:
      bins: ["tool1", "tool2"]      # 需要的二进制
      anyBins: ["tool1", "tool2"]   # 任一二进制
      env: ["API_KEY"]              # 需要的环境变量
      config: ["browser.enabled"]   # 需要的配置
    install:
      - id: "brew"
        kind: "brew"
        formula: "package-name"
        bins: ["binary-name"]
---
```

### 6.2 类型定义

```typescript
type OpenClawSkillMetadata = {
  always?: boolean;        // 始终包含
  skillKey?: string;       // 配置键名
  primaryEnv?: string;     // 主要环境变量
  emoji?: string;          // 显示图标
  homepage?: string;       // 主页
  os?: string[];           // OS 限制
  requires?: {
    bins?: string[];       // 必须全部存在
    anyBins?: string[];    // 任一存在即可
    env?: string[];        // 环境变量
    config?: string[];     // 配置路径
  };
  install?: SkillInstallSpec[];
};
```

### 6.3 调用策略

```typescript
type SkillInvocationPolicy = {
  userInvocable: boolean;          // 是否可通过命令调用
  disableModelInvocation: boolean; // 禁止模型自动触发
};
```

---

## 7. 具体 Skill 示例分析

### 7.1 GitHub Skill - API 交互型

```yaml
---
name: github
description: "GitHub operations via `gh` CLI: issues, PRs, CI runs..."
metadata:
  openclaw:
    emoji: "🐙"
    requires: { bins: ["gh"] }
    install:
      - kind: brew
        formula: "gh"
---
```

**特点：**
- 使用官方 CLI 工具
- 支持多种操作（PR、Issue、CI）
- 提供 JSON 输出和 jq 过滤

### 7.2 1Password Skill - 安全敏感型

```yaml
---
name: 1password
description: "Set up and use 1Password CLI (op)..."
metadata:
  openclaw:
    emoji: "🔐"
    requires: { bins: ["op"] }
---
```

**安全特性：**
- 必须在 tmux 会话中运行
- 使用桌面应用集成认证
- 永不在日志中暴露密钥

### 7.3 Coding Agent Skill - 委托型

```yaml
---
name: coding-agent
description: "Delegate coding tasks to Codex, Claude Code, or Pi agents..."
metadata:
  openclaw:
    emoji: "🧩"
    requires: { anyBins: ["claude", "codex", "opencode", "pi"] }
---
```

**特殊之处：**
- 需要 PTY 模式运行
- 支持后台任务
- 自动通知完成

### 7.4 Discord Skill - 消息通道型

```yaml
---
name: discord
description: "Discord ops via the message tool (channel=discord)."
metadata:
  openclaw:
    emoji: "🎮"
    requires: { config: ["channels.discord.token"] }
allowed-tools: ["message"]
---
```

**特点：**
- 不使用独立工具
- 通过 message 工具统一接口
- 支持 Components v2

---

## 8. 实战：创建自定义 Skill

### 8.1 基本模板

```yaml
---
name: my-skill
description: "Description that helps AI know when to use this skill. Include triggers and use cases."
metadata:
  openclaw:
    emoji: "🔧"
    os: ["darwin"]
    requires:
      bins: ["my-cli-tool"]
    install:
      - kind: brew
        formula: "my-cli-tool"
        bins: ["my-cli-tool"]
---

# My Skill

Brief overview of what this skill does.

## Setup

Installation and authentication steps.

## Common Commands

```bash
my-cli-tool command --option value
```

## Notes

- Important limitations
- Platform requirements
```

### 8.2 最佳实践

1. **简洁描述** - description 是主要触发机制，包含"何时使用"
2. **渐进式内容** - 核心指令在 SKILL.md，详细参考在 references/
3. **清晰示例** - 代码示例比冗长解释更有效
4. **明确限制** - 说明 OS 限制、权限需求等
5. **测试脚本** - 捆绑的 scripts/ 必须经过测试

---

## 9. 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     OpenClaw Runtime                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │   Config    │───▶│   Skills    │───▶│   System    │    │
│  │  (YAML)     │    │   Loader    │    │   Prompt    │    │
│  └─────────────┘    └──────┬──────┘    └──────┬──────┘    │
│                            │                   │            │
│                            ▼                   ▼            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    Skill Sources                     │   │
│  │  bundled < managed < personal < project < workspace  │   │
│  └─────────────────────────────────────────────────────┘   │
│                            │                               │
│                            ▼                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   Agent Runtime                      │   │
│  │  ┌───────────┐  ┌───────────┐  ┌─────────────┐     │   │
│  │  │  Skills   │  │   Tools   │  │   Memory    │     │   │
│  │  │  Prompt   │  │ (exec,    │  │   System    │     │   │
│  │  │           │  │  read...) │  │             │     │   │
│  │  └─────┬─────┘  └─────┬─────┘  └─────────────┘     │   │
│  └────────┼──────────────┼─────────────────────────────┘   │
│           │              │                                  │
│           ▼              ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   Local Apps                         │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐  │   │
│  │  │Obsidian │ │ Things  │ │ Spotify │ │ Discord  │  │   │
│  │  │  CLI    │ │   CLI   │ │   CLI   │ │  API     │  │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └──────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 10. 关键源文件

| 文件 | 功能 |
|------|------|
| `src/agents/skills.ts` | 主入口，导出核心函数 |
| `src/agents/skills/workspace.ts` | Skill 加载和过滤逻辑 |
| `src/agents/skills/types.ts` | 类型定义 |
| `src/agents/skills/config.ts` | 配置解析和过滤逻辑 |
| `src/agents/skills/install.ts` | Skill 依赖安装 |
| `src/agents/skills/frontmatter.ts` | YAML 元数据解析 |
| `src/agents/system-prompt.ts` | System Prompt 构建 |
| `skills/skill-creator/SKILL.md` | Skill 创建指南 |

---

## 11. 总结

OpenClaw 的 Skill 系统通过以下机制实现 AI 与本地应用的交互：

1. **声明式元数据** - 通过 YAML frontmatter 声明依赖和安装方式
2. **CLI 工具桥接** - 大多数 skill 通过 CLI 工具控制本地应用
3. **渐进式加载** - 元数据始终加载，详细内容按需加载
4. **自动依赖管理** - 支持多种安装方式（brew/npm/go/uv）
5. **上下文高效** - 通过精简描述和分层加载优化 token 使用

这种设计使得 AI Agent 能够安全、可控地与各种本地应用交互，同时保持上下文窗口的高效利用。
