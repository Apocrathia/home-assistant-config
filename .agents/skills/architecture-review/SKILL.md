---
name: architecture-review
description: >-
  Explore packages/, layout, and .agents/ for architectural friction (coupling,
  shallow packages, missing boundaries) and file or recommend agent issues under
  docs/issues/. Use when improving config shape, before large refactors, or when
  find-work should surface design-debt candidates.
disable-model-invocation: true
---

# Architecture review — Home Assistant Homelab

Read-only exploration that ends in **candidates** the operator can pick, then
optional filing under `docs/issues/` (`kind: architecture`) via
[`file-issue`](../file-issue/SKILL.md). Git is operator-owned
([`operator-owned-git.md`](../../rules/operator-owned-git.md)). No worktrees
([`worktrees.md`](../../rules/worktrees.md)).

Human Local Todo stays human — do not write ICS. Prefer docs issues for
agent-owned architecture debt.

## Deliverable

A numbered candidate list. For each pick the operator cares about: **Problem**,
**Proposed direction**, **Feedback loop**, and either:

1. File `docs/issues/<slug>.md` from `_template.md` (`kind: architecture`), or
2. Leave as chat-only if the operator declines filing

## Workflow

```
- [ ] 1. Orient: AGENTS.md, constraints + traps, packages layout
- [ ] 2. Explore (read-only): packages/, esphome/, docs/, .agents/
- [ ] 3. Present numbered candidates
- [ ] 4. Operator picks (or asks for a deeper sketch on rank-1)
- [ ] 5. For each pick: problem space + package sketch (chat); no code edits
- [ ] 6. On operator OK: file-issue for each kept candidate
```

## What to look for

- Shallow packages / cross-area coupling
- Logic bouncing across many files for one routine
- Secrets risking hardcoding / wrong package home
- Automations without a clear validation path
- ESPHome / packages / docs drift
- `.agents/` routing that points at missing paths
- Untested assumptions about live entities

## Candidate content (per pick)

- **Problem** — packages/modules involved
- **Proposed direction** — `packages/areas|functions|integrations|projects|routines|system|toys/`
- **Feedback loop** — `config-validate`, reload, live entity check, automation trace
- **Suggested next** — alignment / plan / implement-change / file-issue

## Orient paths

| Path                                    | Why                              |
| --------------------------------------- | -------------------------------- |
| [`AGENTS.md`](../../../AGENTS.md)       | Router                           |
| [`packages/`](../../../packages/)       | Modular YAML                     |
| [`esphome/`](../../../esphome/)         | Device definitions               |
| [`.agents/context/`](../../context/)    | Constraints, traps, nomenclature |
| [`docs/issues/`](../../../docs/issues/) | Agent issue ledger               |

## Do not

- Edit packages, ESPHome, or `.agents/` in this skill (exploration only)
- Write Local Todo ICS or `.shopping_list.json`
- Create GitHub issues unless the operator asks
- File vague "refactor X" without a named feedback loop
- Commit, push, open PRs, or create worktrees
