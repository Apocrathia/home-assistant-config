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
not use git worktrees — stay in the main checkout
([`worktrees.md`](../../rules/worktrees.md)).

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
| Docs issue / Local Todo needs scoping  | Vague title; acceptance not yet writable                                        |
| Package / area placement unclear       | New device could live under `areas/`, `integrations/`, or `projects/`           |
| Security / presence / energy tradeoffs | Away mode, notifications, secrets, network exposure                             |
| Before filing or planning              | Feature/spec/`slice: hitl`/multi-path bug without writable acceptance           |
| Implement gate                         | [`implement-change`](../implement-change/SKILL.md) when expectations still open |

**Skip** when acceptance is already explicit (clear issue/plan or Local Todo
item with enough detail, or a prior alignment summary in this thread).

## Typical flow

```text
idea / docs issue / Local Todo row / find-work brief
        │
        ▼
   /alignment  (read-only; grill until shared understanding)
        │
        ├──► file-issue → docs/issues/   (agent channel)
        ├──► plan authoring → docs/plans/
        ├──► implement-change (packages/, esphome/, docs/)
        ├──► config-validate / package-organize / automation-debug
        ├──► ha-config-expert / automation-architect
        └──► prototype in .scratch/
```

After alignment, **do not** write Local Todo ICS. Agents file durable gaps
under `docs/issues/`; humans keep using the HA UI for their own reports.

## End summary

When the tree is complete, reply with: decisions made, open items (if any),
and a suggested next step:

| Situation                                  | Next                                                                                                                                                     |
| ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Gap ready to record                        | [`file-issue`](../file-issue/SKILL.md) → `docs/issues/<slug>.md`                                                                                         |
| How-work needed                            | Author `docs/plans/<slug>.md`; link issue `plan:`                                                                                                        |
| Scoped YAML / package / automation change  | [`implement-change`](../implement-change/SKILL.md) after operator says proceed                                                                           |
| YAML validity / layout / broken automation | [`config-validate`](../config-validate/SKILL.md), [`package-organize`](../package-organize/SKILL.md), [`automation-debug`](../automation-debug/SKILL.md) |
| Deep HA config unknowns                    | [`ha-config-expert`](../../agents/ha-config-expert/agent.md)                                                                                             |
| Complex automation design                  | [`automation-architect`](../../agents/automation-architect/agent.md)                                                                                     |
| Still exploring shape of logic/UI          | [`prototype`](../prototype/SKILL.md) in `.scratch/`                                                                                                      |
| Still ambiguous                            | Stop; list remaining decisions — do not invent scope                                                                                                     |

Alignment output should be concrete enough to drive filing or implementation
(**Problem**, **Acceptance**, target path under `packages/` / `esphome/` /
`docs/`) without another discovery pass.

## Do not

- Commit, push, open PRs, create branches, or open worktrees
- Write to `.shopping_list.json` or `.storage/local_todo.*.ics`
- Start implementation until the operator says proceed
- File issues during alignment unless the operator asked to file as the next step
