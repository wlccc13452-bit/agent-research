# Kilocode LLM 驱动本地 APP 分析

## 一、核心机制

### 1.1 驱动模式概览

Kilocode 作为 VS Code 扩展，主要通过**工具系统**驱动本地应用：

```
┌─────────────────────────────────────────────────────────────────────┐
│                   Kilocode 驱动本地应用模式                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  模式 A: 文件系统操作                                                │
│  ┌─────────┐     ┌─────────────┐     ┌─────────────┐              │
│  │   LLM   │────▶│ File Tools  │────▶│  本地文件    │              │
│  └─────────┘     └─────────────┘     └─────────────┘              │
│  工具: read_file, write_to_file, edit_file, apply_diff             │
│                                                                     │
│  模式 B: 终端命令执行                                                │
│  ┌─────────┐     ┌─────────────┐     ┌─────────────┐              │
│  │   LLM   │────▶│ Terminal    │────▶│  Shell/CLI  │              │
│  └─────────┘     └─────────────┘     └─────────────┘              │
│  工具: execute_command                                              │
│                                                                     │
│  模式 C: 浏览器自动化                                                │
│  ┌─────────┐     ┌─────────────┐     ┌─────────────┐              │
│  │   LLM   │────▶│ Puppeteer   │────▶│   Browser   │              │
│  └─────────┘     └─────────────┘     └─────────────┘              │
│  工具: browser_action                                               │
│                                                                     │
│  模式 D: MCP 协议扩展                                                │
│  ┌─────────┐     ┌─────────────┐     ┌─────────────┐              │
│  │   LLM   │────▶│ MCP Server  │────▶│ 外部服务    │              │
│  └─────────┘     └─────────────┘     └─────────────┘              │
│  工具: use_mcp_tool, access_mcp_resource                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 与 OpenClaw 的差异

| 维度 | Kilocode | OpenClaw |
|------|----------|----------|
| **驱动目标** | 文件系统、终端、浏览器 | CLI 工具桥接本地应用 |
| **Skill 系统** | 无 Skill，直接工具调用 | Skill 模块化知识注入 |
| **扩展机制** | MCP 协议 | Skill + 插件 |
| **平台限制** | VS Code 扩展 | CLI + 多通道 |

---

## 二、文件系统操作

### 2.1 读取文件

```typescript
// src/core/tools/ReadFileTool.ts
export class ReadFileTool extends BaseTool<"read_file"> {
  async execute(params: { files: FileEntry[] }, task: Task, callbacks: ToolCallbacks) {
    for (const entry of params.files) {
      // 1. 检查文件权限
      if (task.rooIgnoreController?.validatePath(entry.path)) {
        continue // 跳过被忽略的文件
      }
      
      // 2. 读取文件内容
      const content = await fs.readFile(entry.path, "utf-8")
      
      // 3. 处理行范围
      if (entry.lineRanges) {
        const lines = content.split("\n")
        // 提取指定行范围
      }
      
      // 4. 处理图片
      if (isImageFile(entry.path)) {
        const imageData = await processImageFile(entry.path)
        // 返回 base64 图片数据
      }
    }
  }
}
```

**读取流程：**

```
用户: "读取 src/index.ts"
    │
    ▼
LLM 生成工具调用
    │
    │ <read_file>
    │   <path>src/index.ts</path>
    │ </read_file>
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ ReadFileTool.execute()                                           │
│                                                                  │
│ 1. 权限检查                                                      │
│    rooIgnoreController.validatePath("src/index.ts")             │
│                                                                  │
│ 2. 文件读取                                                      │
│    fs.readFile("src/index.ts")                                  │
│                                                                  │
│ 3. 内容处理                                                      │
│    - 添加行号                                                    │
│    - 截断过大文件                                                │
│    - 提取代码定义（可选）                                         │
│                                                                  │
│ 4. 返回结果                                                      │
│    <files><file path="src/index.ts">                            │
│    1: import ...                                                 │
│    2: ...                                                        │
│    </file></files>                                               │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 写入文件

```typescript
// src/core/tools/WriteToFileTool.ts
export class WriteToFileTool extends BaseTool<"write_to_file"> {
  async execute(params: { path: string; content: string }, task: Task, callbacks: ToolCallbacks) {
    const { path, content } = params
    
    // 1. 检查是否需要审批
    const didApprove = await callbacks.askApproval("write", { path, content })
    if (!didApprove) return
    
    // 2. 创建目录（如果不存在）
    await fs.mkdir(dirname(path), { recursive: true })
    
    // 3. 写入文件
    await fs.writeFile(path, content)
    
    // 4. 更新编辑器
    const document = await vscode.workspace.openTextDocument(path)
    await vscode.window.showTextDocument(document)
  }
}
```

### 2.3 编辑文件

```typescript
// src/core/tools/EditFileTool.ts
export class EditFileTool extends BaseTool<"edit_file"> {
  async execute(params: { path: string; diffs: Diff[] }, task: Task, callbacks: ToolCallbacks) {
    const { path, diffs } = params
    
    // 1. 读取当前内容
    const currentContent = await fs.readFile(path, "utf-8")
    
    // 2. 应用差异
    let newContent = currentContent
    for (const diff of diffs) {
      newContent = applyDiff(newContent, diff)
    }
    
    // 3. 写入更新
    await fs.writeFile(path, newContent)
  }
}
```

---

## 三、终端命令执行

### 3.1 命令执行工具

```typescript
// src/core/tools/ExecuteCommandTool.ts
export class ExecuteCommandTool extends BaseTool<"execute_command"> {
  async execute(params: { command: string; cwd?: string }, task: Task, callbacks: ToolCallbacks) {
    const { command, cwd } = params
    
    // 1. 检查 .rooignore
    const ignoredFile = task.rooIgnoreController?.validateCommand(command)
    if (ignoredFile) {
      callbacks.pushToolResult(`Command blocked: ${ignoredFile}`)
      return
    }
    
    // 2. 用户审批
    const didApprove = await callbacks.askApproval("command", command)
    if (!didApprove) return
    
    // 3. 获取终端
    const terminal = TerminalRegistry.getOrCreateTerminal()
    
    // 4. 执行命令
    const result = await terminal.executeCommand(command, {
      cwd: cwd ?? task.workspacePath,
      timeout: commandExecutionTimeout,
    })
    
    // 5. 返回结果
    callbacks.pushToolResult(result.output)
  }
}
```

### 3.2 终端集成

```typescript
// src/integrations/terminal/TerminalRegistry.ts
export class TerminalRegistry {
  private static terminals: Map<string, Terminal> = new Map()
  
  static getOrCreateTerminal(): Terminal {
    if (!this.terminals.has("default")) {
      const vscodeTerminal = vscode.window.createTerminal({
        name: "Kilo Code",
        iconPath: new vscode.ThemeIcon("terminal"),
      })
      this.terminals.set("default", new Terminal(vscodeTerminal))
    }
    return this.terminals.get("default")!
  }
}

// src/integrations/terminal/Terminal.ts
export class Terminal {
  async executeCommand(command: string, options: ExecuteOptions): Promise<ExecuteResult> {
    // 1. 使用 Shell Integration (如果可用)
    if (!options.shellIntegrationDisabled && this.shellIntegration) {
      return this.executeWithShellIntegration(command, options)
    }
    
    // 2. 回退到 PTY 模式
    return this.executeWithPty(command, options)
  }
  
  private async executeWithShellIntegration(command: string, options: ExecuteOptions) {
    const execution = this.shellIntegration.executeCommand(command)
    
    // 等待命令完成
    const exitCode = await execution.exitCode
    
    // 读取输出
    const output = await this.readOutput()
    
    return { exitCode, output }
  }
}
```

### 3.3 命令执行流程

```
用户: "运行 npm install"
    │
    ▼
LLM 生成工具调用
    │
    │ <execute_command>
    │   <command>npm install</command>
    │ </execute_command>
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ ExecuteCommandTool.execute()                                     │
│                                                                  │
│ 1. 权限检查                                                      │
│    rooIgnoreController.validateCommand("npm install")           │
│                                                                  │
│ 2. 用户审批                                                      │
│    askApproval("command", "npm install")                        │
│    → 显示对话框: "Execute command: npm install?"                │
│    → 用户确认                                                    │
│                                                                  │
│ 3. 终端获取                                                      │
│    TerminalRegistry.getOrCreateTerminal()                       │
│                                                                  │
│ 4. 命令执行                                                      │
│    terminal.executeCommand("npm install", { cwd: workspace })   │
│    → VS Code Shell Integration 或 PTY                           │
│    → 实时流式输出                                                │
│                                                                  │
│ 5. 结果收集                                                      │
│    - exitCode: 0                                                 │
│    - output: "added 123 packages..."                            │
│                                                                  │
│ 6. 返回结果                                                      │
│    <output>added 123 packages in 2.5s</output>                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 四、浏览器自动化

### 4.1 浏览器操作工具

```typescript
// src/core/tools/BrowserActionTool.ts
export class BrowserActionTool extends BaseTool<"browser_action"> {
  async execute(params: BrowserActionParams, task: Task, callbacks: ToolCallbacks) {
    const { action, url, selector, text } = params
    
    // 获取或创建浏览器实例
    const browser = await this.getBrowser()
    const page = browser.page
    
    switch (action) {
      case "launch":
        await browser.launch(url)
        break
        
      case "navigate":
        await page.goto(url)
        break
        
      case "click":
        await page.click(selector)
        break
        
      case "type":
        await page.type(selector, text)
        break
        
      case "screenshot":
        const screenshot = await page.screenshot()
        callbacks.pushToolResult({ type: "image", data: screenshot })
        break
        
      case "close":
        await browser.close()
        break
    }
  }
}
```

### 4.2 Puppeteer 集成

```typescript
// src/services/browser/Browser.ts
export class Browser {
  private browser: puppeteer.Browser | null = null
  private page: puppeteer.Page | null = null
  
  async launch(url?: string): Promise<void> {
    this.browser = await puppeteer.launch({
      headless: false,
      defaultViewport: null,
    })
    
    this.page = await this.browser.newPage()
    
    if (url) {
      await this.page.goto(url)
    }
  }
  
  async close(): Promise<void> {
    await this.browser?.close()
    this.browser = null
    this.page = null
  }
}
```

---

## 五、MCP 协议扩展

### 5.1 MCP 工具调用

```typescript
// src/core/tools/UseMcpToolTool.ts
export class UseMcpToolTool extends BaseTool<"use_mcp_tool"> {
  async execute(params: { server_name: string; tool_name: string; arguments: any }, task: Task, callbacks: ToolCallbacks) {
    const { server_name, tool_name, arguments: args } = params
    
    // 1. 获取 MCP 服务器
    const server = McpServerManager.getServer(server_name)
    if (!server) {
      callbacks.pushToolResult(`MCP server "${server_name}" not found`)
      return
    }
    
    // 2. 调用工具
    const result = await server.callTool(tool_name, args)
    
    // 3. 返回结果
    callbacks.pushToolResult(result)
  }
}
```

### 5.2 MCP 资源访问

```typescript
// src/core/tools/AccessMcpResourceTool.ts
export class AccessMcpResourceTool extends BaseTool<"access_mcp_resource"> {
  async execute(params: { server_name: string; uri: string }, task: Task, callbacks: ToolCallbacks) {
    const { server_name, uri } = params
    
    // 1. 获取 MCP 服务器
    const server = McpServerManager.getServer(server_name)
    
    // 2. 读取资源
    const resource = await server.readResource(uri)
    
    // 3. 返回内容
    callbacks.pushToolResult(resource.content)
  }
}
```

### 5.3 MCP 服务器管理

```typescript
// src/services/mcp/McpServerManager.ts
export class McpServerManager {
  private static servers: Map<string, McpServer> = new Map()
  
  static async connectServer(name: string, config: McpServerConfig): Promise<void> {
    const server = new McpServer(config)
    await server.connect()
    this.servers.set(name, server)
  }
  
  static getServer(name: string): McpServer | undefined {
    return this.servers.get(name)
  }
  
  static async listTools(serverName: string): Promise<Tool[]> {
    const server = this.servers.get(serverName)
    return server?.listTools() ?? []
  }
}
```

### 5.4 MCP 示例配置

```json
// .kilocode/mcp.json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/workspace"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "..."
      }
    }
  }
}
```

---

## 六、权限与安全

### 6.1 权限检查流程

```typescript
// 权限检查链
async function checkPermissions(operation: Operation): Promise<boolean> {
  // 1. .rooignore 检查
  if (operation.path && rooIgnoreController.validatePath(operation.path)) {
    return false
  }
  
  // 2. 用户审批
  if (!autoApprove && operation.requiresApproval) {
    const approved = await askUserApproval(operation)
    if (!approved) return false
  }
  
  return true
}
```

### 6.2 .rooignore 配置

```gitignore
# .rooignore
# 敏感文件
.env
*.key
*.pem

# 不应修改的目录
node_modules/
.git/

# 敏感命令
npm publish
git push --force
rm -rf /
```

### 6.3 安全限制

```typescript
// 命令执行限制
const commandLimitations = {
  // 超时限制
  timeout: 60000, // 60秒
  
  // 输出限制
  maxOutputChars: 100000,
  
  // 敏感命令拦截
  blockedCommands: [
    "rm -rf /",
    "sudo rm",
    // ...
  ],
}
```

---

## 七、与其他项目对比

### 7.1 驱动模式对比

| 项目 | 驱动方式 | 扩展机制 |
|------|----------|----------|
| **Kilocode** | 工具调用 | MCP 协议 |
| **OpenClaw** | CLI 工具桥接 | Skill 系统 |
| **Agentic Finance Review** | 流水线执行 | Hook 验证 |

### 7.2 能力对比

| 能力 | Kilocode | OpenClaw |
|------|----------|----------|
| 文件操作 | ✅ 直接操作 | ✅ 通过 CLI |
| 终端命令 | ✅ VS Code 集成 | ✅ Bash 工具 |
| 浏览器控制 | ✅ Puppeteer | ❌ 无 |
| 本地应用控制 | ⚠️ 通过 MCP | ✅ Skill + CLI |
| 验证机制 | ❌ 无 | ❌ 无 |

---

## 八、总结

### 8.1 Kilocode 的驱动特点

1. **VS Code 原生集成**
   - 深度集成 VS Code API
   - 使用 VS Code 终端和编辑器

2. **MCP 协议扩展**
   - 标准化的工具扩展
   - 丰富的第三方 MCP 服务器

3. **浏览器自动化**
   - Puppeteer 集成
   - 支持复杂网页操作

### 8.2 与 OpenClaw 的差异

| 维度 | Kilocode | OpenClaw |
|------|----------|----------|
| **目标** | 编程辅助 | 通用助手 |
| **Skill 系统** | ❌ 无 | ✅ 有 |
| **本地应用控制** | 间接 (MCP) | 直接 (CLI) |
| **验证机制** | ❌ 无 | ❌ 无 |

### 8.3 改进方向

1. **引入 Skill 系统**
   - 类似 OpenClaw 的模块化知识注入
   - 针对不同编程领域的专业化

2. **添加验证机制**
   - 类似 agentic-finance-review 的 Hook 系统
   - 自动验证工具执行结果

3. **增强安全模型**
   - 细粒度权限控制
   - 沙箱隔离执行
