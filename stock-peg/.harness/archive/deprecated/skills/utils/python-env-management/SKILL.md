# Python Environment Management / SKILL.md

## Skill Name
Python Environment Management

## Description
Manage Python dependencies and virtual environment for Stock PEG project using UV package manager.

## Trigger Phrases
- "add Python module"
- "install Python package"
- "manage Python environment"
- "add new dependency"
- "UV command"

## Mandatory Read Order (Always First)
Before starting ANY action:
1. Read `memory/core-facts.md`
2. Read `decisions.md` (check for related decisions)
3. Read `progress.md` (understand current state)
4. Read `AGENTS.md` (global rules)

## Step-by-Step Execution (Strict Order – Do NOT Skip)

1. Confirm project context:
   - Stock PEG is Python 3.13.3 project
   - UV is the package manager (not pip)
   - Dependencies are in `backend/pyproject.toml`
   - Lock file is `backend/uv.lock`

2. For adding new dependency:
   - Check if test is needed (most dependency additions don't require test)
   - Run: `cd backend && uv add <package-name>`
   - Verify: `uv pip show <package-name>`

3. For adding dev dependency:
   - Run: `cd backend && uv add --dev <package-name>`

4. For syncing dependencies (after git pull):
   - Run: `cd backend && uv sync`

5. Verify environment:
   - Run: `uv pip list`
   - Check pyproject.toml and uv.lock are updated

6. Commit changes:
   - `git add backend/pyproject.toml backend/uv.lock`
   - `git commit -m "Add <package-name> dependency"`

7. Update progress.md if this is a significant dependency addition

## Prohibitions (Hard Rules – Never Violate)

- NEVER use `pip install` directly (always use `uv add`)
- NEVER commit `.venv/` directory
- NEVER commit `__pycache__/` or `*.pyc`
- NEVER forget to commit `uv.lock` with `pyproject.toml`
- NEVER skip `uv sync` after `git pull`
- NEVER use Chinese in dependency names or commit messages

## Allowed Tools
- Terminal commands (uv, git)
- File editing tools (for pyproject.toml if manual edit needed)

## Output Format

<thinking>
User wants to add Python dependency. Check current environment setup.
</thinking>

**Step 1:** Add dependency using UV
```bash
cd backend
uv add <package-name>
```

**Step 2:** Verify installation
```bash
uv pip show <package-name>
```

**Step 3:** Commit changes
```bash
git add backend/pyproject.toml backend/uv.lock
git commit -m "Add <package-name> dependency"
```

**Final:**
- Dependency added successfully
- Files committed
- Ready for next instruction

## Quick Reference

| Task | Command |
|------|---------|
| Add dependency | `cd backend && uv add <pkg>` |
| Add dev dependency | `cd backend && uv add --dev <pkg>` |
| Sync dependencies | `cd backend && uv sync` |
| Run script | `cd backend && uv run python <script>` |
| List packages | `cd backend && uv pip list` |

## Project-Specific Notes

- Python version: 3.13.3
- Package manager: UV
- Dependency file: `backend/pyproject.toml`
- Lock file: `backend/uv.lock`
- Virtual env: `backend/.venv/` (auto-created, do not commit)

## Related Documents
- `.harness/AGENTS.md` - Project rules
- `BACKEND.md` - Backend development standards
