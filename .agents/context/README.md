# Context Hub — Home Assistant Homelab

## 60-second model

This repo **is** the live Home Assistant config. Agents edit files; the operator
validates against the running instance, then owns git.

| Layer                 | What it is                                                                                          |
| --------------------- | --------------------------------------------------------------------------------------------------- |
| `packages/*`          | The meat — modular YAML (areas, functions, integrations, projects, routines, system, toys, private) |
| `configuration.yaml`  | Entry point; includes packages                                                                      |
| `.agents/`            | AI context, rules, skills, agents — not HA config                                                   |
| `.shopping_list.json` | Read-only work source (HA-owned; see `work-sources.md`)                                             |
| Git                   | Operator-owned — never commit/push/PR (`rules/operator-owned-git.md`)                               |

Done here means: change → validate (config check / live HA) → hand off with a
suggested Conventional Commit. Upstream shipping skills that commit are
overridden.

## Overview

This directory holds context modules that shape how AI agents work in this
repo. Each file is a thin, focused module loaded on demand. Module names stay
HA-native (`constraints`, `traps`, `nomenclature`, …) — not renamed to
prime-context labels like invariants/pitfalls/vocabulary.

## The context is living

Stale context is worse than none — confidently wrong. When routing, paths, or
repo layout drift, run
[`skills/reconcile-context/SKILL.md`](../skills/reconcile-context/SKILL.md).
Keep modules thin; update this hub when adding modules.

## Context Modules

| Module       | File              | Purpose                                       |
| ------------ | ----------------- | --------------------------------------------- |
| Loading      | `loading.md`      | What to load and when                         |
| Constraints  | `constraints.md`  | Hard limits and non-negotiables               |
| Traps        | `traps.md`        | Known pitfalls and gotchas                    |
| Nomenclature | `nomenclature.md` | Naming conventions and patterns               |
| Voice        | `voice.md`        | Communication style guide                     |
| Output       | `output.md`       | Output format expectations                    |
| Questions    | `questions.md`    | Clarification protocol                        |
| Work sources | `work-sources.md` | Where to find open work (incl. shopping list) |
| Tools        | `tools.md`        | HA MCP, Grafana HA history, config check, jq  |

## Rules (always-on)

Located in `.agents/rules/`. Generic rules come from the
[prime-context](https://github.com/PrimeIntellect-ai/prime-context) core
(pinned in `.agents/upstream-ref`). Project-specific override:

| Rule               | File                          | Purpose                                                         |
| ------------------ | ----------------------------- | --------------------------------------------------------------- |
| Operator-owned git | `rules/operator-owned-git.md` | No agent commits/pushes/PRs; overrides upstream shipping skills |

## Skills

Located in `.agents/skills/` — task-specific playbooks:

| Skill                | Path                         | Use When                                      |
| -------------------- | ---------------------------- | --------------------------------------------- |
| Config Validation    | `skills/config-validate/`    | Writing or modifying YAML configs             |
| Package Organization | `skills/package-organize/`   | Restructuring or creating packages            |
| Automation Debugging | `skills/automation-debug/`   | Fixing broken automations                     |
| Grafana HA History   | `skills/grafana-ha-history/` | Past entity state via Grafana InfluxDB        |
| Find Work            | `skills/find-work/`          | Discovering open work (see `work-sources.md`) |
| Upstream Integration | `skills/integrate-upstream/` | Syncing `.agents/` from prime-context         |
| Implement Change     | `skills/implement-change/`   | One change lap → validate → operator handoff  |
| Reconcile Context    | `skills/reconcile-context/`  | Fix drift between context claims and the repo |

Additional shared skills from the prime-context core (alignment, review-loop,
reconcile-docs, file-issue, retrospective, ship-work, and others) live
alongside them. **All shipping/commit steps in shared skills are overridden by
`rules/operator-owned-git.md`** — agents stop at validation and hand off to the
operator.

## Agents

Located in `.agents/agents/` — specialized profiles for complex tasks:

| Agent                | Path                           | Role                                          |
| -------------------- | ------------------------------ | --------------------------------------------- |
| HA Config Expert     | `agents/ha-config-expert/`     | Deep Home Assistant configuration knowledge   |
| Automation Architect | `agents/automation-architect/` | Complex automation design and patterns        |
| Security Analyst     | `agents/security-analyst/`     | Adversarial, audit-only config posture review |

## Loading Strategy

Context modules are **lazy-loaded** — only load what the task needs. The router
(`AGENTS.md`) points here; detail lives in `loading.md`. Each module is
self-contained and references others by path.

## Hub rules

1. Keep modules focused — one concern per file
2. Reference other modules by path, not by content duplication
3. Update this hub when adding new modules
4. Keep `AGENTS.md` thin — it's a router, not a content file
5. `CLAUDE.md` is a symlink to `AGENTS.md` — edit the router once
