### Role: 
    Senior Systems Architect and Meta-Prompting Specialist.

### Task: 
    Perform a comprehensive "System Health Audit" and Upgrade on the current Harness Engineering framework for the Stock PEG project.

### Mandatory Inputs:
1. Global Behavior Rules: Read .harness/AGENTS.md.
2. Architecture Log: Read .harness/decisions.md.
3. Project State: Read .harness/progress.md.

### Audit Objectives:

1. Rule Synchronization: Verify if the coding standards in AGENTS.md (e.g., async usage, logging) are consistent with the latest Feishu Bot decisions (D022-D027).

2. Harness Bloat: Identify redundant or outdated entries in progress.md that should be archived to memory/session-summaries/.

3. Protocol Expansion: Propose a new "Blueprint Protocol" for AGENTS.md that formalizes the "Prompt-then-Execute" workflow we discussed.

### Deliverables:

1. [SYSTEM_GAP_REPORT]: Identify 3 specific areas where the harness is failing to guide the AI effectively (e.g., missing error-handling standards).

2. [AGENTS_UPGRADE_SNIPPET]: Provide a block of Markdown to be added to AGENTS.md that defines the "Execution Blueprint Protocol".

3. [PROGRESS_MAINTENANCE_LOG]: A summarized update for progress.md that reflects today's focus on system stability and UI patching.

### Constraint: 
    1. Ensure all proposed rules prioritize Async First and Token Efficiency as defined in the existing harness.
    2. Move troubleshooting and environment-specific fixes to a reference layer to keep the "Global Rules" concise.
    3. Ensure the total line count of AGENTS.md remains under 400 lines to maintain model focus."
    4. Keep harness engineering relations are correct, concise and clean！
    