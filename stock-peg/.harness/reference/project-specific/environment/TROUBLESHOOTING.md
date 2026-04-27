# Troubleshooting Guide

**Priority**: Standard
**Project**: Stock PEG
**Last Updated**: 2026-03-18
**Purpose**: Common issues and solutions for development environment

---

## Table of Contents

1. [AI Agent Cannot Find File](#issue-ai-agent-cannot-find-file)
2. [Memory Not Updating](#issue-memory-not-updating)
3. [Progress Tracking Unclear](#issue-progress-tracking-unclear)
4. [Documentation Inconsistent](#issue-documentation-inconsistent)
5. [Chinese Characters Encoding in Generated Code](#issue-chinese-characters-encoding-in-generated-code)
6. [ModuleNotFoundError when Running Test Scripts](#issue-modulenotfounderror-when-running-test-scripts)
7. [Windows Command Line Quoting Issues](#issue-windows-command-line-quoting-issues)
8. [Database Session Management Errors](#issue-database-session-management-errors)

---

## Issue: AI Agent Cannot Find File

**Cause**: Path reference not updated  
**Solution**: Verify path with `.harness/` prefix, check document exists

---

## Issue: Memory Not Updating

**Cause**: Auto-trigger not activated  
**Solution**: Manually run `/update-memory` or say "done"

---

## Issue: Progress Tracking Unclear

**Cause**: Not updating progress.md regularly  
**Solution**: Update progress.md at end of each session, create session summary

---

## Issue: Documentation Inconsistent

**Cause**: Multiple sources of truth  
**Solution**: Follow Document Division table in AGENTS.md

---

## Issue: Chinese Characters Encoding in Generated Code

**Cause**: Windows console uses GBK encoding by default, cannot display UTF-8 Chinese characters

**Solution**:

1. **For Python scripts**: Set `PYTHONIOENCODING=utf-8` environment variable
   ```bash
   # Windows Command Prompt
   set PYTHONIOENCODING=utf-8 && python script.py
   
   # PowerShell
   $env:PYTHONIOENCODING="utf-8"; python script.py
   ```

2. **For test scripts**: Avoid Chinese characters in print statements, use ASCII or English

3. **For file content**: Always use `encoding='utf-8'` when reading/writing files
   ```python
   with open(file_path, 'r', encoding='utf-8') as f:
       content = f.read()
   ```

---

## Issue: ModuleNotFoundError when Running Test Scripts

**Cause**: Test script executed without UV, or from wrong directory

**Solution**: Use UV to execute scripts from correct directory (NO sys.path hacks)

### Correct Execution Patterns

**✅ Option 1: From backend directory (RECOMMENDED)**:
```powershell
cd backend
uv run python ../test/temp/<task>/script.py
```

**✅ Option 2: From project root (ALTERNATIVE)**:
```powershell
uv run python test/temp/<task>/script.py
```

### Forbidden Patterns (NEVER USE)

❌ **sys.path hacks**:
```python
import sys
sys.path.insert(0, '/path/to/backend')  # ❌ FORBIDDEN
sys.path.insert(0, '../backend')        # ❌ FORBIDDEN
```

❌ **Direct Python execution**:
```bash
python test/temp/my-test/test_script.py  # ❌ FORBIDDEN
```

### Why This Works

- **UV automatically sets PYTHONPATH** to include backend directory
- **UV activates virtual environment** with correct dependencies
- **No manual path manipulation needed** when using UV correctly

### Verification

Check that script can import backend modules:
```python
# This should work WITHOUT any sys.path hacks
from config.settings import settings
from database.session import get_db

print(f"Settings loaded: {settings}")
print(f"Database path: {settings.database_url}")
```

If imports fail, verify:
1. ✅ Executing with `uv run python` (not direct Python)
2. ✅ Running from `backend/` or project root
3. ✅ Virtual environment is properly synced (`uv sync`)

---

## Issue: Windows Command Line Quoting Issues

**Cause**: Windows command prompt has issues with quoted URLs containing Chinese characters

**Solution**: Use unquoted URLs or stock codes instead of Chinese names

```bash
# ✅ Works
curl -s http://localhost:8000/api/indicators/force-index/中煤能源

# ❌ Fails (exit code 3)
curl -s "http://localhost:8000/api/indicators/force-index/中煤能源"

# ✅ Best: Use stock code
curl -s http://localhost:8000/api/indicators/force-index/601898
```

---

## Issue: Database Session Management Errors

**Cause**: Using forbidden async database session patterns that violate SQLAlchemy lifecycle

**Solution**: Follow these database session best practices:

### Pattern 1: FastAPI Route Dependencies (CORRECT)

```python
# ✅ CORRECT: Use Depends(get_db) in FastAPI routes
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_db

@app.post("/api/stocks")
async def create_stock(
    stock_data: StockCreate,
    db: AsyncSession = Depends(get_db)  # ✅ Correct
):
    # Database operations here
    await db.commit()
    return {"status": "success"}
```

### Pattern 2: Business Logic Outside Routes (CORRECT)

```python
# ✅ CORRECT: Use async with async_session_maker() for business logic
from database.session import async_session_maker

async def process_stock_data(stock_code: str):
    async with async_session_maker() as db:
        try:
            # Database operations here
            result = await db.execute(...)
            await db.commit()  # Explicit commit
            return result
        except Exception as e:
            await db.rollback()  # Explicit rollback on error
            raise
```

### Pattern 3: Forbidden Pattern (NEVER USE)

```python
# ❌ FORBIDDEN: async for db in get_db() with break
async for db in get_db():
    result = await db.execute(...)
    break  # ❌ Breaks generator chain, causes connection leaks

# ❌ FORBIDDEN: Using get_db() without FastAPI Depends
async def business_function():
    async for db in get_db():  # ❌ Wrong usage
        ...
```

### Why Forbidden?

1. **Connection Leaks**: Breaking generator chain prevents cleanup
2. **Transaction Corruption**: Unclosed transactions cause data inconsistency
3. **Session Management Errors**: Violates SQLAlchemy async session lifecycle
4. **Pool Exhaustion**: Leaked connections deplete connection pool

### Health Monitoring

```python
# Check database connection pool health
from database.session import check_db_health

health = await check_db_health()
# Returns: {
#   "status": "healthy",
#   "pool_size": 5,
#   "checked_out": 0,
#   "overflow": 0
# }
```

### Connection Pool Configuration

- **SQLite**: pool_size=5, max_overflow=10 (WAL mode enabled)
- **PostgreSQL/MySQL**: pool_size=50, max_overflow=100
- **Timeout**: 120 seconds
- **Busy Timeout** (SQLite): 60 seconds

**Reference**: See `backend/database/session.py` for implementation details

---

## Quick Reference

| Issue | Primary Solution |
|-------|------------------|
| File not found | Check `.harness/` prefix |
| Memory not updating | Run `/update-memory` |
| Chinese encoding | Set `PYTHONIOENCODING=utf-8` |
| Module not found | Use `uv run` from backend/ or project root |
| Windows quoting | Use unquoted URLs or stock codes |
| DB session errors | Use `Depends(get_db)` or `async_session_maker()` |

---

## Related Documents

- `.harness/AGENTS.md` - Global rules and workflows
- `.harness/BACKEND.md` - Backend development standards
- `backend/database/session.py` - Database session implementation
