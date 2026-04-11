# OpenClaw.ai 研究报告

## 项目概述

**openclaw.ai** 是 OpenClaw 的官方网站/落地页，是一个静态网站项目。

**仓库地址**: https://github.com/openclaw/openclaw.ai

---

## TASK 1: 计算架构与框架

### 1.1 技术栈

| 技术 | 用途 |
|------|------|
| **Astro** | 静态站点生成器 |
| **GitHub Pages** | 托管平台 |
| **Custom CSS** | 样式（无框架） |
| **Bun** | 包管理器 |

### 1.2 项目结构

```
openclaw.ai/
├── public/
│   ├── install.sh       # macOS/Linux 安装脚本
│   ├── install-cli.sh   # macOS/Linux CLI 安装脚本
│   ├── install.ps1      # Windows 安装脚本
│   └── images/          # 静态资源
├── src/
│   ├── pages/           # Astro 页面（16个 .astro 文件）
│   │   ├── index.astro  # 主页
│   │   ├── integrations.astro  # 集成展示页
│   │   └── shoutouts.astro     # 社区推荐页
│   └── components/      # UI 组件
├── astro.config.mjs     # Astro 配置
└── package.json
```

### 1.3 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Pages (CDN)                        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Static HTML/CSS/JS                      │   │
│  │  ┌─────────┐ ┌─────────────┐ ┌─────────────┐       │   │
│  │  │ Home    │ │Integration  │ │ Shoutouts   │       │   │
│  │  │ Page    │ │ Grid Page   │ │ Page        │       │   │
│  │  └─────────┘ └─────────────┘ └─────────────┘       │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          ▲
                          │ Deploy (main branch)
┌─────────────────────────────────────────────────────────────┐
│                    Build Pipeline                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Astro Build Process                                 │   │
│  │  .astro files → HTML + CSS + JS                      │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 1.4 安装脚本功能

网站承载了 OpenClaw 的安装脚本：

**macOS/Linux:**
```bash
curl -fsSL --proto '=https' --tlsv1.2 https://openclaw.ai/install.sh | bash
```

**Windows:**
```powershell
iwr -useb https://openclaw.ai/install.ps1 | iex
```

**安装流程：**
1. 检测并安装 Homebrew (macOS) 或包管理器
2. 安装 Node.js 22+（如果需要）
3. 通过 npm 全局安装 openclaw
4. 运行 `openclaw doctor --non-interactive`
5. 提示运行 `openclaw onboard`（新安装）

---

## TASK 2: 功能、思维模式与 LLM 交互

### 2.1 项目定位

**openclaw.ai 是一个静态网站项目，不是 AI Agent 应用。**

因此，TASK 2 中的核心问题（思维模式、思维链、LLM 交互设计）**不适用于此项目**。

### 2.2 实现的功能

| 功能 | 描述 |
|------|------|
| 产品展示 | OpenClaw 特性、快速开始指南 |
| 集成展示 | 支持的聊天平台、AI 模型、工具列表 |
| 社区推荐 | 用户评价和社区提及 |
| 安装分发 | 托管安装脚本 |

### 2.3 与主项目的关系

```
openclaw.ai (官网)          openclaw (主项目)
       │                           │
       │ 托管安装脚本               │ 核心代码
       ▼                           ▼
┌─────────────┐             ┌─────────────┐
│ install.sh  │────────────▶│ npm publish │
│ install.ps1 │             │ openclaw    │
└─────────────┘             └─────────────┘
```

---

## TASK 3: LLM 驱动本地 APP

### 不适用

**openclaw.ai 是一个静态网站，不涉及 LLM 与本地应用的交互。**

这个问题的研究应针对 **openclaw 主项目** 进行，详见 `openclaw` 研究报告。

---

## 总结

| 维度 | 分析结果 |
|------|----------|
| **项目类型** | 静态网站（Astro） |
| **TASK 1 适用性** | ✅ 可分析架构 |
| **TASK 2 适用性** | ❌ 无 LLM 交互设计 |
| **TASK 3 适用性** | ❌ 无本地 APP 控制 |
| **核心价值** | 产品展示 + 安装脚本分发 |

**结论**: openclaw.ai 是一个辅助项目，主要用于产品推广和安装入口。真正的 AI Agent 系统在 `openclaw` 主项目中。
