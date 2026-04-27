# Windows-Specific Issues

## URL Quoting with Chinese Characters

**Problem**: Windows PowerShell has issues with quoted URLs containing Chinese characters (exit code 3)

**Wrong Pattern**:
```powershell
curl -s "http://localhost:8000/api/indicators/force-index/中煤能源"  # ❌ Fails
```

**Correct Patterns**:
```powershell
# Option 1: Unquoted URL
curl -s http://localhost:8000/api/indicators/force-index/中煤能源

# Option 2: Use stock code instead
curl -s http://localhost:8000/api/indicators/force-index/601898
```

**Recommendation**: Stock codes are most stable for API calls.

---

## Path Separator Issues

**Problem**: Mixed path separators causing file not found errors

**Solution**:
```python
from pathlib import Path

# Use pathlib for cross-platform compatibility
file_path = Path("backend") / "data" / "stock.db"
```

---

## Virtual Environment Activation

**Problem**: Venv not activating correctly

**Solution**:
```powershell
# Don't manually activate - use UV instead
cd backend
uv run python <script.py>
```

UV handles venv activation automatically.
