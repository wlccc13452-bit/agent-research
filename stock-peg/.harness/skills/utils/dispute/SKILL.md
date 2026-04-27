# dispute SKILL

## Trigger
- User runs `/dispute`
- When facing complex logic decisions
- When multiple approaches seem viable
- When architectural decisions have significant impact

## Purpose
Force a deep adversarial debate between Builder and Auditor roles to ensure thorough analysis before implementation.

## Inputs
- `topic`: The specific issue or decision to debate
- Optional: `context`: Additional background information

## Action

### Step 1: Initialize Debate Framework
Present the dispute structure:
```
🔍 DISPUTE INITIATED

Topic: [user-provided topic]
Context: [relevant background from .harness/ files]

Debate Format:
🔧 Builder: Advocates for implementation approach
🔍 Auditor: Challenges assumptions, identifies risks
🏛️ Architect: Evaluates long-term consistency and technical debt
```

### Step 2: Builder's Proposal
**Builder Role**: Present implementation approach
- Describe the proposed solution
- Explain how it solves the immediate problem
- Highlight speed and efficiency benefits
- Cite relevant code patterns from codebase

### Step 3: Auditor's Challenge
**Auditor Role**: Skeptical analysis
- Question assumptions
- Identify edge cases and failure modes
- Check compliance with `.harness/AGENTS.md` prohibitions
- Reference previous decisions from `decisions.md` that might conflict
- Highlight potential security/performance risks

### Step 4: Architect's Evaluation
**Architect Role**: Long-term perspective
- Evaluate alignment with `core-facts.md` principles
- Assess technical debt implications
- Consider maintenance and scalability
- Compare with architectural patterns from `ARCHITECTURE.md`
- Propose compromises or alternatives

### Step 5: Synthesize Consensus
Output the agreed-upon approach:
```
🏛️ CONSENSUS REACHED

Approach: [final agreed approach]

Rationale:
- [key reason 1]
- [key reason 2]

Validation Gate:
- [specific test or check required]
- [documentation to update]

Risk Mitigation:
- [identified risk] → [mitigation strategy]
```

## Validation

### Success Criteria
- All three roles have spoken
- At least one potential issue was identified and addressed
- Clear consensus approach is documented
- Validation gate is defined

### Step 6: Generate Auditor Report
**Action**: Create audit record for traceability

**Output**: `.harness/memory/auditor-reports/YYYY-MM-DD-[topic].md`

**Template**:
```markdown
# Dispute Resolution Report - [Topic]

**Date**: YYYY-MM-DD
**Auditor**: AI Assistant
**Status**: ✅ CONSENSUS | ⚠️ ESCALATED

---

## Executive Summary
[2-3 sentences on the dispute and resolution]

---

## Debate Summary

### Builder's Proposal
[Summary of implementation approach]

### Auditor's Challenges
[List of risks, edge cases, compliance issues identified]

### Architect's Evaluation
[Long-term perspective, technical debt assessment]

---

## Consensus Reached
**Approach**: [Final agreed approach]

**Rationale**:
- [Reason 1]
- [Reason 2]

**Validation Gate**:
- [Required tests/checks]
- [Documentation to update]

**Risk Mitigation**:
- [Risk] → [Mitigation strategy]

---

## Impact
- **Affected Files**: [List of files]
- **Decision Link**: D0XX (if applicable)
- **Follow-up Actions**: [List of next steps]

---

## Conclusion
[One-line summary of outcome]
```

**Purpose**: 
- Traceability for architectural decisions
- Historical record for future reference
- Maintenance SKILL Phase 5 will archive after 90 days

### Failure Handling
If no consensus can be reached:
1. Document the disagreement
2. Present options to user with trade-offs
3. Request user decision
4. Record the decision in `decisions.md` with rationale

## Output

### Example Output
```
🔍 DISPUTE INITIATED

Topic: Should we use WebSocket or Server-Sent Events for real-time stock quotes?

🔧 Builder: "I propose using WebSocket because:
- Bidirectional communication allows client to request specific stocks
- Lower latency for high-frequency updates
- Existing WebSocket infrastructure from D006 decision
- Implementation: 2 days vs 3 days for SSE"

🔍 Auditor: "Wait, WebSocket has risks:
- Connection management complexity (reconnection, heartbeat)
- Memory leak risk if connections not properly closed
- Conflicts with D019 (Immediate Dashboard Access) - increases startup time
- Requires fallback for proxy/firewall restrictions
- Check: Do we really need bidirectional? Clients only receive quotes."

🏛️ Architect: "Consensus recommendation:
- Use Server-Sent Events (SSE) for quote streaming
- Reasoning:
  1. Unidirectional flow matches our use case (server → client only)
  2. Simpler connection management, automatic reconnection
  3. Works through firewalls/proxies without fallback
  4. Aligns with D019 (fast startup) - no WebSocket handshake overhead
  5. Can add WebSocket later if bidirectional needed (D006 preserved)

Validation Gate:
- Test SSE with 100 concurrent clients
- Verify reconnection after server restart
- Update ARCHITECTURE.md with real-time communication pattern"

✅ Decision recorded: Use SSE for stock quotes
```

## Integration with Deep-Think Workflow

This command enhances the **REFLECT** step:
- **SYNC** → **REFLECT** (can use /dispute for complex decisions) → **ACT** → **VALIDATE** → **DISTILL** → **ANCHOR**

After consensus reached:
1. Proceed to **ACT** step with agreed approach
2. After implementation, run `/validate`
3. Record decision in `decisions.md` during **DISTILL** step

## When to Use

### Use /dispute when:
- Architectural decisions affect multiple components
- Multiple implementation approaches exist with unclear trade-offs
- Decision conflicts with previous decisions (check `decisions.md`)
- High-risk changes (database schema, API contracts, security)
- User asks "should I do X or Y?"

### Do NOT use /dispute when:
- Simple bug fixes with obvious solution
- Straightforward feature additions following existing patterns
- User has already made a clear decision

## Related Files
- AGENTS.md: Multi-Agent Meta-Cognition section
- decisions.md: Check for conflicting decisions
- ARCHITECTURE.md: Reference architectural patterns
- core-facts.md: Verify alignment with project principles
