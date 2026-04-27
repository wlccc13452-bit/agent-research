# Architecture Decisions - 架构决策详细文档

本目录存储架构决策的详细文档，`decisions.md` 中只保留摘要。

---

## 文档命名规范

```
D0XX-D0YY-title.md    # 连续决策（主题相同）
D0XX-title.md         # 单个重大决策
```

---

## 当前文档

### D001-D010: 技术栈选择
**文件**: `D001-D010-tech-stack.md`
**包含决策**:
- D001: State Management (Zustand)
- D002: Server State Management (TanStack Query)
- D003: UI Component Library (shadcn/ui)
- D004: Backend Framework (FastAPI)
- D005: Database Choice (SQLite)
- D006: Non-Blocking Architecture
- D007: Holdings Data Source (`自持股票.md`)
- D008: Python Version (3.13)
- D009: Package Manager (UV + npm)
- D010: Build Tool (Vite)

### D011-D015: Harness系统优化
**文件**: `D011-D015-harness-optimization.md`
**包含决策**:
- D011: MCP Integration for Browser Automation
- D012: Daily Watchlist Data Storage
- D013: Daily Watchlist Organization
- D014: Daily Watchlist UI Placement
- D015: Eliminate Document Redundancy

### D020: MCP Server for Stock Data Access
**文件**: `D020-mcp-server.md`
**关键内容**: FastMCP实现、22+工具、AI Agent直接访问

### D022-D027: 飞书集成
**文件**: `D022-D027-feishu-integration.md`
**包含决策**:
- D022: Feishu Bot Integration
- D023: WebSocket Broadcast for Feishu Chat
- D024: Async SQLAlchemy Query Pattern
- D025: Feishu Timestamp String Handling
- D026: Feishu API Data Source Priority
- D027: Feishu Long Connection Thread Isolation Pattern

---

## 新增文档模板

```markdown
# D0XX: [Decision Title]

**Date**: YYYY-MM-DD
**Status**: Active / Deprecated

## Decision
[一句话决策]

## Reason
- Reason 1
- Reason 2

## Alternatives Considered
- Alternative 1 (rejected because...)
- Alternative 2 (rejected because...)

## Impact
- Impact 1
- Impact 2

## Implementation Details
[详细实现说明]

## Files Modified
- `path/to/file1.py` - Description
- `path/to/file2.ts` - Description

## Related Decisions
- D0XX: Related decision

## Lessons Learned
[经验教训]
```

---

## 维护规则

1. **新建架构决策时**：
   - 在 `decisions.md` 添加摘要
   - 在本目录创建详细文档
   - 更新本 README 的索引

2. **决策分组原则**：
   - 同一主题的连续决策合并为一个文档
   - 重大独立决策单独建文档
   - 避免文档过于碎片化

3. **文档大小控制**：
   - 单个文档不超过 500 行
   - 超过 500 行考虑拆分
