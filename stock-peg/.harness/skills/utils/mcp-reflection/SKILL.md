# MCP Reflection Skill

## Description
After every MCP tool call, reflect on usage and record lessons to memory.

## Trigger Phrases
- "reflect on mcp"
- "mcp review"
- "after mcp call"

## When to Use
- After any significant MCP tool execution
- When MCP call fails or returns unexpected results
- When learning new MCP tool capabilities
- After complex browser automation sequences

## Steps

### 1. Summarize MCP Call
After receiving MCP tool result, document:
- **Tool Called**: Which MCP tool was invoked (e.g., `mcp__playwright_navigate`)
- **Parameters**: Key parameters passed
- **Result**: What was returned
- **Status**: Success / Failure / Partial

### 2. Analyze Failure (if applicable)
If the MCP call failed:
- Identify root cause (wrong parameter, timeout, element not found, etc.)
- Note error message
- Document what was attempted before the failure

### 3. Record Lesson
Append lesson to appropriate memory file:

**For general MCP lessons** → `.harness/memory/mcp-lessons.md`
**For technical decisions** → `.harness/decisions.md`

Format:
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

### 4. Suggest Improvements
Based on the lesson, suggest:
- Better parameter choices
- Alternative tools to consider
- Error handling strategies
- Performance optimizations

### 5. Output Confirmation
After recording, output:
> "MCP reflection complete. Lesson recorded to [file path]."

## Example Usage

### Example 1: Successful Navigation
```
**Tool Called**: mcp__playwright_navigate
**Parameters**: url="https://finance.yahoo.com/quote/600519.SS"
**Result**: Successfully navigated, page loaded
**Status**: Success

**Lesson**: Yahoo Finance pages may require wait time for dynamic content. Consider using `mcp__playwright_wait` before scraping.

**Output**: "MCP reflection complete. Lesson recorded to .harness/memory/mcp-lessons.md."
```

### Example 2: Failed Element Selection
```
**Tool Called**: mcp__playwright_click
**Parameters**: selector="button.submit"
**Result**: Error: Element not found
**Status**: Failure

**Analysis**: 
- Cause: Selector was too generic
- Page had multiple "submit" buttons
- Dynamic content not fully loaded

**Lesson**: Use specific selectors with data attributes. Wait for element visibility before clicking.

**Improvement**: 
- Use `data-testid` or unique IDs
- Add `mcp__playwright_wait` with selector
- Verify element exists before interaction

**Output**: "MCP reflection complete. Lesson recorded to .harness/memory/mcp-lessons.md."
```

## Memory File Structure

### .harness/memory/mcp-lessons.md
```markdown
# MCP Tool Lessons

## Playwright MCP

### [2026-03-15] Lesson: Yahoo Finance Navigation
...

### [2026-03-14] Lesson: Screenshot Timing
...

## Other MCP Tools

### [2026-03-13] Lesson: File System MCP
...
```

## Best Practices

1. **Always Reflect After Failures**: Every failed MCP call should generate a lesson
2. **Include Context**: Document what task triggered the MCP call
3. **Be Specific**: Include actual parameter values and error messages
4. **Suggest Actionable Improvements**: Don't just note the problem, suggest solutions
5. **Cross-Reference**: If lesson relates to a decision, also add to `decisions.md`

## Integration with Other Skills

- Use with `browser-automation` skill for web scraping tasks
- Use with `playwright-cli` skill for testing workflows
- Combine with `memory-update-protocol` for session summaries

## Related Documents

- `.harness/AGENTS.md` - MCP tool overview (Section: Allowed Tools / MCP)
- `.harness/memory/mcp-lessons.md` - Storage for MCP lessons
- `.harness/decisions.md` - Technical decisions involving MCP usage
