# Async SQLAlchemy 2.0 Query Pattern

**Priority**: Standard
**Category**: General / Database Patterns
**Last Updated**: 2026-03-18
**Reusable**: Yes (applicable to any project)
**Decision**: D024

---

## TL;DR (Core Insight)

**Problem**: Using `db.query()` with AsyncSession causes "AsyncSession has no attribute 'query'" error.
**Discovery**: `db.query()` is SQLAlchemy 1.x sync syntax, incompatible with AsyncSession.
**Solution**: Use `select()` + `execute()` pattern for all async queries.

---

## Problem Pattern

### When It Occurs
- Project uses AsyncSession (SQLAlchemy async)
- Code uses `db.query(Model)` syntax (sync pattern)
- Common when migrating from sync to async

### Symptoms
```python
# Error scenario
async def get_items(db: AsyncSession):
    items = db.query(Item).all()  # ❌ AttributeError: 'AsyncSession' object has no attribute 'query'
```

### Identification
1. Project uses `AsyncSession` from `sqlalchemy.ext.asyncio`
2. Code contains `db.query()` or `session.query()`
3. Error: "has no attribute 'query'"

---

## Root Cause Analysis

### SQLAlchemy Version Differences

**SQLAlchemy 1.x (Sync)**:
```python
from sqlalchemy.orm import Session

def get_items(db: Session):
    items = db.query(Item).all()  # ✅ Works with sync Session
    return items
```

**SQLAlchemy 2.0 (Async)**:
```python
from sqlalchemy.ext.asyncio import AsyncSession

async def get_items(db: AsyncSession):
    items = db.query(Item).all()  # ❌ AsyncSession has no .query()
    return items
```

### Why AsyncSession Doesn't Have .query()

1. `.query()` returns immediately (sync behavior)
2. Async code requires explicit `await`
3. SQLAlchemy 2.0 uses `select()` + `execute()` pattern
4. Pattern makes async behavior explicit

---

## Solution Pattern

### Basic Query

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import Item

async def get_items(db: AsyncSession) -> list[Item]:
    # ✅ Correct async pattern
    result = await db.execute(select(Item))
    items = result.scalars().all()
    return items
```

### Query with Filter

```python
async def get_item_by_id(db: AsyncSession, item_id: int) -> Item | None:
    # ✅ Filter pattern
    result = await db.execute(
        select(Item).where(Item.id == item_id)
    )
    item = result.scalar_one_or_none()
    return item
```

### Query with Order and Limit

```python
async def get_recent_items(db: AsyncSession, limit: int = 10) -> list[Item]:
    # ✅ Order + limit pattern
    result = await db.execute(
        select(Item)
        .order_by(Item.created_at.desc())
        .limit(limit)
    )
    items = result.scalars().all()
    return items
```

### Count Query

```python
from sqlalchemy import func

async def count_items(db: AsyncSession) -> int:
    # ✅ Count pattern
    total = await db.scalar(
        select(func.count()).select_from(Item)
    )
    return total or 0
```

### Query with Join

```python
async def get_items_with_category(db: AsyncSession) -> list[dict]:
    # ✅ Join pattern
    result = await db.execute(
        select(Item, Category)
        .join(Category, Item.category_id == Category.id)
    )
    rows = result.all()
    return [{"item": row[0], "category": row[1]} for row in rows]
```

---

## Migration Checklist

**From Sync to Async**:

- [ ] Replace `Session` with `AsyncSession`
- [ ] Replace `db.query(Model)` with `await db.execute(select(Model))`
- [ ] Replace `.all()` with `result.scalars().all()`
- [ ] Replace `.first()` with `result.scalar_one_or_none()`
- [ ] Replace `.count()` with `await db.scalar(select(func.count()))`
- [ ] Add `async` to function definition
- [ ] Add `await` to all db operations

---

## Prohibition

### ❌ NEVER Use These Patterns with AsyncSession

```python
# ❌ WRONG - Sync pattern with async session
items = db.query(Item).all()

# ❌ WRONG - No await
result = db.execute(select(Item))

# ❌ WRONG - Using .query() in async context
async def get_items(db: AsyncSession):
    return db.query(Item).all()  # ❌

# ❌ WRONG - Using session generator in FastAPI route
async def get_items(db: AsyncSession = Depends(get_db)):
    async for session in db:  # ❌ Misunderstanding Depends
        items = await session.execute(select(Item))
```

### ✅ ALWAYS Use These Patterns

```python
# ✅ CORRECT - Async pattern
async def get_items(db: AsyncSession):
    result = await db.execute(select(Item))
    return result.scalars().all()

# ✅ CORRECT - With Depends
async def get_items(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Item))
    return result.scalars().all()
```

---

## Lessons Learned

### 1. Explicit is Better Than Implicit
**Pattern**: Async requires explicit `await` for all operations
**Rule**: If it touches database, it needs `await`

### 2. Check Session Type Early
**Pattern**: Error messages can be confusing
**Rule**: Verify `AsyncSession` type hint in function signature

### 3. Use Type Checking
**Pattern**: mypy catches sync patterns in async context
**Rule**: Run `mypy` before testing

### 4. Common Migration Mistake
**Pattern**: Forgetting to change `.first()` → `.scalar_one_or_none()`
**Rule**: Update all result access patterns

---

## SKILL Integration

**Extracted SKILL**: `skills/utils/async-sqlalchemy-2.0/SKILL.md` (to be created)
**Usage**: Use SKILL when migrating sync to async or writing new async queries

---

## Related Resources

**Project-Specific Example**:
- `project-specific/feishu-integration/websocket-broadcast.md` - Used in chat history queries

**Architecture Decision**:
- D024: Async SQLAlchemy Query Pattern

**Documentation**:
- SQLAlchemy 2.0 Async Documentation: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html

---

## Version

- **Created**: 2026-03-16
- **Debugging Time**: 1 hour
- **Version**: 1.0
- **Reusable**: Yes (applicable to any project using AsyncSession)
