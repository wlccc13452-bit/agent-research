# Harness Engineering Standardization Report

## Task Completed: Language Rules & SKILL Standardization

### 1. Language Rules Update

**Location**: `AGENTS.md` → "Language Rules" section

**Policy**:
- **Primary Language**: English (for all harness engineering documentation)
- **Chinese Allowed**: Code comments, UI text, report content, user messages, data field names
- **English Required**: SKILL.md, documentation files, variable names, API names, log messages, git commits

**Examples Added**:
```python
# ✅ Correct
def calculate_force_index(stock_code: str) -> dict:
    """Calculate Force Index indicator"""
    result = {
        'signal': '买入',  # Chinese for user-facing
        'trend': '上涨趋势'
    }
    logger.info(f"Calculating for {stock_code}")  # English log
    return result

# ❌ Incorrect
股票代码 = "000001"  # Chinese variable name
logger.info("计算指标")  # Chinese log
```

### 2. SKILL Standardization

#### ✅ python-env-management/SKILL.md
**Status**: Already compliant with template

**Sections Included**:
- Skill Name ✓
- Description ✓
- Trigger Phrases ✓
- Mandatory Read Order ✓
- Step-by-Step Execution ✓
- Prohibitions ✓
- Allowed Tools ✓
- Output Format ✓
- Quick Reference (bonus) ✓

#### ✅ force-index/SKILL.md
**Status**: Rewritten to match template

**Changes Made**:
- Added "Mandatory Read Order" section
- Added "Step-by-Step Execution" with test-first rule
- Added "Prohibitions" section
- Added "Allowed Tools" section
- Added "Output Format" with thinking block
- Added signal interpretation guide
- All content in English
- Preserved Chinese for user-facing signals (买入/卖出)

### 3. Files Modified

| File | Changes |
|------|---------|
| `AGENTS.md` | Added "Language Rules" section |
| `skills/utils/python-env-management/SKILL.md` | Verified compliant (no changes needed) |
| `skills/indicators/force-index/SKILL.md` | Complete rewrite to match template |
| `progress.md` | Updated with standardization tasks |

### 4. Compliance Checklist

#### Standard SKILL Template Requirements:
- ✅ Skill Name (clear, descriptive)
- ✅ Description (one sentence)
- ✅ Trigger Phrases (natural language list)
- ✅ Mandatory Read Order (core-facts.md first)
- ✅ Step-by-Step Execution (test-first included)
- ✅ Prohibitions (hard rules)
- ✅ Allowed Tools (MCP tools if needed)
- ✅ Output Format (thinking → steps → final)

#### Language Compliance:
- ✅ All SKILL.md files in English
- ✅ Code variable names in English
- ✅ API endpoints in English
- ✅ Log messages in English
- ✅ User-facing text can be Chinese
- ✅ UI labels can be Chinese
- ✅ Report content can be Chinese

### 5. Key Principles Enforced

**Test-First Rule**:
- NEVER implement production code before test
- Always check for existing tests
- Create failing test first (red stage)

**Structured Logging**:
- Always include trace_id
- Truncate large lists (>20 items)
- Show first 3-5 items + count + summary
- Use correct log level

**Language Separation**:
- English: Technical documentation, code, logs
- Chinese: User-facing text, UI, reports

### 6. Next Steps

For all future SKILL creation:
1. Use exact structure from `skills/_template/SKILL-TEMPLATE.md`
2. Follow test-first development approach
3. Add structured logging with trace_id
4. Maintain English-only for technical content
5. Allow Chinese for user-facing elements

### 7. Related Documents

- Template: `skills/_template/SKILL-TEMPLATE.md`
- Language Rules: `AGENTS.md` → "Language Rules"
- Progress: `progress.md`
- Session Summary: `memory/session-summaries/2026-03-11.md` (to be created)

---

**Status**: ✅ Complete
**Date**: 2026-03-11
