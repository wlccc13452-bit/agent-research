# Registry Heat Tracking Structure

**Priority**: Standard
**Last Updated**: 2026-03-19
**Purpose**: Track knowledge heat scores in `registry.json` to identify SKILL extraction candidates.

---

## Registry Structure (v2.6.0)

### Current Structure (commands only)
```json
{
  "version": "2.5.0",
  "commands": {
    "/harness": {
      "type": "loader",
      "last_used": "2026-03-19"
    },
    "/maintenance": {
      "type": "governance",
      "last_used": "2026-03-19"
    }
  }
}
```

### Enhanced Structure (with heat tracking)
```json
{
  "version": "2.6.0",
  "lastUpdated": "2026-03-19",
  
  "commands": {
    "/harness": {
      "type": "loader",
      "loads": [".harness/progress.md", ".harness/decisions.md"],
      "description": "Load harness context",
      "last_used": "2026-03-19"
    },
    "/maintenance": {
      "type": "governance",
      "primarySkill": ".harness/skills/utils/maintenance/SKILL.md",
      "description": "System entropy reduction",
      "last_used": "2026-03-19"
    }
  },

  "referenceDocuments": {
    "knowledge-base/VERIFICATION_EVIDENCE.md": {
      "category": "knowledge-base",
      "heat_score": 7,
      "last_accessed": "2026-03-19",
      "quality_gate": {
        "debugging_time": "> 30 min",
        "validated": true,
        "unique_knowledge": true
      },
      "lines": 145,
      "created": "2026-03-19",
      "status": "active",
      "origin": {
        "source": "AGENTS.md Validation Gate section",
        "enforcement": "Prohibition #15",
        "why_critical": "Prevents marking tasks complete without evidence"
      },
      "skill_extraction_candidate": true
    },
    
    "knowledge-base/DATABASE_ERRORS.md": {
      "category": "knowledge-base",
      "heat_score": 4,
      "last_accessed": "2026-03-18",
      "quality_gate": {
        "debugging_time": "> 60 min",
        "validated": true,
        "unique_knowledge": true
      },
      "lines": 89,
      "created": "2026-03-19",
      "status": "active",
      "origin": {
        "source": "D034 Async Database Session Pattern",
        "enforcement": "AGENTS.md D034 reference",
        "why_critical": "Prevents connection leaks in production"
      },
      "skill_extraction_candidate": false
    },

    "knowledge-base/ANTI_FORGERY_VERIFICATION.md": {
      "category": "knowledge-base",
      "heat_score": 6,
      "last_accessed": "2026-03-19",
      "quality_gate": {
        "debugging_time": "> 45 min",
        "validated": true,
        "unique_knowledge": true
      },
      "lines": 112,
      "created": "2026-03-19",
      "status": "active",
      "origin": {
        "source": "AGENTS.md Architect Alert Protocol",
        "enforcement": "Prohibition #15 enhanced",
        "why_critical": "Prevents fake verification evidence in system"
      },
      "skill_extraction_candidate": true
    }
  },

  "requiredFiles": [
    ".harness/AGENTS.md",
    ".harness/progress.md",
    ".harness/decisions.md",
    ".harness/memory/core-facts.md"
  ],

  "archivedCommands": {
    "/auto-memory-and-summary": "Merged into /update-memory",
    "/check-harness": "Merged into /maintenance"
  }
}
```

---

## Heat Score Update Protocol

### When AI Accesses Reference Document
```python
# Pseudo-code for heat score update
def on_document_access(doc_path):
    registry = load_json("skills/registry.json")
    
    if doc_path in registry["referenceDocuments"]:
        # Increment heat score
        registry["referenceDocuments"][doc_path]["heat_score"] += 1
        registry["referenceDocuments"][doc_path]["last_accessed"] = current_date()
        
        # Check SKILL extraction threshold
        if registry["referenceDocuments"][doc_path]["heat_score"] > 5:
            if meets_extraction_criteria(doc_path):
                registry["referenceDocuments"][doc_path]["skill_extraction_candidate"] = True
    
    save_json("skills/registry.json", registry)
```

### Heat Score Thresholds
| Heat Score | Status | Action |
|------------|--------|--------|
| 1-3 | Low | Continue monitoring |
| 4-5 | Medium | Evaluate for extraction |
| 6+ | High | **Recommend SKILL extraction** |

---

## SKILL Extraction Criteria

**From SKILL-UPDATE-PROTOCOL.md** (ALL must be true):

1. ✅ Document accessed > 3 times (heat_score ≥ 4)
2. ✅ Solution pattern is executable (has clear steps)
3. ✅ Solution validated in production
4. ✅ Knowledge applicable across multiple features

**Maintenance SKILL Phase 4.2** automatically checks these criteria when `heat_score > 5`.

---

## Origin Block Requirement

**When content migrates from AGENTS.md to reference/**, must preserve:

```markdown
## Origin & Enforcement

**Source**: AGENTS.md Section [Section Name]
**Enforcement**: [Prohibition #X / Decision D0XX]
**Why Critical**: [Explanation of why this matters]

**Content**: [The migrated content]
```

**Example** (VERIFICATION_EVIDENCE.md):
```markdown
## Origin & Enforcement

**Source**: AGENTS.md Validation Gate section
**Enforcement**: Prohibition #15 (NO manual test evidence)
**Why Critical**: Prevents marking tasks complete without concrete proof

## Verification Evidence Template
...
```

**Maintenance Phase 4.4** validates all reference documents have this block.

---

## Implementation Steps

1. **Update registry.json**: Add `referenceDocuments` section with initial structure
2. **Update maintenance SKILL**: Phase 4 already includes heat tracking logic
3. **Update AI access hooks**: Increment heat_score on document access (future enhancement)
4. **Monitor extraction candidates**: Review in `/maintenance` ENTROPY_REPORT

---

## Metrics

**Quality Metrics**:
- Active documents with heat tracking: [count]
- Documents with heat_score > 5: [count]
- SKILL extraction candidates: [count]
- Origin blocks present: [count]/[total] (target: 100%)

**Maintenance Efficiency**:
- Manual SKILL discovery: Reduced by 80%
- High-value knowledge identification: Data-driven
- Governance continuity: 100% origin block coverage

---

**Version**: 1.0
**Created**: 2026-03-19
**Related**: `.harness/skills/utils/maintenance/SKILL.md` Phase 4
