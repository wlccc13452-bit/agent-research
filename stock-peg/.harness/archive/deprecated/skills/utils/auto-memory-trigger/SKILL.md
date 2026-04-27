# auto-memory-trigger SKILL

## Purpose
Detect when memory update is needed and trigger the memory-update-protocol.

## When to Activate
- User says "done" / "finish" / "session end"
- User invokes `/update-memory`
- Major task completion detected

## Actions

### Step 1: Check Update Need
Ask: "Did we make any new decisions, discover important patterns, fix recurring bugs, or learn something worth remembering?"

### Step 2: Trigger Update if Needed
If YES → Invoke **memory-update-protocol SKILL** (which includes a Step 0 Robustness Check).

**Note**: Do not worry if `progress.md` or `decisions.md` are missing; the protocol will automatically create them with default templates before proceeding.

If NO → Skip update, reply: "No significant changes detected. Memory not updated."

## Output Format
```
[Memory Update Check]
- New decisions? [Yes/No]
- Important patterns? [Yes/No]
- Recurring bugs fixed? [Yes/No]
- Learnings? [Yes/No]

→ Result: [Trigger memory-update-protocol / Skip]
```