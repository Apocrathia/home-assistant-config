---
name: reconcile-docs
description: >-
  Sync docs/ with Home Assistant packages and project reality when config and
  docs drift. Use after package/layout changes or when asked to update docs.
disable-model-invocation: true
---

# Reconcile docs

Bring `docs/` in line with the live Homelab config and package layout. This is
practical HA doc sync — not a swarm issues/plans lifecycle.

**Docs that exist:** `docs/README.md`, `docs/packages.md`, `docs/projects.md`,
`docs/CONTRIBUTING.md`, `docs/LICENSE.md`, `docs/images/`. There is no
`docs/issues/`, `docs/plans/`, or `docs/backlog/` — do not create them, and do
not run a "delete satisfied issues/plans" workflow.

**Checkout:** edit in the main working tree only. No git worktrees, no branch
ceremony.

Git is operator-owned: edit docs, validate links, hand off with a suggested
Conventional Commit. Do not commit or push.

## When to run

- Packages added/moved/removed under `packages/`
- Project docs out of date vs `packages/projects/` or `docs/projects.md`
- Operator asks to update or reconcile docs
- After a config change that docs claim to describe

## Workflow

```
- [ ] 1. Summarize what moved (packages, projects, architecture claims)
- [ ] 2. Diff docs vs reality; update affected pages only
- [ ] 3. Cross-link; keep README doc index accurate
- [ ] 4. Link check (--all); hand off
```

### 1. Summarize

One short paragraph: what behavior or layout changed, which doc pages cover it.
Use `ls packages/**` / `git diff` against the base as needed.

### 2. Update docs

| Doc                    | Reconcile against                                                                                                |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `docs/packages.md`     | Real dirs/files under `packages/` (areas, functions, integrations, private, projects, routines, system, toys, …) |
| `docs/projects.md`     | `packages/projects/` and related config                                                                          |
| `docs/README.md`       | Architecture blurb and links to the pages above                                                                  |
| `docs/CONTRIBUTING.md` | Actual contribution / validation flow if claims drifted                                                          |

Edit only what drifted. Don't invent backlog/issue trackers. Follow-up work
goes through [`work-sources.md`](../../context/work-sources.md) /
[`file-issue`](../file-issue/SKILL.md), not new doc trees.

If agent context also drifted, run or hand off to
[`reconcile-context`](../reconcile-context/SKILL.md) (protected paths need
confirmation). Don't silently rewrite `.agents/**` from this skill.

### 3–4. Verify and hand off

```bash
python3 .agents/skills/reconcile-context/scripts/check_links.py --all
```

## Report

```markdown
## Reconcile docs

**Docs updated:** <files>
**Skipped (no such surface):** issues/plans/backlog
**Context follow-up:** <none | run reconcile-context>
**Link check:** <pass | fixed N>
**Suggested commit:** <type(scope): description>
```

Clean pass: one line and stop.
