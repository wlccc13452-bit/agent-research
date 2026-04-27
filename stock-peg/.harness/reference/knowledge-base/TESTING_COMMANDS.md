# Testing Commands & Python Execution

**Priority**: High
**Applicable Prohibition**: Prohibition #1 (NO `uv run` bypass)
**Last Updated**: 2026-03-21

---

## Overview

This document defines the standard approach for Python execution, testing, and debugging in the Stock PEG project.

---

## Python Execution Priority

### Priority 1: VSCode IDE Interpreter (Testing & Debugging)

**Path**: `@/d:/2026projects/stocks-research/stock-peg/backend/.venv/Scripts/python.exe`

**Use Cases**:
- VSCode Python interpreter selection
- Interactive debugging in VSCode
- Test runner execution via VSCode Test Explorer
- Code analysis and IntelliSense

**Configuration Files**:
- `.vscode/settings.json` - Python interpreter path
- `.vscode/launch.json` - Debug configurations
- `.vscode/tasks.json` - Test runner tasks

**Setup Verification**:
```powershell
# Reload VSCode after configuration
Ctrl+Shift+P → "Developer: Reload Window"
```

---

### Priority 2: UV Execution (Command Line & Scripts)

**Command**: `uv run pytest` or `uv run python <script.py>`

**Use Cases**:
- CLI test execution
- Background scripts
- Automated CI/CD pipelines
- Production deployment

**Why UV**:
- Automatic virtual environment activation
- Dependency management via `pyproject.toml`
- Consistent environment across all machines
- No manual venv activation needed

**Examples**:
```powershell
# Run all tests
cd backend && uv run pytest

# Run specific test file
uv run pytest test/api/test_stock.py

# Run with verbose output
uv run pytest -v

# Run Python script
uv run python scripts/update_data.py
```

---

### Priority 3: Direct Execution (NOT ALLOWED)

**FORBIDDEN**:
- `python <script.py>` (without UV)
- `python3 <script.py>`
- Manual venv activation: `.\.venv\Scripts\activate`

**Why Forbidden**:
- Bypasses dependency management
- Inconsistent environment
- Missing UV-specific configurations
- Risk of using wrong Python version

---

## Debugging Configuration

### VSCode Debug Setup

1. **Select Interpreter**:
   - Open Command Palette: `Ctrl+Shift+P`
   - Type: "Python: Select Interpreter"
   - Choose: `@/d:/2026projects/stocks-research/stock-peg/backend/.venv/Scripts/python.exe`

2. **Launch Configuration** (`.vscode/launch.json`):
   ```json
   {
     "version": "0.2.0",
     "configurations": [
       {
         "name": "Python: FastAPI",
         "type": "debugpy",
         "request": "launch",
         "module": "uvicorn",
         "args": [
           "main:app",
           "--reload",
           "--port", "8000"
         ],
         "jinjaTemplates": true,
         "justMyCode": false
       },
       {
         "name": "Python: Pytest",
         "type": "debugpy",
         "request": "launch",
         "module": "pytest",
         "args": ["-v", "-s"],
         "console": "integratedTerminal"
       }
     ]
   }
   ```

3. **Tasks Configuration** (`.vscode/tasks.json`):
   ```json
   {
     "version": "2.0.0",
     "tasks": [
       {
         "label": "Run Tests",
         "type": "shell",
         "command": "uv",
         "args": ["run", "pytest"],
         "group": {
           "kind": "test",
           "isDefault": true
         }
       }
     ]
   }
   ```

---

## Test Execution Patterns

### Unit Tests
```powershell
# Run all unit tests
uv run pytest tests/unit/ -v

# Run with coverage
uv run pytest --cov=backend --cov-report=html
```

### Integration Tests
```powershell
# Run integration tests
uv run pytest tests/integration/ -v

# Run specific test marker
uv run pytest -m "integration" -v
```

### API Tests
```powershell
# Test FastAPI endpoints
uv run pytest tests/api/ -v

# Test with async support
uv run pytest tests/api/ --asyncio-mode=auto
```

---

## Environment Variables

**Required Files**:
- `backend/.env` - Local environment configuration

**Critical Variables**:
```bash
# Database
DATABASE_URL=sqlite:///./data/stock_peg.db

# API Keys
TUSHARE_TOKEN=your_token
OPENAI_API_KEY=your_key

# Feishu Bot
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_secret
```

**Validation**:
```powershell
# Check if .env exists
Test-Path backend/.env

# Should return: True
```

---

## Troubleshooting

### Issue: VSCode Cannot Find Python Interpreter

**Symptom**: "No Python interpreter selected" error

**Solution**: See `VSCODE_PYTHON_PATH.md` for detailed configuration steps

---

### Issue: UV Command Not Found

**Symptom**: "uv: command not found" or "uv is not recognized"

**Solution**:
```powershell
# Install UV (if not installed)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Verify installation
uv --version
```

---

### Issue: Tests Fail with Import Errors

**Symptom**: ModuleNotFoundError when running tests

**Solution**:
```powershell
# Ensure UV environment is synced
cd backend && uv sync

# Re-run tests
uv run pytest
```

---

### Issue: Wrong Python Version

**Symptom**: Tests fail due to Python version mismatch

**Solution**:
```powershell
# Check Python version in UV environment
uv run python --version

# Should output: Python 3.13.x

# If wrong version, update .python-version file
echo "3.13" > .python-version
```

---

## Related Documents

- `AGENTS.md` - Environment Lock (global rules)
- `VSCODE_PYTHON_PATH.md` - VSCode interpreter configuration
- `ENVIRONMENT_ERRORS.md` - Common environment issues (if exists)

---

## Decision Reference

- **D008**: Python 3.13 mandatory
- **D009**: UV package manager mandatory
- **D029**: UV-only Python management in backend

---

## Quality Metrics

- **Execution Method**: UV only (100% compliance required)
- **IDE Interpreter**: Fixed path for consistency
- **Test Coverage**: Target > 80%
- **Environment Sync**: `uv sync` before every session

---

**Note**: This document consolidates all Python execution knowledge. For other environment issues, see related documents in this knowledge base.
