# SKILL Update Protocol

**Purpose**: Extract reusable knowledge from `reference/` into executable SKILLs.

---

## Extraction Trigger (ALL must be true)

1. Reference document accessed > 3 times in session
2. Solution pattern is executable (has clear steps)
3. Solution validated in production
4. Knowledge applicable across multiple features

---

## Extraction Process

### Step 1: Identify Candidate

**Indicators**:
- Document contains step-by-step solution
- Pattern reused > 2 times
- Problem-solving workflow well-defined
- Document size < 300 lines

### Step 2: Extract SKILL

**Location**: `reference/skills/<topic>/SKILL.md`

**Requirements**:
- Size: < 200 lines
- Structure: Trigger → Purpose → Steps → Validation
- Format: Markdown with code snippets

### Step 3: Register SKILL

**Actions**:
1. Copy to `.harness/skills/utils/<topic>/SKILL.md`
2. Update `skills/registry.json`:
   ```json
   {
     "command": "/<topic>",
     "path": ".harness/skills/utils/<topic>/SKILL.md",
     "description": "...",
     "trigger": "..."
   }
   ```
3. Update `AGENTS.md` Skills Directory

### Step 4: Update Reference Document

**Add link to original reference document**:
```markdown
## SKILL Integration
**Extracted SKILL**: `skills/utils/<topic>/SKILL.md`
**Usage**: Use SKILL for guided implementation
```

---

## SKILL Lifecycle

```
Creation → Active → Deprecated → Archived

1. Creation: Extracted from reference → Registered in .harness/skills/
2. Active: Used by AI Agent → Updated based on feedback
3. Deprecated: Marked as deprecated → Replacement referenced
4. Archived: Moved to skills/archives/ → Historical reference
```

---

## Maintenance Rules

### When Creating SKILL
- Verify no duplicate exists
- Use naming: `<topic>-<action>`
- Keep < 200 lines
- Validate against new scenarios

### When Deprecating SKILL
- Mark as deprecated (don't delete)
- Reference replacement SKILL
- Update registry.json and AGENTS.md

### When Updating Reference Document
- Check if SKILL exists
- Update SKILL if solution changes
- Validate SKILL still works

---

**Version**: 2.0 (Extraction mechanism only)
