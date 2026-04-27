命令模式
使用斜杠命令快速执行操作：

/refactor - 重构当前代码
/test - 生成单元测试
/explain - 解释代码逻辑


/refactor	重构代码	/refactor
/test	生成测试	/test
/fix	修复错误	/fix
/optimize	优化性能	/optimize
/document	生成文档	/document
/translate	翻译代码	/translate python

 Codebuddy 会保存我的代码吗？
A: 不会。Codebuddy 不会保存或上传你的代码到云端，所有处理都在本地完成。

下一步
高级用法 - 学习更多高级功能
MCP 集成 - 了解如何集成外部工具
自定义技能 - 创建自己的技能 ###PATH:docs/docs/advanced/custom-skills.md ###LANGUAGE:Markdown
sidebar_position: 2
自定义技能
学习如何创建和使用自定义技能来扩展 Codebuddy 的功能。

什么是自定义技能？
自定义技能是一组预定义的指令和工作流，可以帮助 Codebuddy 更好地完成特定任务。

技能文件结构
.skills/
└── my-skill/
    ├── skill.md          # 技能定义文件（必需）
    ├── templates/        # 模板文件夹（可选）
    │   └── component.ts
    └── examples/         # 示例文件夹（可选）
        └── example.md
创建技能
1. 创建技能文件
在项目根目录的 .skills/ 文件夹中创建新技能：

bash
复制
mkdir -p .skills/my-skill
touch .skills/my-skill/skill.md
2. 编写技能定义
编辑 skill.md 文件：

markdown
复制
# My Custom Skill

## 描述
这个技能用于快速生成 React 组件

## 触发条件
当用户说 "创建组件" 或 "generate component" 时触发

## 参数
- name: 组件名称（必需）
- type: 组件类型（可选，默认为 functional）
- style: 样式方案（可选，默认为 css）

## 工作流程

### 第一步：确认参数
如果用户没有提供所有必需参数，询问用户。

### 第二步：生成组件代码
根据参数生成组件代码。

### 第三步：创建文件
在 src/components/ 目录下创建组件文件。

### 第四步：生成测试
为组件生成单元测试文件。

## 示例

### 示例 1：基本用法
用户输入：
创建组件 Button


Codebuddy 输出：
已创建以下文件：

src/components/Button/Button.tsx
src/components/Button/Button.test.tsx
src/components/Button/Button.css

### 示例 2：指定类型
用户输入：
创建组件 Modal type=class style=styled-components


Codebuddy 输出：
已创建以下文件：

src/components/Modal/Modal.tsx
src/components/Modal/Modal.test.tsx
src/components/Modal/Modal.styles.ts

## 模板

### 组件模板
文件：templates/component.ts

```typescript
import React from 'react';
import './{{name}}.css';

interface {{name}}Props {
  // Define props here
}

export const {{name}}: React.FC<{{name}}Props> = (props) => {
  return (
    <div className="{{name | kebabCase}}">
      {{name}} Component
    </div>
  );
};
最佳实践
提供清晰的描述和示例
使用参数化模板提高灵活性
包含错误处理和验证
添加有用的注释和文档

### 3. 注册技能

在 `.codebuddy/config.json` 中注册技能：

```json
{
  "skills": [
    ".skills/my-skill"
  ]
}
使用技能
基本用法
创建组件 Button
带参数
创建组件 Modal type=class style=styled-components
技能最佳实践
1. 清晰的触发条件
markdown
复制
## 触发条件
- 用户明确提到技能名称
- 使用特定关键词组合
- 在特定上下文中
2. 参数验证
markdown
复制
## 参数验证
- name: 不能为空，只能包含字母和数字
- type: 必须是 'functional' 或 'class'
- style: 必须是 'css', 'scss', 'styled-components' 之一
3. 错误处理
markdown
复制
## 错误处理
如果参数验证失败：
1. 显示友好的错误消息
2. 提供正确的参数示例
3. 询问用户是否要重新输入
4. 提供反馈
markdown
复制
## 反馈机制
执行完成后：
1. 显示创建的文件列表
2. 提供下一步建议
3. 询问是否需要进一步修改
内置变量
Codebuddy 提供了一些内置变量，可以在技能中使用：

变量	说明	示例
{{name}}	组件名称	Button
`{{name	kebabCase}}`	短横线命名
`{{name	pascalCase}}`	帕斯卡命名
`{{name	camelCase}}`	驼峰命名
{{date}}	当前日期	2024-01-15
{{time}}	当前时间	14:30:00
示例技能
React 组件生成器
markdown
复制
# React Component Generator

## 描述
快速生成 React 组件，支持函数式和类组件

## 触发条件
当用户说 "创建组件" 或 "generate component"

## 工作流程
1. 询问组件名称（如果未提供）
2. 选择组件类型（函数式/类组件）
3. 选择样式方案（CSS/SCSS/Styled-components）
4. 生成组件代码
5. 创建测试文件
6. 创建样式文件
API 接口生成器
markdown

解如何使用 Model Context Protocol (MCP) 扩展 Codebuddy 的功能。

什么是 MCP？
Model Context Protocol (MCP) 是一个开放协议，允许 AI 助手与外部工具和数据源进行交互。通过 MCP，Codebuddy 可以：

访问本地文件系统
连接数据库
调用外部 API
使用自定义工具
配置 MCP
基本配置
在项目根目录创建 .codebuddy/mcp-config.json 文件：

json
复制
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/path/to/your/project"
      ]
    }
  }
}
多服务器配置
你可以同时配置多个 MCP 服务器：

json
复制
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/project"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "your-github-token"
      }
    },
    "database": {
      "command": "node",
      "args": ["/path/to/custom-server.js"],
      "env": {
        "DATABASE_URL": "postgresql://localhost/mydb"
      }
    }
  }
}
官方 MCP 服务器
文件系统服务器
提供文件系统访问能力：

json
复制
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/project"]
    }
  }
}
功能：

读取文件
写入文件
创建目录
列出文件
GitHub 服务器
集成 GitHub 功能：

json
复制
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "your-github-token"
      }
    }
  }
}
功能：

创建 Issue
创建 Pull Request
查看代码
管理仓库
PostgreSQL 服务器
连接 PostgreSQL 数据库：

json
复制
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_CONNECTION_STRING": "postgresql://user:pass@localhost/db"
      }
    }
  }
}
功能：

执行 SQL 查询
查看表结构
数据分析
创建自定义 MCP 服务器
基本结构
typescript
复制
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';

const server = new Server({
  name: 'my-custom-server',
  version: '1.0.0',
}, {
  capabilities: {
    tools: {},
  },
});

// 定义工具
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'my_tool',
        description: 'My custom tool',
        inputSchema: {
          type: 'object',
          properties: {
            param1: { type: 'string' },
          },
        },
      },
    ],
  };
});

// 处理工具调用
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === 'my_tool') {
    // 处理逻辑
    return {
      content: [
        {
          type: 'text',
          text: 'Result',
        },
      ],
    };
  }
});

// 启动服务器
const transport = new StdioServerTransport();
await server.connect(transport);
完整示例
typescript
复制
// weather-server.ts
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';

const server = new Server({
  name: 'weather-server',
  version: '1.0.0',
}, {
  capabilities: {
    tools: {},
  },
});

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'get_weather',
        description: 'Get current weather for a city',
        inputSchema: {
          type: 'object',
          properties: {
            city: {
              type: 'string',
              description: 'City name',
            },
          },
          required: ['city'],
        },
      },
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === 'get_weather') {
    const { city } = request.params.arguments;
    
    // 调用天气 API
    const weather = await fetchWeather(city);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(weather),
        },
      ],
    };
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
使用 MCP 工具
MCP 工具会自动集成到 Codebuddy 中，你可以像使用内置功能一样使用它们。

示例：文件系统
读取 src/index.ts 文件的内容
Codebuddy 会自动使用 filesystem MCP 服务器来读取文件。

示例：GitHub
为这个仓库创建一个 Issue，标题是"修复登录Bug"
示例：数据库
查询 users 表中最近注册的 10 个用户
最佳实践
1. 安全配置
不要在配置文件中硬编码敏感信息：

json
复制
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
2. 权限控制
限制 MCP 服务器的访问范围：

json
复制
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/path/to/project/src"
      ]
    }
  }
}
3. 错误处理
在自定义服务器中添加适当的错误处理：

typescript
复制
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  try {
    // 处理逻辑
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: `Error: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
});
4. 日志记录
添加日志以便调试：

typescript
复制
console.error('Tool called:', request.params.name);
console.error('Arguments:', request.params.arguments);
调试 MCP
查看日志
bash
复制
tail -f ~/.codebuddy/logs/mcp.log
测试服务器
bash
复制
# 手动运行服务器
npx -y @modelcontextprotocol/server-filesystem /path/to/project
常见问题
Q: MCP 服务器无法启动

检查：

Node.js 是否安装
npx 是否可用
路径是否正确
Q: 工具调用失败

检查：

参数是否正确
环境变量是否设置
权限是否足够
示例项目
查看完整的 MCP 集成示例：

文件系统集成
GitHub 集成
数据库集成
下一步
自定义技能 - 创建自定义技能
高级用法 - 学习高级功能
常见问题 - 查看常见问题解答 ###PATH:docs/docs/getting-started/installation.md ###LANGUAGE:Markdown
sidebar_position: 1
安装指南
本指南将帮助你在几分钟内完成 Codebuddy 的安装和配置。

系统要求
操作系统
Windows 10/11
macOS 10.15 (Catalina) 或更高版本
Linux (Ubuntu 18.04+, Fedora 30+, 或其他主流发行版)
硬件要求
内存: 最低 4GB RAM (推荐 8GB+)
存储空间: 至少 500MB 可用空间
网络: 需要网络连接 (用于 AI 模型调用)
软件依赖
Node.js 16.0 或更高版本
npm 7.0 或更高版本
安装方式
方式一：通过 IDE 插件安装 (推荐)
Codebuddy 支持主流 IDE，选择你的 IDE 进行安装：

VS Code
打开 VS Code
点击左侧扩展图标 (或按 Ctrl+Shift+X)
搜索 "Codebuddy"
点击 "Install"
或者通过命令行安装：

bash
复制
code --install-extension codebuddy.codebuddy-vscode
JetBrains IDEs (IntelliJ IDEA, PyCharm, WebStorm 等)
打开 IDE 设置 (File > Settings 或 Preferences)
导航到 Plugins
选择 Marketplace 标签
搜索 "Codebuddy"
点击 "Install"
方式二：通过命令行安装
如果你更喜欢使用命令行工具：

bash
复制
# 使用 npm 安装
npm install -g @codebuddy/cli

# 或使用 yarn
yarn global add @codebuddy/cli
安装完成后，验证安装：

bash
复制
codebuddy --version
方式三：从源码构建
对于开发者或需要自定义配置的用户：

bash
复制
# 克隆仓库
git clone https://github.com/codebuddy/codebuddy.git

# 进入项目目录
cd codebuddy

# 安装依赖
npm install

# 构建项目
npm run build

# 全局链接
npm link
首次配置
1. 初始化配置
首次运行时，Codebuddy 会引导你完成初始化配置：

bash
复制
codebuddy init
这会创建必要的配置文件和目录：

~/.codebuddy/config.json - 全局配置文件
~/.codebuddy/cache/ - 缓存目录
~/.codebuddy/logs/ - 日志目录
2. 配置 AI 模型
Codebuddy 支持多种 AI 模型提供商。编辑 ~/.codebuddy/config.json：

使用 Claude (推荐)
json
复制
{
  "ai": {
    "provider": "anthropic",
    "model": "claude-3-5-sonnet",
    "apiKey": "your-api-key-here"
  }
}
获取 API Key: Anthropic Console

使用 OpenAI
json
复制
{
  "ai": {
    "provider": "openai",
    "model": "gpt-4",
    "apiKey": "your-api-key-here"
  }
}
获取 API Key: OpenAI Platform

使用本地模型
如果你有本地部署的模型：

json
复制
{
  "ai": {
    "provider": "local",
    "endpoint": "http://localhost:8080/v1",
    "model": "your-model-name"
  }
}
3. 项目级配置 (可选)
在项目根目录创建 .codebuddy/config.json 进行项目特定配置：

json
复制
{
  "project": {
    "name": "My Project",
    "language": "typescript",
    "framework": "react"
  },
  "rules": [
    "Use TypeScript strict mode",
    "Follow Airbnb style guide"
  ]
}
验证安装
运行以下命令验证安装是否成功：

bash
复制
# 检查版本
codebuddy --version

# 测试连接
codebuddy test

# 查看帮助
codebuddy --help
更新
更新 IDE 插件
在 IDE 的扩展管理器中点击 "Update"。

更新命令行工具
bash
复制
# npm
npm update -g @codebuddy/cli

# yarn
yarn global upgrade @codebuddy/cli
卸载
卸载 IDE 插件
在 IDE 的扩展管理器中找到 Codebuddy，点击 "Uninstall"。

卸载命令行工具
bash
复制
# npm
npm uninstall -g @codebuddy/cli

# yarn
yarn global remove @codebuddy/cli

# 清理配置文件
rm -rf ~/.codebuddy
常见问题
Q: 安装后无法启动？
A: 检查以下几点：

Node.js 版本是否符合要求
PATH 环境变量是否正确配置
是否有足够的权限
Q: 配置文件在哪里？
A:

全局配置: ~/.codebuddy/config.json
项目配置: .codebuddy/config.json
Q: 如何更改语言？
A: 在配置文件中设置：

json
复制
{
  "language": "zh-CN"
}
Q: 支持哪些编程语言？
A: Codebuddy 支持所有主流编程语言，包括：

JavaScript/TypeScript
Python
Java
C/C++
Go
Rust
等等
下一步
安装完成后，建议阅读：

配置向导 - 了解更多配置选项
快速开始 - 学习基本功能
示例项目 - 查看实际应用案例
获取帮助
如果遇到问题：

📖 查看 常见问题
💬 加入社区讨论
📧 提交问题反馈 ###PATH:docs/docs/getting-started/configuration.md ###LANGUAGE:Markdown
sidebar_position: 2
配置向导
完成 Codebuddy 的配置，让它更好地服务于你的项目。

配置文件结构
Codebuddy 使用两级配置：

~/.codebuddy/              # 全局配置目录
├── config.json           # 全局配置文件
├── cache/                # 全局缓存
└── logs/                 # 全局日志

your-project/
└── .codebuddy/           # 项目配置目录
    ├── config.json       # 项目配置文件
    ├── mcp-config.json   # MCP 服务器配置
    ├── skills/           # 自定义技能
    └── rules/            # 项目规则
全局配置
AI 模型配置
编辑 ~/.codebuddy/config.json：

json
复制
{
  "ai": {
    "provider": "anthropic",
    "model": "claude-3-5-sonnet",
    "apiKey": "${ANTHROPIC_API_KEY}",
    "temperature": 0.7,
    "maxTokens": 4096
  }
}
参数说明：

provider: AI 服务提供商 (anthropic, openai, local)
model: 模型名称
apiKey: API 密钥（建议使用环境变量）
temperature: 创造性程度 (0-1)
maxTokens: 最大输出长度
编辑器配置
json
复制
{
  "editor": {
    "autoComplete": true,
    "autoFormat": true,
    "formatOnSave": true,
    "lintOnSave": true,
    "tabSize": 2,
    "insertSpaces": true
  }
}
界面配置
json
复制
{
  "ui": {
    "theme": "dark",
    "language": "zh-CN",
    "fontSize": 14,
    "showLineNumbers": true,
    "minimap": true
  }
}
项目配置
基本配置
在项目根目录创建 .codebuddy/config.json：

json
复制
{
  "project": {
    "name": "My Awesome Project",
    "description": "A brief description",
    "language": "typescript",
    "framework": "react",
    "version": "1.0.0"
  },
  "context": {
    "srcDir": "src",
    "testDir": "tests",
    "outputDir": "dist",
    "exclude": ["node_modules", "dist", ".git"]
  }
}
编码规范
定义项目的编码规范：

json
复制
{
  "rules": [
    "使用 TypeScript strict mode",
    "遵循 Airbnb 编码规范",
    "函数必须有 JSDoc 注释",
    "变量使用 camelCase 命名",
    "组件使用 PascalCase 命名",
    "常量使用 UPPER_SNAKE_CASE 命名"
  ]
}
或者创建 .codebuddy/rules/coding.md 文件：

markdown
复制
# 编码规范

## 命名规范

- 变量：使用 camelCase
  ```typescript
  const userName = 'John';
函数：使用 camelCase，动词开头

typescript
复制
function getUserById(id: string) { }
组件：使用 PascalCase

typescript
复制
function UserProfile() { }
注释规范
公共函数必须有 JSDoc 注释
复杂逻辑必须有行内注释
TODO 必须包含作者和日期
测试规范
单元测试覆盖率 > 80%
集成测试覆盖核心流程
E2E 测试覆盖关键用户路径

### 技术栈配置

指定项目使用的技术栈：

```json
{
  "stack": {
    "frontend": {
      "framework": "react",
      "language": "typescript",
      "styling": "tailwindcss",
      "testing": "jest"
    },
    "backend": {
      "runtime": "node",
      "framework": "express",
      "database": "postgresql",
      "orm": "prisma"
    },
    "tools": {
      "bundler": "vite",
      "linting": "eslint",
      "formatting": "prettier"
    }
  }
}
MCP 配置
配置 Model Context Protocol 服务器：

文件系统访问
json
复制
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "${workspaceFolder}"
      ]
    }
  }
}
GitHub 集成
json
复制
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
数据库集成
json
复制
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_CONNECTION_STRING": "${DATABASE_URL}"
      }
    }
  }
}
环境变量
使用环境变量保护敏感信息：

创建 .env 文件
bash
复制
# AI 服务配置
ANTHROPIC_API_KEY=sk-ant-xxxxx
OPENAI_API_KEY=sk-xxxxx

# GitHub 配置
GITHUB_TOKEN=ghp_xxxxx

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/mydb
在配置中引用
json
复制
{
  "ai": {
    "apiKey": "${ANTHROPIC_API_KEY}"
  },
  "mcpServers": {
    "github": {
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
高级配置
自定义命令
创建 .codebuddy/commands.json：

json
复制
{
  "commands": {
    "lint": {
      "description": "运行 ESLint 检查",
      "command": "npm run lint"
    },
    "test": {
      "description": "运行测试",
      "command": "npm test"
    },
    "build": {
      "description": "构建项目",
      "command": "npm run build"
    }
  }
}
模板配置
创建 .codebuddy/templates/ 目录：

.codebuddy/templates/
├── component.ts
├── service.ts
├── test.ts
└── readme.md
模板示例 (component.ts)：

typescript
复制
import React from 'react';

interface {{ComponentName}}Props {
  // Add props here
}

export const {{ComponentName}}: React.FC<{{ComponentName}}Props> = (props) => {
  return (
    <div className="{{component-name}}">
      {{ComponentName}} Component
    </div>
  );
};
缓存配置
json
复制
{
  "cache": {
    "enabled": true,
    "maxSize": "500MB",
    "ttl": 3600,
    "location": "~/.codebuddy/cache"
  }
}
日志配置
json
复制
{
  "logging": {
    "level": "info",
    "file": "~/.codebuddy/logs/codebuddy.log",
    "maxSize": "10MB",
    "maxFiles": 5
  }
}
配置示例
React + TypeScript 项目
json
复制
{
  "project": {
    "name": "My React App",
    "language": "typescript",
    "framework": "react"
  },
  "rules": [
    "使用函数式组件",
    "使用 React Hooks",
    "组件拆分到单独文件",
    "使用 CSS Modules 或 styled-components"
  ],
  "stack": {
    "frontend": {
      "framework": "react",
      "language": "typescript",
      "styling": "tailwindcss",
      "testing": "jest"
    }
  },
  "context": {
    "srcDir": "src",
    "testDir": "src/__tests__",
    "exclude": ["node_modules", "build", ".git"]
  }
}
Node.js API 项目
json
复制
{
  "project": {
    "name": "My API",
    "language": "typescript",
    "type": "api"
  },
  "rules": [
    "遵循 RESTful API 设计",
    "使用 Express Router",
    "添加请求验证",
    "统一错误处理"
  ],
  "stack": {
    "backend": {
      "runtime": "node",
      "framework": "express",
      "database": "postgresql",
      "orm": "prisma"
    }
  }
}
验证配置
使用以下命令验证配置是否正确：

bash
复制
# 验证配置文件
codebuddy config validate

# 查看当前配置
codebuddy config show

# 测试 AI 连接
codebuddy test
常见问题
Q: 配置文件优先级？
A: 项目配置 > 全局配置 > 默认配置

Q: 如何重置配置？
A:

bash
复制
codebuddy config reset
Q: 配置更改后需要重启吗？
A: 大部分配置会自动生效，但以下情况需要重启：

修改 AI 模型配置
添加/删除 MCP 服务器
修改缓存位置
下一步
基本操作 - 学习如何使用 Codebuddy
MCP 集成 - 配置外部工具集成
自定义技能 - 创建自定义技能 ###PATH:docs/blog/2019-05-28-first-blog-post.md ###LANGUAGE:Markdown
slug: first-blog-post title: First Blog Post authors: name: Gao Wei title: Docusaurus Core Team url: https://github.com/wgao19 image_url: https://github.com/wgao19.png tags: [hola, docusaurus]
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque elementum dignissim ultricies. Fusce rhoncus ipsum tempor eros aliquam consequat. Lorem ipsum dolor sit amet

###PATH:docs/blog/2021-08-26-welcome/index.md ###LANGUAGE:Markdown
slug: welcome title: Welcome authors: [slorber, yangshun] tags: [facebook, hello, docusaurus]
Docusaurus blogging features are powered by the blog plugin.

Simply add Markdown files (or folders) to the blog directory.

Regular blog authors can be added to authors.yml.

The blog post date can be extracted from filenames, such as:

2019-05-30-welcome.md
2019-05-30-welcome/index.md
A blog post folder can be convenient:

index.md with date: 2021-08-26 frontmatter
authors.yml file for blog post authors
docusaurus.png file for blog post image
The blog supports tags as well!

And if you don't want a blog: just delete this directory, and use blog: false in your Docusaurus config.

###PATH:docs/blog/2021-08-01-mdx-blog-post.mdx ###LANGUAGE:Markdown
slug: mdx-blog-post title: MDX Blog Post authors: [slorber] tags: [docusaurus]
Blog posts support Docusaurus Markdown features, such as MDX.

:::tip

Use the power of React to create interactive blog posts.

:::

For example, use JSX to create an interactive button:

js
复制
<button onClick={() => alert('button clicked!')}>Click me!</button>
<button onClick={() => alert('button clicked!')}>Click me!

This is just an example, in real practice you should avoid interactive content in server-rendered markdown.

###PATH:docs/blog/2021-09-01-docusaurus-how-to/index.md ###LANGUAGE:Markdown
slug: docusaurus-how-to title: How to use Docusaurus authors: [codebuddy] tags: [docusaurus, documentation]
How to Use Docusaurus
This guide will help you understand how to use Docusaurus effectively.

Getting Started
First, create a new Docusaurus project:

bash
复制
npx create-docusaurus@latest my-website classic
Writing Documentation
Create new documentation files in the docs folder:

markdown
复制
---
sidebar_position: 2
---

# My Document

Content goes here...
Adding Blog Posts
Add blog posts in the blog folder:

markdown
复制
---
slug: my-blog-post
title: My Blog Post
authors: [me]
---

Blog content here...
Deployment
Deploy your site:

bash
复制
npm run build
npm run serve
That's it! You now have a documentation site running. ###PATH:test/client-test/README.md ###LANGUAGE:Markdown

客户端测试工具
本目录包含用于测试股票 PEG 系统客户端功能的 Node.js 脚本。

文件说明
test_kline_fast_load.mjs - K线快速加载测试工具
test_holdings_api.mjs - 持仓数据 API 测试工具
测试报告.md - K线快速加载功能的详细测试报告
package.json - 项目依赖配置
使用方法
1. 安装依赖
bash
复制
cd test/client-test
npm install
2. 确保后端服务已启动
后端服务应运行在 http://localhost:8000

3. 运行测试
K线快速加载测试
bash
复制
npm run test:kline
这个测试会：

获取所有自持股票列表
逐个测试每只股票的 K 线数据加载速度
统计本地数据可用率和加载耗时
生成详细的测试报告
持仓数据 API 测试
bash
复制
npm run test:holdings
这个测试会：

测试 /api/holdings/ 端点
测试 /api/holdings/sectors 端点
测试 /api/holdings/stocks 端点
测试 WebSocket 连接和数据推送
测试结果
测试完成后，结果会输出到控制台，包括：

API 响应时间
数据可用性统计
错误信息（如果有）
注意事项
确保后端服务正常运行
确保数据库中有测试数据
测试脚本使用 ES Modules (import/export)
测试结果仅供参考，实际性能可能因环境而异
相关文档
K线快速加载测试报告
后端 API 文档
前端开发文档 ###PATH:test/client-test/test_kline_fast_load.mjs ###LANGUAGE:JavaScript #!/usr/bin/env node
/**

K线快速加载测试工具
测试前端调用后端 API 的响应速度和数据可用性
使用方法：
node test_kline_fast_load.mjs */
import fetch from 'node-fetch';

const API_BASE_URL = 'http://localhost:8000';

// ANSI 颜色代码 const colors = { reset: '\x1b[0m', bright: '\x1b[1m', red: '\x1b[31m', green: '\x1b[32m', yellow: '\x1b[33m', blue: '\x1b[34m', cyan: '\x1b[36m', };

// 日志工具 const log = { info: (msg) => console.log(${colors.cyan}ℹ${colors.reset} ${msg}), success: (msg) => console.log(${colors.green}✓${colors.reset} ${msg}), error: (msg) => console.log(${colors.red}✗${colors.reset} ${msg}), warn: (msg) => console.log(${colors.yellow}⚠${colors.reset} ${msg}), header: (msg) => console.log(\n${colors.bright}${colors.blue}${msg}${colors.reset}\n), };

// 格式化时间 function formatDuration(ms) { if (ms < 1000) return ${ms}ms; return ${(ms / 1000).toFixed(2)}s; }

// 测试获取持仓股票 async function testGetHoldings() { log.header('测试 1: 获取持仓股票列表');

const start = Date.now(); try { const response = await fetch(${API_BASE_URL}/api/holdings/); const data = await response.json(); const duration = Date.now() - start;

if (!response.ok) {
  log.error(`HTTP ${response.status}: ${response.statusText}`);
  return null;
}

const stocks = data?.holdings?.sectors?.flatMap(s => s.stocks || []) || [];
log.success(`获取到 ${stocks.length} 只股票，耗时 ${formatDuration(duration)}`);

return stocks.map(s => s.code);
} catch (error) { log.error(请求失败: ${error.message}); return null; } }

// 测试单只股票的 K 线加载 async function testKlineLoad(stockCode) { const start = Date.now(); try { const response = await fetch( ${API_BASE_URL}/api/stocks/kline-quick/${stockCode}?period=day&count=100&quick_load=true ); const data = await response.json(); const duration = Date.now() - start;

return {
  stockCode,
  success: response.ok,
  duration,
  dataAvailable: data?.local_data_available || false,
  dataCount: data?.data?.length || 0,
  isUpdating: data?.is_updating || false,
  lastUpdate: data?.last_update || null,
};
} catch (error) { return { stockCode, success: false, duration: Date.now() - start, error: error.message, }; } }

// 测试所有股票的 K 线加载 async function testAllKlines(stockCodes) { log.header('测试 2: K线快速加载性能测试');

if (!stockCodes || stockCodes.length === 0) { log.warn('没有股票需要测试'); return; }

log.info(开始测试 ${stockCodes.length} 只股票的 K 线加载...);

const results = []; const batchSize = 3; // 并发请求数

for (let i = 0; i < stockCodes.length; i += batchSize) { const batch = stockCodes.slice(i, i + batchSize); const batchResults = await Promise.all(batch.map(testKlineLoad)); results.push(...batchResults);

// 显示进度
batchResults.forEach(result => {
  if (result.success) {
    const status = result.dataAvailable ? '✓' : '✗';
    log.success(
      `${result.stockCode}: ${formatDuration(result.duration)} | ` +
      `数据${status} (${result.dataCount}条)` +
      (result.isUpdating ? ' | 后台更新中' : '')
    );
  } else {
    log.error(`${result.stockCode}: 失败 - ${result.error}`);
  }
});

// 批次间休息，避免过载
if (i + batchSize < stockCodes.length) {
  await new Promise(resolve => setTimeout(resolve, 100));
}
}

return results; }

// 生成测试报告 function generateReport(results) { log.header('测试报告');

const total = results.length; const successful = results.filter(r => r.success).length; const dataAvailable = results.filter(r => r.dataAvailable).length; const avgDuration = results.reduce((sum, r) => sum + r.duration, 0) / total; const maxDuration = Math.max(...results.map(r => r.duration)); const minDuration = Math.min(...results.map(r => r.duration));

console.log('统计信息:'); console.log( 总股票数: ${total}); console.log( 成功加载: ${successful}/${total} (${((successful/total)*100).toFixed(1)}%)); console.log( 数据可用: ${dataAvailable}/${total} (${((dataAvailable/total)*100).toFixed(1)}%)); console.log( 平均耗时: ${formatDuration(avgDuration)}); console.log( 最大耗时: ${formatDuration(maxDuration)}); console.log( 最小耗时: ${formatDuration(minDuration)});

//

2 个文件
检查点 1
