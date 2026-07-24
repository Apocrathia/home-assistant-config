---
name: alignment
description: >-
  Interview the operator about a topic until shared understanding, walking each
  branch of the decision tree one at a time. Use when stress-testing an idea,
  design, or requirement; resolving open questions before acting; or when the
  user says alignment, /alignment, or wants to get aligned.
disable-model-invocation: true
---

# Alignment — Home Assistant Homelab

Read-only. Do not edit files, commit, or implement until alignment is reached
and the operator explicitly asks to proceed. Git is operator-owned
([`operator-owned-git.md`](../../rules/operator-owned-git.md)). This repo does
not use git worktrees — stay in the main checkout.

Derived from the [grill-me](https://www.aihero.dev/my-grill-me-skill-has-gone-viral)
pattern: interview relentlessly until shared understanding, one decision branch
at a time. Explore the repo when that answers the question; do not ask the
operator to repeat what the tree already shows.

For each question, use the format in
[`question-format.md`](../../rules/question-format.md): Context, **Ask**,
Suggestion, Gaps/concerns (omit Gaps when none).

## When to run

Run **before** changing config when any of these apply:

| Trigger                                | Examples                                                                        |
| -------------------------------------- | ------------------------------------------------------------------------------- |
| New feature or automation              | Desired behavior unclear, multiple package homes, stop condition fuzzy          |
| Shopping-list item needs scoping       | Vague title; acceptance not yet writable                                        |
| Package / area placement unclear       | New device could live under `areas/`, `integrations/`, or `projects/`           |
| Security / presence / energy tradeoffs | Away mode, notifications, secrets, network exposure                             |
| Implement gate                         | [`implement-change`](../implement-change/SKILL.md) when expectations still open |

**Skip** when acceptance is already explicit (clear shopping-list item with
enough detail, or a prior alignment summary in this thread). Do not re-run
alignment in the same thread if a summary already exists.

## Typical flow

```text
idea / shopping-list row / find-work brief
        │
        ▼
   /alignment  (read-only; grill until shared understanding)
        │
        ├──► implement-change (config under packages/, esphome/, docs/)
        ├──► config-validate / package-organize / automation-debug
        ├──► ha-config-expert / automation-architect
        └──► prototype in .scratch/ (design question still open)
```

This repo has **no** `docs/issues/` or `docs/plans/` as first-class surfaces.
Do not route alignment output into those paths. Capture acceptance in the
thread (and optionally recommend a shopping-list wording for the operator to
add in HA if they want a durable to-do).

## End summary

When the tree is complete, reply with: decisions made, open items (if any),
and a suggested next step:

| Situation                                  | Next                                                                                                                                                     |
| ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Scoped YAML / package / automation change  | [`implement-change`](../implement-change/SKILL.md) after operator says proceed                                                                           |
| YAML validity / layout / broken automation | [`config-validate`](../config-validate/SKILL.md), [`package-organize`](../package-organize/SKILL.md), [`automation-debug`](../automation-debug/SKILL.md) |
| Deep HA config unknowns                    | [`ha-config-expert`](../../agents/ha-config-expert/agent.md)                                                                                             |
| Complex automation design                  | [`automation-architect`](../../agents/automation-architect/agent.md)                                                                                     |
| Still exploring shape of logic/UI          | [`prototype`](../prototype/SKILL.md) in `.scratch/`                                                                                                      |
| Cursor / `.agents/` / skills / hooks       | Propose edits; wait for confirmation per [`protected-paths.md`](../../rules/protected-paths.md)                                                          |
| Still ambiguous                            | Stop; list remaining decisions — do not invent scope                                                                                                     |

Alignment output should be concrete enough to drive implementation
(**Problem**, **Acceptance**, target path under `packages/` / `esphome/` /
`docs/`) without another discovery pass.

## Routed from

- [`find-work`](../find-work/SKILL.md): vague shopping-list or multi-path items
- [`implement-change`](../implement-change/SKILL.md): alignment gate before edits
- [`clarify-dont-guess.md`](../../rules/clarify-dont-guess.md) / [`subagents.md`](../../rules/subagents.md): extended ambiguity

## Do not

- Commit, push, open PRs, or create branches
- Write issue/plan files under `docs/issues/` or `docs/plans/`
- Write to `.shopping_list.json` (operator / HA owns it)
- Start implementation until the operator says proceed
