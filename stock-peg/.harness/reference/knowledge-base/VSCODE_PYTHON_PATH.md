# VSCode Python Path Issue

**Priority**: Standard
**Applicable Prohibition**: N/A (Configuration guide only)
**Last Updated**: 2026-03-19

---

## Issue

VSCode auto-test cannot find Python interpreter:
```
@/d:/play-ground/股票研究/stock-peg/backend/.venv/Scripts/python.exe
```

**Root Cause**: Missing `.vscode/settings.json`

---

## Solution

### Files Created

- `.vscode/settings.json` - Python interpreter path
- `.vscode/launch.json` - Debug configurations
- `.vscode/tasks.json` - Test runner tasks

### Required Action

**Reload VSCode** (mandatory for config to take effect):
```
Ctrl+Shift+P → "Developer: Reload Window"
```

---

**Note**: All Python execution MUST use `uv run` (see AGENTS.md Environment Lock).
