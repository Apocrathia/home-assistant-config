# Context Hub — Home Assistant Homelab

## Overview

This directory contains all context modules that shape how AI agents interact with this Home Assistant configuration. Each file is a thin, focused module that loads on demand.

## Context Modules

| Module       | File              | Purpose                         |
| ------------ | ----------------- | ------------------------------- |
| Loading      | `loading.md`      | What to load and when           |
| Constraints  | `constraints.md`  | Hard limits and non-negotiables |
| Traps        | `traps.md`        | Known pitfalls and gotchas      |
| Nomenclature | `nomenclature.md` | Naming conventions and patterns |
| Voice        | `voice.md`        | Communication style guide       |
| Output       | `output.md`       | Output format expectations      |
| Questions    | `questions.md`    | Clarification protocol          |

## Skills

Located in `.agents/skills/` — task-specific playbooks:

| Skill                | Path                       | Use When                           |
| -------------------- | -------------------------- | ---------------------------------- |
| Config Validation    | `skills/config-validate/`  | Writing or modifying YAML configs  |
| Package Organization | `skills/package-organize/` | Restructuring or creating packages |
| Automation Debugging | `skills/automation-debug/` | Fixing broken automations          |

## Agents

Located in `.agents/agents/` — specialized profiles for complex tasks:

| Agent                | Path                           | Role                                        |
| -------------------- | ------------------------------ | ------------------------------------------- |
| HA Config Expert     | `agents/ha-config-expert/`     | Deep Home Assistant configuration knowledge |
| Automation Architect | `agents/automation-architect/` | Complex automation design and patterns      |

## Loading Strategy

Context modules are **lazy-loaded** — only loaded when needed. The router (`AGENTS.md`) defines the order. Each module is self-contained and references the others only by path.

## Rules

1. Keep modules focused — one concern per file
2. Reference other modules by path, not by content duplication
3. Update this hub when adding new modules
4. Keep AGENTS.md thin — it's a router, not a content file
