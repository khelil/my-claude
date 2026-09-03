---
name: gsd-settings
description: "Configure GSD workflow toggles and model profile"
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
---


<objective>
Interactive configuration of GSD workflow agents and model profile via multi-question prompt.

Routes to the settings workflow which handles:
- Config existence ensuring
- Current settings reading and parsing
- Interactive 5-question prompt (model, research, plan_check, verifier, branching)
- Config merging and writing
- Confirmation display with quick command references
</objective>

<execution_context>
To load this command's workflow spec: check for `.claude/gsd-core/workflows/settings.md` relative to the current working directory first (project-local); if it is not there, fall back to `~/.claude/gsd-core/workflows/settings.md` (the global install). If neither file exists, stop — a workflow spec is required and none was found.
</execution_context>

<process>
Execute end-to-end.
</process>
