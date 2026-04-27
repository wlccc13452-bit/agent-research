# run-shell-command / SKILL.md

## Skill Name
run-shell-command

## Description
Execute any safe shell command in the project directory and return processed output for LLM.

## Trigger Phrases
- "run command ..."
- "execute shell ..."
- "try this in terminal: ..."

## Mandatory Read Order
1. memory/core-facts.md
2. decisions.md
3. progress.md
4. AGENTS.md

## Step-by-Step Execution
1. Read core-facts.md for environment info (.venv, test dir, etc.)
2. Confirm command is safe (no rm -rf, no pip install without uv, etc.)
3. Execute command in project root
4. Process output:
   - Truncate long output (>1000 chars): show first 300 + "..." + last 300 + total lines
   - If stderr non-empty → wrap it as natural language hint
   - Always add [exit_code] [duration_ms]
5. Return to agent with trace_id logging

## Prohibitions
- NEVER run destructive commands (rm, mv, git push without confirmation)
- NEVER expose secrets in command