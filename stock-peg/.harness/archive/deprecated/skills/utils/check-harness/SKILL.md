# check-harness SKILL

## Trigger
- User runs `/check-harness`
- Weekly maintenance (recommended in AGENTS.md)
- After adding new commands or SKILLs
- When harness system seems broken or inconsistent

## Purpose
Run comprehensive health checks for Harness Engineering system integrity.

## Inputs
- Optional: `fix` (automatically fix minor issues)
- Optional: `verbose` (show detailed diagnostics)

## Action

### Step 1: Check Directory Structure
Verify all required directories and files exist:

```
Required Files:
✅ .harness/AGENTS.md
✅ .harness/progress.md
✅ .harness/decisions.md
✅ .harness/memory/core-facts.md
✅ .harness/skills/registry.json

Required Directories:
✅ .harness/memory/session-summaries/
✅ .harness/skills/utils/
✅ .codebuddy/rules/
```

**Validation**: Use `ls` or `test -f` to check existence.

### Step 2: Check Registry Integrity
Verify `.harness/skills/registry.json`:

1. **JSON Validity**: Parse JSON successfully
2. **Command Mappings**: Each command has:
   - `type` field
   - `primarySkill` field with valid path
3. **No Duplicates**: No duplicate command keys
4. **Paths Exist**: All `primarySkill` paths exist on disk
5. **Version Currency**: `version` and `lastUpdated` are recent

**Validation**:
```bash
# Check JSON syntax
cat .harness/skills/registry.json | jq .

# Check each skill path exists
# (extract paths from registry and verify with test -f)
```

### Step 3: Check Command Routing Integrity
Verify `.codebuddy/rules/` files:

1. **harness-loader.mdc exists**: `.codebuddy/rules/harness-loader.mdc`
2. **update-memory.mdc exists**: `.codebuddy/rules/update-memory.mdc`
3. **References valid**: File paths in rules point to existing files

**Validation**:
```bash
test -f .codebuddy/rules/harness-loader.mdc
test -f .codebuddy/rules/update-memory.mdc
```

### Step 4: Check SKILL File Consistency
For each registered skill in registry.json:

1. **File Exists**: SKILL.md exists at registered path
2. **Minimal Structure**: Contains required sections:
   - `## Trigger`
   - `## Action`
   - `## Validation`
   - `## Output`
3. **No Broken References**: Any file references in SKILL.md exist

**Validation**: Parse each SKILL.md and check for required sections.

### Step 5: Check Document Consistency
Verify no content overlap between documents:

1. **AGENTS.md** contains: rules, workflows, prohibitions, naming
2. **core-facts.md** contains: immutable facts, environment constraints
3. **progress.md** contains: completion status, recent work
4. **decisions.md** contains: D0XX decision records

**Manual check**: Read each file and verify scope.

### Step 6: Check Session Summary Currency
Verify recent session summaries exist:

1. **Today's date**: Check if summary exists for today
2. **Recent 7 days**: At least one summary in past 7 days
3. **Format valid**: Summaries follow template structure

**Validation**:
```bash
ls -la .harness/memory/session-summaries/ | head -10
```

## Validation

### Success Criteria
```
✅ PASS: Directory structure complete
✅ PASS: Registry JSON valid
✅ PASS: All registered skills exist
✅ PASS: Command routing files exist
✅ PASS: No broken file references
✅ PASS: Session summaries up to date
```

### Failure Handling

For each failure, report:
```
❌ FAIL: [check name]
   Expected: [what should be]
   Found: [what is missing]
   Fix: [specific action to repair]
```

If `fix=true` provided:
- Create missing directories
- Create missing files with minimal templates
- Update registry.json version/timestamp
- Report what was fixed

## Output

### Full Health Report
```
🔍 HARNESS HEALTH CHECK

📅 Check Date: 2026-03-15
📁 Project: Stock PEG

✅ PASS: Directory structure (8/8 files)
✅ PASS: Registry integrity (12 commands registered)
✅ PASS: Command routing (2/2 rules files)
✅ PASS: SKILL files (12/12 exist, 12/12 valid structure)
✅ PASS: Document boundaries (no overlap detected)
⚠️  WARN: Session summaries
   - Last summary: 2026-03-14 (1 day ago)
   - Recommendation: Create today's summary

📊 SUMMARY: 5/5 checks passed, 1 warning
✅ Harness system is HEALTHY

Next maintenance: 2026-03-22 (weekly)
```

### JSON Artifact Output
```bash
python .harness/skills/utils/check-harness/check_harness.py
python .harness/skills/utils/check-harness/check_harness.py --json-out .harness/reports/check-harness-custom.json
```

Generated artifact:
- Default path: `.harness/reports/check-harness-latest.json`
- Includes: timestamp, summary (`total/passed/failed/status`), and per-check details

### On Failure
```
🔍 HARNESS HEALTH CHECK

❌ FAIL: Directory structure
   Missing: .harness/ARCHITECTURE.md
   Fix: Create file with minimal template

❌ FAIL: Registry integrity
   Invalid JSON at line 45
   Fix: Check JSON syntax (missing comma?)

❌ FAIL: SKILL file missing
   Registered: /daily-watchlist → .harness/skills/daily-watchlist/SKILL.md
   Found: File does not exist
   Fix: Create SKILL.md or remove from registry

📊 SUMMARY: 0/5 checks passed, 3 failures
❌ Harness system is BROKEN - Fix required before proceeding

Run with 'fix=true' to auto-repair minor issues.
```

## Integration with Maintenance Cadence

This command supports the maintenance schedule in AGENTS.md:

- **Daily**: (not needed - manual updates to progress.md)
- **Weekly**: Run `/check-harness` and fix issues
- **Monthly**: Run `/check-harness` + clean stale references
- **Quarterly**: Full audit using `/check-harness` + manual review

## Auto-Repair Actions

When `fix=true` is provided:

### Auto-Created Files
- Missing directories: Create with `mkdir -p`
- Missing required files: Create with minimal template
- Registry version: Update `lastUpdated` to current date

### NOT Auto-Repaired
- Invalid JSON syntax (requires manual fix)
- Missing SKILL.md content (requires manual writing)
- Document content overlap (requires manual reorganization)

## Related Files
- `.harness/skills/registry.json` - Command registry
- `.codebuddy/rules/harness-loader.mdc` - Load command routing
- `.codebuddy/rules/update-memory.mdc` - Memory update routing
- AGENTS.md - Maintenance schedule (Section 16)
