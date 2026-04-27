# MCP Installation Guide for Multiple IDEs

**Priority**: Standard
**Last Updated**: 2026-03-18

This project may use multiple development tools: **CodeBuddy**, **Cursor**, **VSCode**, and **Trae**. Each has different MCP configuration methods.

---

## Quick Reference Table

| Tool | Config File | Location | Format |
|------|------------|----------|--------|
| **CodeBuddy** | `mcp-config.json` | `.codebuddy/mcp-config.json` | JSON |
| **Cursor** | `mcp.json` | `~/.cursor/mcp.json` | JSON |
| **VSCode** | `settings.json` | VSCode settings | JSON |
| **Trae** | Similar to Cursor | Project or user level | JSON |

---

## 1. CodeBuddy MCP Configuration

### Config Location
```
<project-root>/.codebuddy/mcp-config.json
```

### Format
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-server-playwright"],
      "env": {}
    }
  }
}
```

### After Configuration
- Save file
- Restart CodeBuddy
- MCP tools available with `mcp__` prefix

---

## 2. Cursor IDE MCP Configuration

### Method 1: User-Level Configuration

**Location**: `~/.cursor/mcp.json` (Windows: `%USERPROFILE%\.cursor\mcp.json`)

**Format**:
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-server-filesystem", "/path/to/dir"],
      "env": {}
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-server-github"],
      "env": {
        "GITHUB_TOKEN": "your-token"
      }
    }
  }
}
```

### Method 2: Project-Level Configuration

**Location**: `<project-root>/.cursor/mcp.json`

**Format**: Same as user-level

### After Configuration
1. Save file
2. Reload Cursor window (Ctrl+Shift+P → "Reload Window")
3. MCP tools available in chat

### Cursor-Specific Notes
- Cursor supports both Claude and GPT models
- MCP works with Claude models
- Check Settings → Features → Model Context Protocol

---

## 3. VSCode MCP Configuration

### Option 1: Claude for VSCode Extension

**Extension**: "Claude for VS Code" by Anthropic

**Configuration**:
1. Install extension from marketplace
2. Open Settings (Ctrl+,)
3. Search for "Claude MCP"
4. Add MCP servers in settings.json:

```json
{
  "claude.mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-server-filesystem", "${workspaceFolder}"],
      "env": {}
    }
  }
}
```

### Option 2: Continue Extension

**Extension**: "Continue" (supports multiple AI providers)

**Configuration**:
1. Install Continue extension
2. Open Continue config (Ctrl+Shift+P → "Continue: Open Config")
3. Add MCP servers to `~/.continue/config.json`:

```json
{
  "models": [...],
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-server-filesystem"],
      "env": {}
    }
  }
}
```

### Option 3: Cline Extension

**Extension**: "Cline" (autonomous coding agent)

**Configuration**:
1. Install Cline extension
2. Open Cline sidebar
3. Click settings → MCP Servers
4. Add server configuration

---

## 4. Trae MCP Configuration

*Note: Trae configuration may vary based on version*

### Expected Configuration

**Location**: `~/.trae/mcp.json` or project-level `.trae/mcp.json`

**Format**: Similar to Cursor

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-server-playwright"],
      "env": {}
    }
  }
}
```

### Verify with Trae
Check Trae documentation for exact configuration path

---

## Universal MCP Server Examples

These examples work across all tools (adjust config location):

### Filesystem MCP
```json
{
  "filesystem": {
    "command": "npx",
    "args": ["-y", "@anthropic-ai/mcp-server-filesystem", "/home/user/projects"],
    "env": {}
  }
}
```

### GitHub MCP
```json
{
  "github": {
    "command": "npx",
    "args": ["-y", "@anthropic-ai/mcp-server-github"],
    "env": {
      "GITHUB_TOKEN": "${GITHUB_TOKEN}"
    }
  }
}
```

### Brave Search MCP
```json
{
  "brave-search": {
    "command": "npx",
    "args": ["-y", "@anthropic-ai/mcp-server-brave-search"],
    "env": {
      "BRAVE_API_KEY": "${BRAVE_API_KEY}"
    }
  }
}
```

### Memory MCP
```json
{
  "memory": {
    "command": "npx",
    "args": ["-y", "@anthropic-ai/mcp-server-memory"],
    "env": {}
  }
}
```

---

## Project-Specific Setup

For this project (`stock-peg`), create configs for each tool:

### Directory Structure
```
stock-peg/
├── .codebuddy/
│   └── mcp-config.json          # CodeBuddy config
├── .cursor/
│   └── mcp.json                 # Cursor project config (optional)
├── .vscode/
│   └── settings.json            # VSCode settings with MCP
└── .trae/
    └── mcp.json                 # Trae config (if exists)
```

### Shared MCP Configuration

Create a shared template file for easy copying:

**File**: `.harness/templates/mcp-template.json`

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-server-playwright"],
      "env": {}
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-server-filesystem", "${PROJECT_ROOT}"],
      "env": {}
    }
  }
}
```

---

## Environment Variables

### Best Practice: Use Shell Environment

**Don't hardcode secrets!** Use environment variable references:

```json
{
  "github": {
    "command": "npx",
    "args": ["-y", "@anthropic-ai/mcp-server-github"],
    "env": {
      "GITHUB_TOKEN": "${GITHUB_TOKEN}"
    }
  }
}
```

Then set in your shell:

**Windows PowerShell**:
```powershell
$env:GITHUB_TOKEN = "your-token"
```

**Linux/macOS**:
```bash
export GITHUB_TOKEN="your-token"
```

**Or add to `.env` file** (if tool supports it):
```env
GITHUB_TOKEN=your-token
BRAVE_API_KEY=your-key
```

---

## Verification Methods

### CodeBuddy
- Check tools with `mcp__` prefix
- Example: `mcp__playwright_navigate`

### Cursor
- Open chat, ask "What MCP tools are available?"
- Tools should appear in autocomplete

### VSCode
- Check extension output (View → Output → Claude/Continue)
- Tools available in chat interface

### Trae
- Check settings or documentation for MCP status

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **MCP not loading** | Check JSON syntax; verify command path |
| **Command not found** | Install package: `npm install -g @anthropic-ai/mcp-server-xxx` |
| **Permission denied** | Check executable permissions |
| **Env vars not working** | Use `${VAR}` syntax; ensure variable is set |
| **Timeout** | Some MCP servers take time to start; wait 10-30s |

---

## Tool Comparison

| Feature | CodeBuddy | Cursor | VSCode+Claude |
|---------|-----------|--------|---------------|
| **Config location** | Project level | User/Project | User/Workspace |
| **Hot reload** | Restart needed | Reload window | Auto-reload |
| **MCP prefix** | `mcp__` | Varies | Varies |
| **Multi-project** | Per-project | Shared or per-project | Per-workspace |
| **Model support** | Claude | Claude/GPT | Claude |

---

## Recommended Setup for This Project

### Minimal Setup (Current)
Keep only CodeBuddy config:
```
.codebuddy/mcp-config.json
```

### Multi-Tool Setup
If using multiple IDEs:

1. **Create shared template**:
   ```
   .harness/templates/mcp-template.json
   ```

2. **Copy to each tool's config** when switching IDEs

3. **Or use symlinks** (advanced):
   ```bash
   # Linux/macOS
   ln -s ../../.harness/templates/mcp-template.json .cursor/mcp.json
   
   # Windows (Admin PowerShell)
   New-Item -ItemType SymbolicLink -Path ".cursor\mcp.json" -Target "..\..\.harness\templates\mcp-template.json"
   ```

---

## Summary

**Key Points**:
1. Different tools use different config locations
2. MCP server format is mostly consistent
3. Use environment variables for secrets
4. Verify with tool-specific methods
5. Consider shared template for multi-tool projects

**Quick Setup**:
- CodeBuddy: `.codebuddy/mcp-config.json`
- Cursor: `~/.cursor/mcp.json` or `.cursor/mcp.json`
- VSCode: Extension settings
- Trae: Check documentation
