# SKILL Template

> **Purpose**: Define reusable workflows for common tasks. AI agents will follow this template to execute tasks systematically.

---

## Skill Name
[Short identifier, e.g., `add-api-endpoint`, `parse-custom-file`, `update-memory`]

## Description
[One sentence: what this skill does and when to use it]

## Trigger Phrases
[List natural language phrases that activate this skill]
- "add new API endpoint"
- "create route for..."
- "implement feature X"
- "/command-name"

## Mandatory Read Order (CRITICAL – Always First)
**MUST read these files before ANY action:**
1. `memory/core-facts.md` - Eternal facts & style preferences
2. `decisions.md` - Existing technical decisions (avoid duplicates)
3. `progress.md` - Current project completion status
4. `AGENTS.md` - Global rules, prohibitions, language requirements

---

## Command Runtime Preference (CRITICAL)
- Use **PowerShell-first** command design in all new SKILL files.
- If cross-platform commands are needed, place PowerShell example first and Bash as optional fallback.
- For HTTP/API examples, prefer `Invoke-RestMethod` or `Invoke-WebRequest` before `curl`.
- Ensure command examples are executable in Windows PowerShell environments by default.

---

## Step-by-Step Execution (Strict Order)

### Phase 1: Context Setup
1. Verify project type (harness engineering project has AGENTS.md)
2. Confirm environment (.venv activated, dependencies installed)
3. Identify test location (root-level `test/` directory)

### Phase 2: Test-Driven Implementation (if applicable)
4. Check if test already exists in `test/`
5. If missing → **CREATE failing test FIRST**
6. Implement minimal code to pass test
7. Run full test suite:
   - Backend: `python -m pytest test/`
   - Frontend: `npm run test`

### Phase 3: Quality Assurance
8. Add structured logging (include `trace_id`, truncate large data)
9. Verify code follows style preferences from core-facts.md
10. Check language requirements (English for docs/logs, Chinese for UI only)

### Phase 4: Memory Update (IMPORTANT)
11. **If new technical decision made** → append to `decisions.md`
12. **Update completion status** → modify `progress.md`
13. **Write session summary** → create `memory/session-summaries/YYYY-MM-DD-[topic].md`

---

## Prohibitions (Hard Rules – Never Violate)

### Code Quality
- ❌ NEVER use `any` type (TypeScript)
- ❌ NEVER omit function return type annotations (Python)
- ❌ NEVER implement production code before tests

### Security
- ❌ NEVER commit `.env` files or expose secrets
- ❌ NEVER hardcode API keys or passwords

### Logging
- ❌ NEVER log full large lists (>20 items) without truncation
- ❌ ALWAYS include `trace_id` in logs

### Language (CRITICAL)
- ❌ NEVER write non-English text in:
  - SKILL.md files
  - .harness/AGENTS.md, .harness/FRONTEND.md, .harness/BACKEND.md, .harness/ARCHITECTURE.md
  - decisions.md, progress.md
  - memory/ directory files
  - Code comments, logs, variable names
- ✅ Chinese ALLOWED in: UI text, user-facing messages, report content

### Documentation
- ❌ NEVER create .md/.doc/.txt files unless explicitly requested

---

## Allowed Tools
[List only tools needed for this skill]
- `read_file` - Read project files
- `write_to_file` - Create new files
- `replace_in_file` - Update existing files
- `execute_command` - Run shell commands
- [MCP tools if applicable]

---

## Output Format (Standard Structure)

```
<thinking>
Planning execution based on core-facts.md and decisions.md...
Identifying which steps apply to this task...
</thinking>

**Step 1:** [Action description] → [Result]

**Step 2:** [Action description] → [Result]

**Step 3:** [Action description] → [Result]

**Final:**
- ✅ Task complete
- ✅ Memory updated (decisions.md, progress.md, session summary)
- ✅ Tests passing
- Ready for next instruction
```

---

## Key System Improvements

### 1. Test-First Discipline
- ALWAYS write failing test before implementation
- Ensures code quality and prevents regression

### 2. Mandatory Context Reading
- FORCES reading core files before any action
- Prevents duplicate decisions and inconsistent patterns

### 3. Structured Memory Updates
- AUTOMATIC updates to decisions.md, progress.md, session summaries
- Maintains project knowledge continuity

### 4. Language Enforcement
- STRICT English-only for technical documentation
- Chinese only for user-facing content
- Prevents mixed-language documentation debt

### 5. Logging Standards
- REQUIRE trace_id for debugging
- TRUNCATE large data to avoid log bloat
- Proper log levels (info/debug/warning/error)

---

## Example: Minimal SKILL File

```markdown
# Force Index Analysis / SKILL.md

## Skill Name
force-index-indicator-analysis

## Description
Calculate Alexander Elder's Force Index for stock trend analysis and trading signals.

## Trigger Phrases
- "calculate Force Index"
- "analyze Force Index for [stock]"
- "/force-index"

## Mandatory Read Order
1. memory/core-facts.md
2. decisions.md
3. progress.md
4. AGENTS.md

## Step-by-Step Execution
1. Confirm backend API running (port 8000)
2. Call `/api/indicators/force-index/{code_or_name}`
3. Format results using signal interpretation tables
4. Log API call with trace_id
5. Update session summary if new findings

## Prohibitions
- NEVER call API without checking server status
- NEVER use incorrect API path (always `/api/indicators/force-index/`)

## Allowed Tools
- execute_command (PowerShell Invoke-RestMethod)
- read_file
- write_to_file

## Output Format
[Standard format above]
```

---

## Why This Template Works

1. **Forces Discipline**: Mandatory reads prevent context loss
2. **Clear Triggers**: AI knows exactly when to activate
3. **Step-by-Step Guidance**: No ambiguity in execution
4. **Quality Gates**: Built-in tests, logging, language checks
5. **Memory Continuity**: Automatic updates to project knowledge

---

## Remember

**The SKILL system is designed to:**
- Make AI behavior **predictable and reliable**
- Ensure **consistent quality** across sessions
- Maintain **project memory** automatically
- Enforce **best practices** without manual oversight

**When creating a new SKILL:**
1. Copy this template
2. Fill in relevant sections
3. Keep it concise but complete
4. Test with real scenarios
5. Iterate based on results
