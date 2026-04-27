# Force Index Indicator / SKILL.md

## Immutable API Paths (Copy Exactly – Do NOT Modify)

FORCE_INDEX_SINGLE = "/api/indicators/force-index/{code_or_name}"
FORCE_INDEX_BATCH   = "/api/indicators/force-index-batch"
BASE_URL            = "http://localhost:8000"

When constructing URL:
- ALWAYS use FORCE_INDEX_SINGLE
- NEVER type from memory
- Example: BASE_URL + FORCE_INDEX_SINGLE.format(code_or_name="600519")


## Skill Name
force-index-indicator-analysis

## Description
Calculate and analyze Alexander Elder's Force Index (FI2/FI13) for stock trend strength, generate buy/sell signals, trend type identification, and strategy recommendations. All output in English.

## Trigger Phrases
- "calculate Force Index"
- "analyze Force Index"
- "evaluate stock trend strength"
- "get Force Index for [stock]"
- "Force Index analysis"

## Mandatory Read Order (Always First – Do NOT Skip)
1. Read memory/core-facts.md
2. Read decisions.md (check related decisions, e.g., data sources, logging rules)
3. Read progress.md (understand current project state)
4. Read .harness/AGENTS.md (global rules and prohibitions)

## Step-by-Step Execution (Strict Order – Never Skip Steps)

1. Confirm project context:
   - Full English-only project (vinchi-morph or stock-peg)
   - .venv activated (remind user: "Please run `source .venv/bin/activate` first if backend involved")
   - Backend API base: http://localhost:8000
   - Tests in root-level test/ directory

2. Check if related test(s) exist in test/ (e.g., test/test_force_index.py)
   - If missing → plan and CREATE failing test FIRST

3. Write minimal failing test(s):
   - Test FI2/FI13 calculation accuracy
   - Test signal strength classification
   - Test trend type detection
   - Test logging with trace_id

4. Implement or call minimal code to pass test:
   - Use existing backend endpoint if available: /api/indicators/force-index/{code_or_name}
   - If endpoint missing → implement in backend/services/force_index_calculator.py
   - Use Pydantic for request/response validation
   - Add structured logging with trace_id (core-facts.md §8)

5. Run full test suite:
   - Backend: python -m pytest test/
   - Frontend (if UI involved): npm run test

6. Format analysis output (use tables from "Signal Interpretation" and "Trend Analysis Quick Reference" in this skill)
   - Include basic info, indicator values, trend analysis, historical data (last 10 days), conclusion

7. Add structured logging:
   - Use format: [TIMESTAMP] [LEVEL] [Component] [trace_id] Message
   - Log: API call, calculation start/end, signal generated
   - Truncate large data lists (e.g., historical prices: first 5 + total count + summary)

8. If new decisions/lessons (e.g., new stock mapping, API change) → append to decisions.md

9. Update progress.md (completion status + one-line summary)

10. Write session summary to memory/session-summaries/YYYY-MM-DD.md

## Prohibitions (Hard Rules – Never Violate)

- NEVER implement calculation before writing & running corresponding test
- NEVER return raw numbers without signal interpretation and strategy suggestion
- NEVER use 'any' type in TypeScript
- NEVER commit .env or expose API keys
- NEVER log full large lists (>20 items) without truncation
- NEVER output non-English text in code, logs, or analysis results
- NEVER call API without checking server status (remind user to start uvicorn if needed)
- NEVER assume endpoint path – always use /api/indicators/force-index/

## Allowed Tools (MCP – only if needed)

- code-execution (to simulate Force Index calculation)
- browser-fetch (to reference Elder's Force Index formula if needed)
- web_search (to verify stock data if akshare fails)

## Output Format (Always Follow)
**Pre-API Check:**
Confirmed path: http://localhost:8000/api/indicators/force-index/{code_or_name}

<thinking>
Step-by-step plan, referencing .harness/memory/core-facts.md and .harness/decisions.md...
</thinking>

**Step 1:** Create failing test → [patch / code block]

**Step 2:** Implement calculation / API call → [patch or curl example]

**Step 3:** Run tests (simulate output)

**Step 4:** Format analysis result (tables) + logging

**Final:**
- Analysis complete.
- Memory updated.
- Ready for next instruction.

---

## Reference: Signal Interpretation

| Strength | Signal       | Action Suggestion     |
|----------|--------------|-----------------------|
| 7 to 10  | Strong Buy   | Hold or add position  |
| 4 to 6   | Buy          | Consider buying       |
| 1 to 3   | Bullish Bias | Observe               |
| 0        | Neutral      | Watch                 |
| -3 to -1 | Bearish Bias | Caution               |
| -6 to -4 | Sell         | Reduce position       |
| -10 to -7| Strong Sell  | Exit position         |

## Trend Analysis Quick Reference

| Trend Type     | FI2     | FI13    | Strategy Recommendation          |
|----------------|---------|---------|----------------------------------|
| Uptrend        | Positive| Positive| Hold or buy on dips              |
| Downtrend      | Negative| Negative| Reduce or avoid                  |
| Reversal       | Turning | Turning | Wait for confirmation            |
| Sideways       | Fluctuating | Stable | Stay on sidelines                |