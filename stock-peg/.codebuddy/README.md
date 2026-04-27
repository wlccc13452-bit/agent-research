# CodeBuddy Configuration

## MCP Servers

### Playwright MCP
Browser automation for web scraping and testing.

**Available Tools:**
- `mcp__playwright_navigate` - Navigate to URL
- `mcp__playwright_screenshot` - Take screenshot
- `mcp__playwright_click` - Click element
- `mcp__playwright_fill` - Fill input field
- `mcp__playwright_evaluate` - Execute JavaScript
- `mcp__playwright_close` - Close browser

**Setup:**
1. Ensure Node.js is installed
2. Restart CodeBuddy after config changes
3. MCP tools will appear with `mcp__` prefix

## Files

| File | Purpose |
|------|---------|
| `mcp-config.json` | MCP server configuration |
| `teams/` | Team mode data (auto-generated) |
| `memory/` | Persistent memory (auto-generated) |
