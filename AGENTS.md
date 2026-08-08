# Home Assistant Homelab - AI Agent Context Router

## How This Works

You are operating in a Home Assistant configuration repository. This directory is the user's
Home Assistant config — the single source of truth for their smart home.

**60-second model:** `packages/*` is the meat; `.agents/` is AI context; git and
HA to-do stores (`.shopping_list.json`, `.storage/local_todo.*.ics`) are
operator/HA-owned (agents never commit or write those). Start at [`.agents/context/README.md`](./.agents/context/README.md).

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
9. **`.agents/context/work-sources.md`** — Work discovery sources
10. **`.agents/context/tools.md`** — HA MCP, Grafana HA history, config check, shopping-list jq

## Routing

Start at [`.agents/context/README.md`](./.agents/context/README.md). Skip detail: [`.agents/context/loading.md`](./.agents/context/loading.md).

| If you're…                              | Then read                                                                   |
| --------------------------------------- | --------------------------------------------------------------------------- |
| New / unsure                            | `README.md` only                                                            |
| Starting non-trivial work               | `traps.md` + `constraints.md`                                               |
| Creating entities or automations        | `nomenclature.md` + `output.md` + `constraints.md`                          |
| Scope is fuzzy                          | `questions.md`                                                              |
| Writing docs or agent tone              | `voice.md` + `output.md`                                                    |
| Finding work to do                      | `work-sources.md` + `skills/find-work/SKILL.md`                             |
| Implementing a scoped change            | `constraints.md` + `skills/implement-change/SKILL.md` (hand off, no commit) |
| Validating YAML configs                 | `tools.md` + `skills/config-validate/SKILL.md`                              |
| Restructuring packages                  | `skills/package-organize/SKILL.md`                                          |
| Fixing broken automations               | `skills/automation-debug/SKILL.md`                                          |
| Past HA entity state / history          | `tools.md` + `skills/grafana-ha-history/SKILL.md`                           |
| Syncing `.agents/` from upstream        | `skills/integrate-upstream/SKILL.md`                                        |
| Context claims drifted from repo        | `skills/reconcile-context/SKILL.md`                                         |
| Tempted to commit / push / open PR      | `rules/operator-owned-git.md` — don't                                       |
| Auditing security posture / dep vectors | `agents/security-analyst/agent.md` + `rules/deepwiki.md`                    |
| Deep HA config knowledge needed         | `agents/ha-config-expert/agent.md`                                          |
| Complex automation design needed        | `agents/automation-architect/agent.md`                                      |

## Skills

When performing specific tasks, consult relevant skill files:

| Skill                | Path                                         | Use When                                                             |
| -------------------- | -------------------------------------------- | -------------------------------------------------------------------- |
| Config Validation    | `.agents/skills/config-validate/SKILL.md`    | Writing or modifying YAML configs                                    |
| Package Organization | `.agents/skills/package-organize/SKILL.md`   | Restructuring or creating packages                                   |
| Automation Debugging | `.agents/skills/automation-debug/SKILL.md`   | Fixing broken automations                                            |
| Grafana HA History   | `.agents/skills/grafana-ha-history/SKILL.md` | Past entity state via Grafana InfluxDB                               |
| Find Work            | `.agents/skills/find-work/SKILL.md`          | Discovering open work — sources in `.agents/context/work-sources.md` |
| Implement Change     | `.agents/skills/implement-change/SKILL.md`   | One change lap → validate → operator handoff                         |
| Upstream Integration | `.agents/skills/integrate-upstream/SKILL.md` | Syncing `.agents/` from the prime-context core                       |
| Reconcile Context    | `.agents/skills/reconcile-context/SKILL.md`  | Fix drift between context claims and the repo                        |
| Create Agent         | `.agents/skills/create-agent/SKILL.md`       | New persona under `.agents/agents/`                                  |
| Create Skill         | `.agents/skills/create-skill/SKILL.md`       | New procedural skill under `.agents/skills/`                         |

Shared skills from the [prime-context](https://github.com/PrimeIntellect-ai/prime-context)
core (alignment, review-loop, reconcile-docs, ship-work, and others)
also live under `.agents/skills/`. The pinned upstream revision is in
`.agents/upstream-ref`. **Shipping/commit steps are overridden by
`.agents/rules/operator-owned-git.md`.**

## Agents

Specialized agent profiles for complex tasks:

| Agent                | Path                                           | Role                                   |
| -------------------- | ---------------------------------------------- | -------------------------------------- |
| HA Config Expert     | `.agents/agents/ha-config-expert/agent.md`     | Deep HA configuration knowledge        |
| Automation Architect | `.agents/agents/automation-architect/agent.md` | Complex automation design              |
| Security Analyst     | `.agents/agents/security-analyst/agent.md`     | Adversarial, audit-only posture review |

## Key Directories

| Path                     | Purpose                                        |
| ------------------------ | ---------------------------------------------- |
| `packages/`              | Modular YAML configs (the meat)                |
| `packages/areas/`        | Room/location-specific configs                 |
| `packages/functions/`    | Bundled functionality configs                  |
| `packages/integrations/` | Integration/device configs                     |
| `packages/private/`      | Local-only packages (gitignored except README) |
| `packages/projects/`     | Multi-device projects                          |
| `packages/routines/`     | Time/event-based automations                   |
| `packages/system/`       | HA system management                           |
| `packages/toys/`         | Fun/non-essential automations                  |
| `docs/`                  | Documentation and diagrams                     |
| `esphome/`               | ESPHome device definitions                     |
| `utilities/`             | Helper scripts                                 |
| `.scratch/`              | Local throwaways (gitignored except README)    |
| `.agents/`               | AI context, rules, skills, agents              |

## Quick Reference

- **Main config**: `configuration.yaml` (includes `packages/*`)
- **Secrets**: `secrets.yaml` (never hardcode credentials)
- **Storage**: `.storage/` (JSON — do NOT edit directly)
- **Work sources**: `.storage/local_todo.*.ics` (Issues/Tasks/Ideas) and
  `.shopping_list.json` (read-only; see `work-sources.md`)
- **Custom components**: `custom_components/`
- **Themes**: `themes/`
- **CLAUDE.md**: symlink → `AGENTS.md`

## Rules

1. Always load context modules in order (see loading.md)
2. Respect constraints (see constraints.md) — these are non-negotiable
3. Know the traps (see traps.md) — learn from past mistakes
4. Use the nomenclature (see nomenclature.md) — names matter
5. Match the voice (see voice.md) — communicate appropriately
6. Format output as specified (see output.md) — consistency matters
7. Ask questions when needed (see questions.md) — clarify before assuming
8. Git is operator-owned (see `.agents/rules/operator-owned-git.md`) — never
   commit, push, or open PRs; this overrides any upstream skill that ships work
9. HA to-do stores are read-only work sources (see
   `.agents/context/work-sources.md`) — never write
   `.shopping_list.json` or `.storage/local_todo.*.ics`
