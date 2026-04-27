# General Async Patterns

This directory contains **reusable async programming patterns** applicable to any project.

---

## Core Principle

**Reusable Knowledge**: Independent of project domain, can be applied to other projects.

---

## Documents

### Thread Isolation Pattern
**File**: `thread-isolation-pattern.md`
**Problem**: SDKs that call `loop.run_until_complete()` crash in running event loops
**Solution**: Dedicated thread + independent event loop + module re-import
**Usage**: Integrating async SDKs with FastAPI/asyncio

### Event Loop Nesting
**File**: `event-loop-nesting.md` (to be created)
**Problem**: Cannot call `run_until_complete()` inside running event loop
**Solution**: Refactor to async/await or use thread isolation
**Usage**: Debugging async architecture issues

---

## Quality Standards

- ✅ Document < 300 lines
- ✅ Code examples < 50 lines
- ✅ English only
- ✅ Debugging time > 30 minutes
- ✅ Reusable in other projects

---

## Related Categories

- `general/sdk-integration/` - SDK-specific patterns
- `general/database-patterns/` - Database async patterns
- `project-specific/` - Project-specific implementations

---

## Version

- **Created**: 2026-03-16
- **Version**: 1.0
