# Reference Layer - Harness Engineering Mechanism

**Role**: Layer 2 in 3-layer architecture (Core → Reference → SKILLs)

---

## Closed-Loop Mechanism

```
Core (Layer 1)          Reference (Layer 2)           SKILLs (Executable)
AGENTS.md ←────────→ reference/ ←────────────→ .harness/skills/
decisions.md            ↓ extraction                  (automated)
progress.md        knowledge-base/
core-facts.md
(< 300 lines)        (< 400 lines)                 (< 200 lines)
```

### Loop 1: Core ↔ Reference (Expansion/Condensation)

**Expansion** (Core > 300 lines):
1. Identify bloat in Core file
2. Create reference doc: `general/` or `project-specific/`
3. Replace Core content with pointer: `**Details**: reference/path/file.md`
4. Update this index

**Condensation** (Reference accessed > 3x):
1. Extract critical summary (< 50 lines)
2. Add to Core if critical for daily operations
3. Keep reference as detailed backup

### Loop 2: Reference → SKILL (Automation)

**Extraction Trigger** (ALL must be true):
- Reference doc accessed > 3 times in session
- Pattern is executable (has clear steps)
- Solution validated in production

**Process**:
1. Extract to `.harness/skills/<topic>/SKILL.md` (< 200 lines)
2. Register in `skills/registry.json`
3. Update reference doc with SKILL link

**Example**:
```
reference/general/async-patterns/thread-isolation-pattern.md
  → Extracted to: .harness/skills/utils/async-sdk-integration/SKILL.md
  → Registry: {"command": "/async-sdk", "path": "..."}
```

---

## Content Retention Mechanism

### Quality Gate (Before Creation)

**ALL criteria MUST be met**:
1. Debugging time > 30 minutes
2. Root cause fully analyzed
3. Solution validated in production
4. NOT found in LLM training (industry standard)

**FORBIDDEN** (reject immediately):
- Generic advice (LLM already knows)
- Copy-paste from official docs
- Undocumented hacks (no root cause)

### Size Limits (Enforced by maintenance SKILL)

| Category | Max Lines | Auto-Action |
|----------|-----------|-------------|
| `general/` | 300 | Compress if > 300 |
| `project-specific/` | 400 | Compress if > 400 |
| `knowledge-base/` | 200 | Archive if unused 90 days |
| `skills/` (in reference) | 200 | Move to `.harness/skills/` |

### Auto-Compression Trigger

**maintenance SKILL Phase 5**:
- Scan all reference docs
- Identify files > size limit
- Apply compression (keep critical, remove verbose)
- Validate links after compression

---

## Anchor Protocol (Semantic Preservation)

**Purpose**: Prevent semantic loss when knowledge migrates from Core to Reference layer.

### 1. Reverse Index Requirement

**ALL Reference documents MUST include at header**:

```markdown
# [Document Title]

**Priority**: [Critical | Standard]
**Applicable Prohibition**: AGENTS.md Rule #[X] (or Decision D0XX)
**Last Updated**: YYYY-MM-DD

[Content...]
```

**Why Required**:
- Maintains governance link when content moves out of Core
- AI can trace back to original enforcement rule
- Ensures constraint semantics preserved across layers

### 2. Priority Classification

| Priority | Behavior | Examples |
|----------|----------|----------|
| **Critical** | AI **MUST re-read** on related tasks, even if cached | Prohibition enforcement, Architecture patterns, Validation rules |
| **Standard** | AI may use cached knowledge if recent | Troubleshooting guides, Configuration examples, Best practices |

**Critical Priority Criteria** (ANY true):
- Enforces a Hard Prohibition from AGENTS.md
- Implements a PROTECTED decision
- Affects system integrity or security
- Violation causes P0/P1 production issues

### 3. Forced Re-read Mechanism

**When Priority = Critical**:

1. **Task Trigger**: AI encounters related task
   - Example: Task involves "test evidence" → Re-read VERIFICATION_EVIDENCE.md

2. **Cache Bypass**: AI MUST ignore cached content
   - Load fresh copy from file system
   - Ensure latest enforcement rules applied

3. **Validation**: maintenance SKILL Phase 4.4 checks
   - All Critical docs have valid reverse index
   - Prohibition/Decision references are current

### 4. Anchor Block Template

**Standard Format** (copy to all Reference docs):

```markdown
# [Document Title]

**Priority**: [Critical | Standard]
**Applicable Prohibition**: AGENTS.md Rule #[X] OR Decision D0XX
**Last Updated**: YYYY-MM-DD

---

## Origin & Enforcement

**Source**: [AGENTS.md Section | Decision D0XX]
**Enforcement**: [Prohibition #X | Decision D0XX]
**Why Critical**: [One-line explanation]

---

## [Content Sections]
```

### 5. Examples

#### Example 1: Critical Priority (VERIFICATION_EVIDENCE.md)

```markdown
# Verification Evidence Guide

**Priority**: Critical
**Applicable Prohibition**: AGENTS.md Rule #15
**Last Updated**: 2026-03-19

---

## Origin & Enforcement

**Source**: AGENTS.md Validation Gate section
**Enforcement**: Prohibition #15 (NO manual test evidence)
**Why Critical**: Prevents marking tasks complete without concrete proof

## Verification Evidence Template
[Content...]
```

**Behavior**: AI MUST re-read this doc on any task completion or validation task.

#### Example 2: Standard Priority (TESTING_COMMANDS.md)

```markdown
# Testing Commands Reference

**Priority**: Standard
**Applicable Prohibition**: N/A (Reference guide only)
**Last Updated**: 2026-03-19

---

## pytest Commands
[Content...]
```

**Behavior**: AI may use cached knowledge if recently accessed.

### 6. Migration Validation

**maintenance SKILL Phase 4.4** enforces:

✅ **Check 1**: All Reference docs have Priority label
✅ **Check 2**: All Reference docs have Applicable Prohibition/Decision
✅ **Check 3**: All Critical docs have Origin & Enforcement block
✅ **Check 4**: All Prohibition references are valid (exist in AGENTS.md)
✅ **Check 5**: All Decision references are valid (exist in decisions.md)

**Auto-Repair**: If missing anchor block, maintenance SKILL creates one with:
- Priority: Critical (if Prohibition mentioned in content)
- Applicable Prohibition: Extracted from content references
- Origin & Enforcement: Generated from context

---

## Category Classification

| Category | Purpose | Reusability | Size Limit |
|----------|---------|-------------|------------|
| **General** | Universal patterns | ✅ Other projects | < 300 lines |
| **Project-Specific** | Domain knowledge | ❌ This project | < 400 lines |
| **Knowledge-Base** | Troubleshooting | ❌ This project | < 200 lines |
| **Skills** | Executable workflows | ✅ Automated | < 200 lines |

---

## Document Registry Summary

**Total Registered**: 23 documents
**Critical Priority**: 9
**Standard Priority**: 14
**SKILL Extraction Candidates**: 2

### Architecture Decisions (3 documents)

| Document | Priority | Decision | Lines |
|----------|----------|----------|-------|
| [D001-D010-tech-stack.md](architecture/D001-D010-tech-stack.md) | Standard | D001-D010 | 308 |
| [D022-D027-feishu-integration.md](architecture/D022-D027-feishu-integration.md) | Standard | D022-D027 | 276 |
| [D028-harness-knowledge-restructuring.md](architecture/D028-harness-knowledge-restructuring.md) | Critical | D028 | 233 |

### Configuration (1 document)

| Document | Priority | Lines |
|----------|----------|-------|
| [env-setup.md](configuration/env-setup.md) | Standard | 194 |

### General Patterns (3 documents)

| Document | Priority | Decision | Lines | SKILL Candidate |
|----------|----------|----------|-------|-----------------|
| [thread-isolation-pattern.md](general/async-patterns/thread-isolation-pattern.md) | Critical | D027 | 210 | ✅ |
| [async-sqlalchemy-2.0.md](general/database-patterns/async-sqlalchemy-2.0.md) | Standard | D034 | 236 | - |
| [module-level-caching.md](general/sdk-integration/module-level-caching.md) | Critical | D027 | 208 | ✅ |

### Knowledge Base (7 documents)

| Document | Priority | Prohibition/Decision | Lines |
|----------|----------|----------------------|-------|
| [DATABASE_ERRORS.md](knowledge-base/DATABASE_ERRORS.md) | Critical | D034 | 103 |
| [VSCODE_PYTHON_PATH.md](knowledge-base/VSCODE_PYTHON_PATH.md) | Standard | - | 38 |
| [VERIFICATION_EVIDENCE.md](knowledge-base/VERIFICATION_EVIDENCE.md) | Critical | Prohibition #15 | 76 |
| [ANTI_FORGERY_VERIFICATION.md](knowledge-base/ANTI_FORGERY_VERIFICATION.md) | Critical | Prohibition #15 | 245 |
| [ARCHIVES_STANDARDIZATION.md](knowledge-base/ARCHIVES_STANDARDIZATION.md) | Critical | D038 | 277 |
| [REGISTRY_HEAT_TRACKING.md](knowledge-base/REGISTRY_HEAT_TRACKING.md) | Standard | - | 225 |
| [SYSTEM_LOGS_MANAGEMENT.md](knowledge-base/SYSTEM_LOGS_MANAGEMENT.md) | Critical | D038 | 361 |

### Project-Specific (8 documents)

| Document | Priority | Prohibition/Decision | Lines |
|----------|----------|----------------------|-------|
| [HARNESS_ARCHITECTURE.md](project-specific/architecture/HARNESS_ARCHITECTURE.md) | Standard | - | 216 |
| [TROUBLESHOOTING.md](project-specific/environment/TROUBLESHOOTING.md) | Standard | - | 259 |
| [bot-architecture.md](project-specific/feishu-integration/bot-architecture.md) | Standard | D022-D027 | 381 |
| [websocket-broadcast.md](project-specific/feishu-integration/websocket-broadcast.md) | Standard | D023 | 279 |
| [LANGUAGE_RULES.md](project-specific/standards/LANGUAGE_RULES.md) | Critical | Prohibition #16 | 165 |
| [TASK_EXECUTION_STANDARDS.md](project-specific/standards/TASK_EXECUTION_STANDARDS.md) | Critical | Prohibition #15 | 289 |
| [WORKFLOWS.md](project-specific/workflows/WORKFLOWS.md) | Standard | - | 377 |
| [mcp-setup/SKILL.md](project-specific/tools/mcp-setup/SKILL.md) | Standard | - | 266 |
| [tushare-api/SKILL.md](project-specific/data-sources/tushare-api/SKILL.md) | Standard | - | 288 (99KB) |

**Note**: tushare-api/SKILL.md is a large index document (99KB) containing complete Tushare API reference. Points to 229 Chinese documents in `references/` subdirectory.

### Skills (1 document)

| Document | Priority | Extracted From | Lines |
|----------|----------|----------------|-------|
| [async-sdk-integration/SKILL.md](skills/async-sdk-integration/SKILL.md) | Critical | thread-isolation-pattern.md | 266 |

---

**Version**: 5.0 (Added complete document registry)
