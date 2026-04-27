# harness-loader SKILL

## Description
Load the full harness engineering system: AGENTS.md + MEMORY + decisions + progress.

## Trigger phrases
- /harness
- load harness
- activate harness
- read AGENTS.md and memory

## Instructions for CodeBuddy
When user says any trigger phrase:
1. Immediately read in order (if file exists, skip if missing):
   - .harness/progress.md (If missing, default to "Initial startup")
   - .harness/decisions.md (If missing, default to "No decisions recorded")
   - .harness/memory/core-facts.md (If missing, default to "No core facts")
   - .harness/AGENTS.md (Required)
2. Confirm: "Harness loaded. Current progress: [summary from progress.md or 'Initial startup']. Ready for task."
3. Do NOT proceed to task until user gives next instruction.