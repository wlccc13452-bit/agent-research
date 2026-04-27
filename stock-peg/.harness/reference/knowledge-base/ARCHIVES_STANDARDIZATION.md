# Archives Directory Standardization

**Purpose**: Define the standardized structure and naming conventions for `.harness/memory/archives/`.

**Priority**: Critical
**Applicable Decision**: D038
**Last Updated**: 2026-03-19

---

## Origin & Enforcement

**Source**: D038 Maintenance SKILL for System Entropy Reduction
**Enforcement**: `/update-memory` Phase 5.1, `/maintenance` Phase 6
**Why Critical**: Inconsistent archive structure breaks automated archival and historical retrieval.

---

## Standardized Structure

### Directory Layout

```
memory/archives/
├── progress-archive-2026-Q1.md          # Progress records (Q1 2026)
├── progress-archive-2026-Q2.md          # Progress records (Q2 2026)
├── auditor-reports-archive-2026-Q1.md   # Audit reports (Q1 2026)
├── auditor-reports-archive-2026-Q2.md   # Audit reports (Q2 2026)
├── session-summaries-archive-2026-Q1.md # Session summaries (Q1 2026, optional)
├── session-summaries-archive-2026-Q2.md # Session summaries (Q2 2026, optional)
└── README.md                            # Archive index
```

### Naming Convention

**Format**: `<type>-archive-YYYY-QN.md`

| Type | Source SKILL | Content |
|------|--------------|---------|
| `progress` | `/update-memory` Phase 5.1 | Task completions, decisions, files |
| `auditor-reports` | `/maintenance` Phase 5.2 | Dispute resolution reports |
| `session-summaries` | `/update-memory` Phase 5.2 | Compressed weekly/monthly sessions |

**Quarters**:
- Q1: January - March
- Q2: April - June
- Q3: July - September
- Q4: October - December

---

## Archive Rules

### Rule 1: Files Only (No Subdirectories)

❌ **FORBIDDEN**:
```
archives/
├── tasks-2026-Q1/           # ❌ Subdirectory
│   ├── task1.md
│   └── task2.md
└── reports-2026-Q1/         # ❌ Subdirectory
    ├── report1.md
    └── report2.md
```

✅ **CORRECT**:
```
archives/
├── progress-archive-2026-Q1.md      # ✅ Single file
├── auditor-reports-archive-2026-Q1.md # ✅ Single file
└── README.md
```

**Why**: 
- Simplifies automated processing
- Consistent with `/update-memory` and `/maintenance` output
- Single file per quarter easier to navigate

### Rule 2: Size Limit < 1000 Lines

**Trigger**: Archive file > 1000 lines

**Action** (`/maintenance` Phase 6.2):
1. Extract critical content: decision titles, key milestones
2. Compress verbose details: remove full logs, keep summaries
3. Target: < 800 lines per archive file

**Example Compression**:
```markdown
# Before (1200 lines)
## 2026-01-15: Force Index Implementation
**Decision**: D028
**Summary**: Implemented Force Index indicator...
**Full Log**: [500 lines of verbose details]

# After (150 lines)
## 2026-01-15: Force Index Implementation
**Decision**: D028
**Summary**: Implemented Force Index indicator with trend analysis
**Impact**: Added FI2/FI13 trends, 40% code reduction
```

### Rule 3: README Index Required

**Template**:
```markdown
# Progress Archives

This directory stores archived project records.

## Progress Archives
- [2026 Q1](./progress-archive-2026-Q1.md) - 15 tasks
- [2026 Q2](./progress-archive-2026-Q2.md) - 12 tasks

## Auditor Reports Archives
- [2026 Q1](./auditor-reports-archive-2026-Q1.md) - 3 disputes

## Session Summaries Archives
- [2026 Q1](./session-summaries-archive-2026-Q1.md) - 20 sessions

## Purpose
- Keep active memory files manageable
- Preserve complete project history
- Enable historical analysis
```

**Update Trigger**: `/maintenance` Phase 6.3 auto-updates README.md

---

## Archive Lifecycle

### Progress Archives

```
progress.md (active, last 30 days)
    ↓ /update-memory Phase 5.1 (progress.md > 200 lines)
progress-archive-2026-Q1.md (archived)
    ↓ /maintenance Phase 6.2 (archive > 1000 lines)
progress-archive-2026-Q1.md (compressed)
```

### Auditor Reports Archives

```
auditor-reports/*.md (active, last 90 days)
    ↓ /maintenance Phase 5.2 (reports > 90 days old)
auditor-reports-archive-2026-Q1.md (archived)
    ↓ /maintenance Phase 6.2 (archive > 1000 lines)
auditor-reports-archive-2026-Q1.md (compressed)
```

### Session Summaries Archives

```
session-summaries/*.md (active, last 7 days)
    ↓ /update-memory Phase 5.2 (summaries > 7 days old)
summaries/weekly-summary-2026-W12.md (compressed)
    ↓ /update-memory Phase 5.2 (summaries > 30 days old)
summaries/monthly-summary-2026-03.md (compressed)
    ↓ Optional: Archive quarterly
session-summaries-archive-2026-Q1.md (archived)
```

---

## Migration Guide

### From Subdirectory to File

**Current State** (inconsistent):
```
archives/
└── tasks-2026-Q1/
    ├── force-index-implementation.md
    └── harness-standardization.md
```

**Target State** (standardized):
```
archives/
├── progress-archive-2026-Q1.md
└── README.md
```

**Migration Process** (`/maintenance` Phase 6.2):
1. Scan `tasks-2026-Q1/` for all markdown files
2. Extract from each file:
   - Task title, date, decision link
   - Summary, key changes, impact
3. Merge into `progress-archive-2026-Q1.md`:
   ```markdown
   # Progress Archive - 2026 Q1

   **Period**: 2026-01-01 to 2026-03-31
   **Tasks Count**: 2
   **Generated**: 2026-03-19

   ---

   ## Task 1: Force Index Implementation
   **Date**: 2026-03-15
   **Decision**: D028
   **Summary**: Implemented Force Index indicator with trend analysis
   **Files**: backend/indicators/force_index.py, frontend/components/ForceIndexChart.tsx
   **Impact**: Added FI2/FI13 trends, 40% code reduction
   ```
4. Delete `tasks-2026-Q1/` subdirectory
5. Update README.md

---

## Validation Checklist

**`/maintenance` Phase 6.1** validates:

✅ **Structure**:
- [ ] No subdirectories (only files)
- [ ] All files follow naming convention
- [ ] README.md exists

✅ **Size**:
- [ ] All archives < 1000 lines
- [ ] Oversized archives flagged for compression

✅ **Content**:
- [ ] Each archive has header with period, count, generated date
- [ ] Decision links are valid (exist in decisions.md)
- [ ] No duplicate entries

✅ **Index**:
- [ ] README.md lists all archives
- [ ] Archive counts match actual entries
- [ ] Links are valid

---

## Integration Points

### `/update-memory` SKILL
- Phase 5.1: Generate `progress-archive-YYYY-QN.md`
- Phase 5.2: Generate `session-summaries-archive-YYYY-QN.md` (optional)

### `/maintenance` SKILL
- Phase 5.2: Generate `auditor-reports-archive-YYYY-QN.md`
- Phase 6.1: Validate archives structure
- Phase 6.2: Repair inconsistent structure
- Phase 6.3: Update README.md index

---

## Quality Metrics

**Consistency**:
- Structure: 100% files (no subdirectories)
- Naming: 100% follow `<type>-archive-YYYY-QN.md`
- Index: 100% archives listed in README.md

**Size Control**:
- All archives < 1000 lines
- Average archive size: 300-600 lines

**Maintainability**:
- Automated archival (no manual intervention)
- Automated compression (oversized archives)
- Automated index update (README.md)

---

**Version**: 1.0
**Created**: 2026-03-19
**Related**: 
- `.harness/skills/utils/update-memory/SKILL.md` (Phase 5.1)
- `.harness/skills/utils/maintenance/SKILL.md` (Phase 6)
- `.harness/memory/archives/README.md` (index)
