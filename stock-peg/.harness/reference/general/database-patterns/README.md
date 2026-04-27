# General Database Patterns

This directory contains **reusable database patterns** applicable to any project.

---

## Core Principle

**Reusable Knowledge**: Database-agnostic patterns for async operations.

---

## Documents

### Async SQLAlchemy 2.0 Query Pattern
**File**: `async-sqlalchemy-2.0.md`
**Problem**: `db.query()` doesn't work with AsyncSession
**Solution**: Use `select()` + `execute()` pattern for all async queries
**Usage**: Migrating sync to async or writing new async queries

---

## Quality Standards

- ✅ Document < 300 lines
- ✅ Code examples < 50 lines
- ✅ English only
- ✅ Debugging time > 30 minutes
- ✅ Reusable in other projects

---

## Related Categories

- `general/async-patterns/` - Async programming patterns
- `project-specific/` - Project-specific database implementations

---

## Version

- **Created**: 2026-03-16
- **Version**: 1.0
