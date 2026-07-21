# Context Loading — Home Assistant Homelab

## Routing Table

Load context modules in this order. Each file is a thin module that loads on demand.

1. **`.agents/context/README.md`** — Start here for overview
2. **`.agents/context/constraints.md`** — Hard limits (always load before config changes)
3. **`.agents/context/traps.md`** — Known pitfalls (load before non-trivial changes)
4. **`.agents/context/nomenclature.md`** — Naming conventions (load when creating entities)
5. **`.agents/context/voice.md`** — Communication style (load for substantive replies)
6. **`.agents/context/output.md`** — Output format expectations (load when writing docs)
7. **`.agents/context/questions.md`** — Clarification protocol (load when scope is fuzzy)

## When to Load What

| If you're…                       | Then read                              |
| -------------------------------- | -------------------------------------- |
| New / unsure                     | `README.md` only                       |
| Starting non-trivial work        | `traps.md` + `constraints.md`          |
| Creating entities or automations | `nomenclature.md`                      |
| Scope is fuzzy                   | `questions.md`                         |
| Writing docs or agent tone       | `voice.md` + `output.md`               |
| Validating YAML configs          | `skills/config-validate/SKILL.md`      |
| Restructuring packages           | `skills/package-organize/SKILL.md`     |
| Fixing broken automations        | `skills/automation-debug/SKILL.md`     |
| Deep HA config knowledge needed  | `agents/ha-config-expert/agent.md`     |
| Complex automation design needed | `agents/automation-architect/agent.md` |

## Rules

1. Context modules are **lazy-loaded** — only load what the task needs
2. Each module is self-contained — reference others by path, not by content duplication
3. Keep modules focused — one concern per file
4. Update `README.md` (context hub) when adding new modules
