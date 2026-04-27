# Reference Quality Standards

**Core Principle**: `reference/` contains ONLY validated, non-obvious knowledge.

---

## Quality Gate (Before Creation)

**ALL criteria MUST be met**:
1. **Debugging Time**: > 30 minutes
2. **Root Cause**: Fully analyzed (not surface symptoms)
3. **Solution**: Validated in production
4. **Uniqueness**: NOT found in LLM training (industry standard)
5. **Reusability**: Applicable to > 1 scenario

**FORBIDDEN** (reject immediately):
- Generic advice (LLM already knows)
- Copy-paste from official docs
- Undocumented hacks (no root cause)
- Temporary workarounds

---

## Content Retention Mechanism

### Size Limits (Enforced by maintenance SKILL Phase 5)

| Category | Max Lines | Auto-Action |
|----------|-----------|-------------|
| `general/` | 300 | Compress if > 300 |
| `project-specific/` | 400 | Compress if > 400 |
| `knowledge-base/` | 200 | Archive if unused 90 days |
| `skills/` (in reference) | 200 | Move to `.harness/skills/` |

### Auto-Compression Algorithm

**Trigger**: File exceeds size limit

**Process**:
1. Identify non-critical sections (verbose examples, duplicate explanations)
2. Remove verbose content, keep critical insight
3. Replace with pointer: `**Details**: reference/...`
4. Validate all links still work

---

## Category Classification

### General (Universal Knowledge)

**Characteristics**:
- ✅ Reusable in other projects
- ✅ Technology-agnostic patterns
- ✅ Independent of project-specific data

**Examples**:
- SDK module-level caching trap
- Async event loop nesting solution
- Database session anti-patterns

**Location**: `reference/general/<category>/<topic>.md`

---

### Project-Specific (Domain Knowledge)

**Characteristics**:
- ✅ Tied to project requirements
- ✅ Domain-specific knowledge
- ⚠️ May contain sensitive data references

**Examples**:
- Feishu bot integration architecture
- Stock data API design
- Technical indicator calculations

**Location**: `reference/project-specific/<domain>/<feature>.md`

---

### Skills (Executable Knowledge)

**Characteristics**:
- ✅ Extracted from reference documents
- ✅ Executable workflow / checklist
- ✅ Registered in `skills/registry.json`

**Extraction Trigger** (ALL must be true):
1. Accessed > 3 times in session
2. Pattern is executable
3. Solution validated

**Location**: `reference/skills/<topic>/SKILL.md` → `.harness/skills/`

---

**Version**: 2.0 (Quality gate + Retention mechanism only)
