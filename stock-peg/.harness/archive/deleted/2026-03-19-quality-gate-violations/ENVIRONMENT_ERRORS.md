# Environment Errors

## Module Not Found

**Error**: `ModuleNotFoundError: No module named 'xxx'`

**Solution**:
```powershell
# From backend directory
cd backend
uv run python <script.py>

# Or from project root
uv run python backend/<script.py>
```

**Reason**: UV automatically sets PYTHONPATH and activates virtual environment.

---

## Python Execution Errors

### sys.path Hacks (FORBIDDEN)

**Wrong Pattern**:
```python
import sys
sys.path.insert(0, '/path/to/backend')  # ❌ FORBIDDEN
sys.path.insert(0, '../backend')        # ❌ FORBIDDEN
```

**Correct Pattern**:
```powershell
# Execute via UV from correct directory
cd backend
uv run python <script.py>
```

**Why Forbidden**: sys.path hacks are fragile, platform-specific, and break with directory changes.

### Direct Python Execution (FORBIDDEN)

**Wrong Pattern**:
```powershell
python test/temp/<task>/script.py       # ❌ FORBIDDEN
..\backend\.venv\Scripts\python.exe ... # ❌ FORBIDDEN
```

**Correct Pattern**:
```powershell
cd backend
uv run python ../test/temp/<task>/script.py
```

---

## Chinese Encoding Issues

**Error**: `UnicodeEncodeError` or garbled Chinese text

**Solution**:
```powershell
$env:PYTHONIOENCODING="utf-8"
uv run python <script.py>
```

Or in script:
```python
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
```
