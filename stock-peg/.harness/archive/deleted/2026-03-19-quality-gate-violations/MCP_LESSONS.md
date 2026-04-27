# MCP Tool Lessons

This file stores lessons learned from MCP (Model Context Protocol) tool usage.

---

## Playwright MCP

<!-- Lessons for Playwright browser automation tools -->

## Other MCP Tools

<!-- Lessons for other MCP integrations -->

---

## Format Template

```markdown
### [YYYY-MM-DD] MCP Lesson: [Tool Name]

**Context**: [What task was being performed]

**Call**:
```
Tool: mcp__playwright_xxx
Params: {...}
```

**Result**: [Success/Failure]

**Lesson**: [What was learned]

**Improvement**: [How to do better next time]
```

---

## Example Entry

### [2026-03-19] MCP Lesson: Playwright Screenshot

**Context**: Taking screenshot of dynamic stock chart

**Call**:
```
Tool: mcp__playwright_screenshot
Params: {"selector": "#chart-container"}
```

**Result**: Success

**Lesson**: Wait for chart to render before screenshot. Use `mcp__playwright_wait` with selector.

**Improvement**: Add explicit wait for data-loaded class on chart container.
