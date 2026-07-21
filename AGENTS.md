# Home Assistant Homelab - AI Agent Context Router

## How This Works

You are operating in a Home Assistant configuration repository. This directory is the user's
Home Assistant config — the single source of truth for their smart home.

## Context Loading Order

Load context modules in this order. Each file is a thin shim that points to deeper context:

1. **`.agents/context/README.md`** — Context hub (start here)
2. **`.agents/context/loading.md`** — What to load and when
3. **`.agents/context/constraints.md`** — Hard limits and non-negotiables
4. **`.agents/context/traps.md`** — Known pitfalls and gotchas
5. **`.agents/context/nomenclature.md`** — How things are named
6. **`.agents/context/voice.md`** — Communication style
7. **`.agents/context/output.md`** — Output format expectations
8. **`.agents/context/questions.md`** — Clarification protocol

## Routing

Start at [`.agents/context/README.md`](./.agents/context/README.md). Skip detail: [`.agents/context/loading.md`](./.agents/context/loading.md).

| If you're…                       | Then read                                          |
| -------------------------------- | -------------------------------------------------- |
| New / unsure                     | `README.md` only                                   |
| Starting non-trivial work        | `traps.md` + `constraints.md`                      |
| Creating entities or automations | `nomenclature.md` + `output.md` + `constraints.md` |
| Scope is fuzzy                   | `questions.md`                                     |
| Writing docs or agent tone       | `voice.md` + `output.md`                           |
| Validating YAML configs          | `skills/config-validate/SKILL.md`                  |
| Restructuring packages           | `skills/package-organize/SKILL.md`                 |
| Fixing broken automations        | `skills/automation-debug/SKILL.md`                 |
| Deep HA config knowledge needed  | `agents/ha-config-expert/agent.md`                 |
| Complex automation design needed | `agents/automation-architect/agent.md`             |

## Skills

When performing specific tasks, consult relevant skill files:

| Skill                | Path                                       | Use When                           |
| -------------------- | ------------------------------------------ | ---------------------------------- |
| Config Validation    | `.agents/skills/config-validate/SKILL.md`  | Writing or modifying YAML configs  |
| Package Organization | `.agents/skills/package-organize/SKILL.md` | Restructuring or creating packages |
| Automation Debugging | `.agents/skills/automation-debug/SKILL.md` | Fixing broken automations          |

## Agents

Specialized agent profiles for complex tasks:

| Agent                | Path                                           | Role                            |
| -------------------- | ---------------------------------------------- | ------------------------------- |
| HA Config Expert     | `.agents/agents/ha-config-expert/agent.md`     | Deep HA configuration knowledge |
| Automation Architect | `.agents/agents/automation-architect/agent.md` | Complex automation design       |

## Key Directories

| Path                     | Purpose                                     |
| ------------------------ | ------------------------------------------- |
| `packages/`              | Modular YAML configs (the meat)             |
| `packages/areas/`        | Room/location-specific configs              |
| `packages/functions/`    | Bundled functionality configs               |
| `packages/integrations/` | Integration/device configs                  |
| `packages/projects/`     | Multi-device projects                       |
| `packages/routines/`     | Time/event-based automations                |
| `packages/system/`       | HA system management                        |
| `packages/toys/`         | Fun/non-essential automations               |
| `docs/`                  | Documentation and diagrams                  |
| `esphome/`               | ESPHome device definitions                  |
| `utilities/`             | Helper scripts                              |
| `.scratch/`              | Local throwaways (gitignored except README) |

## Quick Reference

- **Main config**: `configuration.yaml` (includes `packages/*`)
- **Secrets**: `secrets.yaml` (never hardcode credentials)
- **Storage**: `.storage/` (JSON — do NOT edit directly)
- **Custom components**: `custom_components/`
- **Themes**: `themes/`

## Rules

1. Always load context modules in order (see loading.md)
2. Respect constraints (see constraints.md) — these are non-negotiable
3. Know the traps (see traps.md) — learn from past mistakes
4. Use the nomenclature (see nomenclature.md) — names matter
5. Match the voice (see voice.md) — communicate appropriately
6. Format output as specified (see output.md) — consistency matters
7. Ask questions when needed (see questions.md) — clarify before assuming
