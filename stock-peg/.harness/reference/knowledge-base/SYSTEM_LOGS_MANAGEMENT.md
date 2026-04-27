# System Logs Management Mechanism

**Priority**: Critical
**Applicable Decision**: D038
**Last Updated**: 2026-03-19

---

## Origin & Enforcement

**Source**: D038 Maintenance SKILL for System Entropy Reduction
**Enforcement**: `/dispute` SKILL Step 6, `/maintenance` SKILL Phase 5
**Why Critical**: Ensures system logs don't grow unbounded. Missing mechanism = disk waste and loss of audit trail.

---

**Purpose**: Define the lifecycle management for system-generated logs in `.harness/memory/`.

---

## Overview

Three types of system logs and archives are managed by Harness Engineering:

| Directory | Purpose | Managed By | Retention |
|-----------|---------|------------|-----------|
| `auditor-reports/` | Dispute resolution records | `/dispute` SKILL | 90 days → Archive |
| `maintenance-logs/` | Maintenance session logs | `/maintenance` SKILL | 60 days → Delete |
| `archives/` | Archived logs and progress | `/update-memory` + `/maintenance` | Permanent |

---

## 1. Auditor Reports (`auditor-reports/`)

### 1.1 Generation Mechanism

**Trigger**: User runs `/dispute` command

**SKILL**: `.harness/skills/utils/dispute/SKILL.md` Step 6

**Process**:
1. User initiates dispute with a topic
2. Builder, Auditor, Architect debate
3. Consensus reached or escalated
4. **Auto-generate report**: `auditor-reports/YYYY-MM-DD-[topic].md`

**Report Template**:
```markdown
# Dispute Resolution Report - [Topic]

**Date**: YYYY-MM-DD
**Auditor**: AI Assistant
**Status**: ✅ CONSENSUS | ⚠️ ESCALATED

---

## Executive Summary
[2-3 sentences on dispute and resolution]

---

## Debate Summary

### Builder's Proposal
[Implementation approach]

### Auditor's Challenges
[Risks, edge cases, compliance issues]

### Architect's Evaluation
[Long-term perspective, technical debt]

---

## Consensus Reached
**Approach**: [Final agreed approach]
**Rationale**: [Key reasons]
**Validation Gate**: [Required tests/checks]
**Risk Mitigation**: [Risk → Strategy]

---

## Impact
- **Affected Files**: [List]
- **Decision Link**: D0XX
- **Follow-up Actions**: [Next steps]
```

### 1.2 Cleanup Mechanism

**Trigger**: `/maintenance` SKILL Phase 5.2

**Retention**: 90 days

**Process**:
1. Scan `auditor-reports/` for files > 90 days old
2. Group by quarter (Q1, Q2, Q3, Q4)
3. Merge into quarterly archive: `archives/auditor-reports-YYYY-QN.md`
4. **Keep**: Executive summary, consensus, decision links
5. **Remove**: Verbose debate details, intermediate steps
6. Delete original files

**Archive Example**:
```markdown
# Auditor Reports Archive - 2026 Q1

**Period**: 2026-01-01 to 2026-03-31
**Reports Count**: 5
**Generated**: 2026-04-01

---

## Report 1: Schema Migration Strategy
**Date**: 2026-01-15
**Status**: ✅ CONSENSUS
**Summary**: Decided to use gradual migration over big-bang rewrite
**Decision**: D028
**Impact**: Reduced deployment risk by 70%

---

## Report 2: API Versioning Approach
**Date**: 2026-02-20
**Status**: ✅ CONSENSUS
**Summary**: Adopted URL-based versioning (/v1/, /v2/)
**Decision**: D030
**Impact**: Clear upgrade path for clients
...
```

---

## 2. Maintenance Logs (`maintenance-logs/`)

### 2.1 Generation Mechanism

**Trigger**: User runs `/maintenance` command (or auto-trigger after 10 tasks)

**SKILL**: `.harness/skills/utils/maintenance/SKILL.md` Phase 5.1

**Process**:
1. User runs `/maintenance` (or auto-trigger)
2. Execute Phases 1-4 (integrity audit, standardization, layering, usage tracking)
3. **Auto-generate log**: `maintenance-logs/YYYY-MM-DD-maintenance-log.md`

**Log Template**:
```markdown
# Maintenance Log - YYYY-MM-DD

**Trigger**: `/maintenance` (manual/auto)
**Duration**: X minutes
**Status**: ✅ Complete | ⚠️ Issues Found

---

## [SYSTEM_ENTROPY_REPORT]
[Copy from Phase 1-4 output]

---

## [LEAN_UPDATE]
[Summary of AGENTS.md changes]

---

## [PRUNING_PROPOSAL]
[SKILLs identified for archival]

---

## [HEAT_MAP]
[Top 10 high-value reference documents]

---

## Actions Taken
- [List of specific fixes applied]
- [Files updated]
- [Archive operations performed]

---

## Next Maintenance
- **Recommended**: YYYY-MM-DD (after 10 tasks or 7 days)
- **Critical Issues**: [Issues requiring immediate attention]
```

### 2.2 Cleanup Mechanism

**Trigger**: `/maintenance` SKILL Phase 5.2

**Retention**: 60 days

**Process**:
1. Scan `maintenance-logs/` for files > 60 days old
2. **Delete immediately** (low historical value)
3. Keep last 10 log files for recent reference

**Why Delete Instead of Archive?**:
- Maintenance logs contain operational details, not architectural decisions
- Low historical value after 60 days
- Recent 10 logs sufficient for troubleshooting patterns

---

## 3. Archives Directory (`archives/`)

### 3.1 Structure

**Standardized Layout**:
```
memory/archives/
├── progress-archive-2026-Q1.md          # From /update-memory
├── auditor-reports-archive-2026-Q1.md   # From /maintenance
├── session-summaries-archive-2026-Q1.md # From /update-memory (optional)
└── README.md                            # Index
```

**Naming Convention**: `<type>-archive-YYYY-QN.md`

### 3.2 Management Mechanism

**Generated By**:
- `/update-memory` Phase 5.1: `progress-archive-YYYY-QN.md`
- `/maintenance` Phase 5.2: `auditor-reports-archive-YYYY-QN.md`

**Validated By**:
- `/maintenance` Phase 6: Archives integrity validation
  - Phase 6.1: Structure validation (files only, no subdirectories)
  - Phase 6.2: Repair inconsistent structure
  - Phase 6.3: Update README.md index

**Size Control**:
- Trigger: Archive file > 1000 lines
- Action: Compress to < 800 lines (keep summaries, remove verbose details)

**See**: `reference/knowledge-base/ARCHIVES_STANDARDIZATION.md` for complete rules.

---

## 4. Complete Lifecycle Flow

### Auditor Reports Lifecycle
```
User runs /dispute
    ↓
[Step 6] Generate report
    ↓
auditor-reports/YYYY-MM-DD-topic.md (Day 0)
    ↓
[90 days pass]
    ↓
/maintenance Phase 5.2
    ↓
archives/auditor-reports-YYYY-QN.md (archived)
```

### Maintenance Logs Lifecycle
```
User runs /maintenance
    ↓
[Phase 5.1] Generate log
    ↓
maintenance-logs/YYYY-MM-DD-maintenance-log.md (Day 0)
    ↓
[60 days pass]
    ↓
/maintenance Phase 5.2
    ↓
[DELETED] (low value)
```

---

## 5. Management Matrix

| Directory | Generated By | Generated When | Cleaned By | Cleaned When | Retention |
|-----------|--------------|----------------|------------|--------------|-----------|
| `auditor-reports/` | `/dispute` SKILL Step 6 | Dispute complete | `/maintenance` Phase 5.2 | Every `/maintenance` run | 90 days |
| `maintenance-logs/` | `/maintenance` Phase 5.1 | Maintenance start | `/maintenance` Phase 5.2 | Every `/maintenance` run | 60 days |

---

## 6. Quality Metrics

**Auditor Reports**:
- Generation: ✅ Automatic on every `/dispute`
- Coverage: 100% of disputes documented
- Archive Quality: Executive summary + consensus preserved
- Traceability: Decision links maintained

**Maintenance Logs**:
- Generation: ✅ Automatic on every `/maintenance`
- Coverage: 100% of maintenance sessions logged
- Cleanup Efficiency: Files > 60 days deleted
- Disk Space: Controlled growth (last 10 files only)

---

## 7. Edge Cases

### Case 1: Multiple Disputes Same Day
- Append timestamp: `YYYY-MM-DD-HHMM-topic.md`
- Or append to existing daily report with separator

### Case 2: No Maintenance Runs for 90 Days
- Auditor reports accumulate beyond retention
- Next `/maintenance` will clean all expired files
- No data loss (all archived before deletion)

### Case 3: Manual Report Creation
- Follow template format
- Include date in filename
- Will be processed by `/maintenance` normally

---

## 8. Integration Points

**`/dispute` SKILL**:
- Step 6: Generate auditor report (NEW)
- Links to: `decisions.md` (Decision Link field)

**`/maintenance` SKILL**:
- Phase 5.1: Generate maintenance log (NEW)
- Phase 5.2: Clean and archive logs (EXISTING, enhanced)
- Links to: `archives/` (quarterly archives)

**`/update-memory` SKILL**:
- No involvement (system logs, not project memory)

---

## 9. Validation

**Automatic Checks** (by `/maintenance` Phase 5.2):
- ✅ All auditor reports < 90 days old are in `auditor-reports/`
- ✅ All maintenance logs < 60 days old are in `maintenance-logs/`
- ✅ Quarterly archives exist for expired reports
- ✅ Last 10 maintenance logs retained

**Manual Verification**:
```bash
# Check auditor reports age
ls -la .harness/memory/auditor-reports/

# Check maintenance logs age
ls -la .harness/memory/maintenance-logs/

# Check archives
ls -la .harness/memory/archives/
```

---

**Version**: 1.0
**Created**: 2026-03-19
**Related**: 
- `.harness/skills/utils/dispute/SKILL.md` (Step 6)
- `.harness/skills/utils/maintenance/SKILL.md` (Phase 5.1, 5.2)
