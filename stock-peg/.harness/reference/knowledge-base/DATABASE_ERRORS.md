# Database Errors

**Priority**: Critical
**Applicable Decision**: D034
**Last Updated**: 2026-03-19

---

## Origin & Enforcement

**Source**: D034 Async Database Session Pattern
**Enforcement**: AGENTS.md Prohibition #9 (NO async for session in db in routes)
**Why Critical**: Wrong session patterns cause connection leaks, transaction corruption, and pool exhaustion in production.

---

## Session Management in FastAPI

### Wrong Pattern (FORBIDDEN)

```python
# ❌ FORBIDDEN - Breaks generator chain
async for db in get_db():
    # ... use db
    break  # Causes connection leak
```

**Problems**:
- Connection leaks
- Transaction corruption
- Pool exhaustion

### Correct Patterns

**Pattern 1: Route Dependencies (Recommended)**
```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

@router.get("/api/stocks")
async def get_stocks(db: AsyncSession = Depends(get_db)):
    # FastAPI manages session automatically
    result = await db.execute(query)
    return result.scalars().all()
```

**Pattern 2: Business Logic with explicit session**
```python
from database.session import async_session_maker

async def update_stock_data():
    async with async_session_maker() as db:
        try:
            await db.execute(update_stmt)
            await db.commit()
        except Exception:
            await db.rollback()
            raise
```

---

## Connection Pool Exhaustion

**Symptoms**:
- Timeout errors
- "Too many connections"
- Slow response times

**Diagnosis**:
```python
# Check pool metrics
GET /health
# Returns: pool_size, checked_out, overflow, checked_in
```

**Solution**:
- Alert threshold: > 80% pool utilization
- Check for unclosed sessions (Pattern 1 or 2 above)
- Review connection pool config:
  ```python
  # SQLite config
  pool_size = 5
  max_overflow = 10
  ```

---

## Async Session Context Errors

**Error**: `MissingGreenletError` or `greenlet_spawn has not been called`

**Cause**: Using sync methods on async session

**Solution**:
```python
# Wrong
result = db.execute(query)  # ❌ Sync call

# Correct
result = await db.execute(query)  # ✅ Async call
```
