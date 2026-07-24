---
name: architecture-review
description: >-
  Explore packages/, layout, and .agents/ for architectural friction (coupling,
  shallow packages, missing boundaries) and recommend work to the operator.
  Use when improving config shape, before large refactors, or when find-work
  should surface design-debt candidates. Does not file docs/issues.
disable-model-invocation: true
---

# Architecture review — Home Assistant Homelab

Read-only exploration that ends in **operator-facing recommendations**, not
code edits and not issue files. Git is operator-owned
([`operator-owned-git.md`](../../rules/operator-owned-git.md)).

This repo has **no** `docs/issues/` or `docs/plans/` as first-class surfaces.
Do not create those paths. Hand findings to the operator (and optionally
suggest shopping-list wording they can add in Home Assistant).

## Deliverable

A numbered candidate list the operator can pick from. For each pick the
operator cares about: **Problem**, **Proposed direction**, **Feedback loop**,
and a suggested next skill / path. Optionally: recommend a shopping-list
title + one-line acceptance for the operator to capture in HA.

[`find-work`](../find-work/SKILL.md) may later re-surface these themes if the
operator adds them to the shopping list or documents them under `docs/`.

## Workflow

```
- [ ] 1. Orient: AGENTS.md, .agents/context/constraints.md + traps.md, packages layout
- [ ] 2. Explore (read-only): packages/, esphome/, docs/, .agents/ — note friction
- [ ] 3. Present numbered candidates (clusters, coupling, validation gaps)
- [ ] 4. Operator picks candidates (or asks for a deeper sketch on rank-1)
- [ ] 5. For each pick: problem space + interface/package sketch (chat); no edits
- [ ] 6. Hand off: recommend shopping-list wording and/or next skill
```

## What to look for

Surfaces that matter here (not Rust crates):

- Shallow packages: almost everything in one YAML file with no clear boundary
- Cross-area coupling: area packages depending on unrelated integrations
- Logic bouncing across many files to understand one routine
- Secrets or credentials risking hardcoding / wrong package home
- Automations without a clear validation or feedback path
- ESPHome / packages / docs drift (entity names, areas, device ownership)
- `.agents/` routing that points at missing paths or upstream-only workflows
- Untested assumptions about live entities (prefer HA MCP / live context when useful)

Friction you hit while exploring **is** the signal.

## Candidate content (per pick)

- **Problem** — packages/modules involved, coupling, live-config risk
- **Proposed direction** — where complexity should live (`packages/areas/`,
  `functions/`, `integrations/`, `projects/`, `routines/`, `system/`, `toys/`)
- **Dependency strategy** — helpers, scripts, secrets, ESPHome ownership
- **Feedback loop** — how to prove the refactor (`config-validate`, reload,
  live entity check, automation trace)
- **Suggested next** — skill + whether shopping-list capture is useful

Do not paste a full implementation plan; stop at enough clarity for alignment
or implement-change.

## Orient paths

| Path                                 | Why                               |
| ------------------------------------ | --------------------------------- |
| [`AGENTS.md`](../../../AGENTS.md)    | Router                            |
| [`packages/`](../../../packages/)    | Modular YAML (the meat)           |
| [`esphome/`](../../../esphome/)      | Device definitions                |
| [`.agents/context/`](../../context/) | Constraints, traps, nomenclature  |
| [`docs/`](../../../docs/)            | Human docs (not an issue tracker) |

## Do not

- Edit packages, ESPHome, or `.agents/` in this skill (exploration only)
- Create `docs/issues/`, `docs/plans/`, or GitHub issues unless the operator asks
- Write to `.shopping_list.json` — recommend wording; operator adds in HA
- File vague "refactor X" without a named feedback loop
- Commit, push, open PRs, or create branches
