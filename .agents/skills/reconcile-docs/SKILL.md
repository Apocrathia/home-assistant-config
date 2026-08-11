---
name: reconcile-docs
description: >-
  Sync docs/ with Home Assistant packages and project reality, and delete
  satisfied docs/issues and docs/plans in the shipping change. Use after
  package/layout changes or when asked to update docs.
disable-model-invocation: true
---

# Reconcile docs

Bring `docs/` in line with the live Homelab config and package layout. Also
run the issue/plan **delete-on-ship** cleanup when acceptance is met.

**Checkout:** edit in the main working tree only. No git worktrees
([`worktrees.md`](../../rules/worktrees.md)).

Git is operator-owned: edit docs, validate links, hand off with a suggested
Conventional Commit. Do not commit or push
([`operator-owned-git.md`](../../rules/operator-owned-git.md)).

## Surfaces

| Path                                                              | Role                                           |
| ----------------------------------------------------------------- | ---------------------------------------------- |
| `docs/README.md`, `packages.md`, `projects.md`, `CONTRIBUTING.md` | Human docs                                     |
| `docs/issues/`                                                    | Agent what-ledger — delete when acceptance met |
| `docs/plans/`                                                     | How-ledger — delete when done / acceptance met |

Never write Local Todo ICS or `.shopping_list.json`.

## When to run

- Packages added/moved/removed under `packages/`
- Project docs out of date vs `packages/projects/` or `docs/projects.md`
- Shipping a change that satisfies an open issue/plan
- Operator asks to update or reconcile docs

## Workflow

```
- [ ] 1. Summarize what moved (packages, projects, issues/plans touched)
- [ ] 2. Diff docs vs reality; update affected pages only
- [ ] 3. Delete-on-ship: satisfied issues/plans + fix backlinks
- [ ] 4. Cross-link; keep README doc index accurate
- [ ] 5. Link check (--all); hand off
```

### 2. Update human docs

| Doc                    | Reconcile against                                                                 |
| ---------------------- | --------------------------------------------------------------------------------- |
| `docs/packages.md`     | Real dirs/files under `packages/`                                                 |
| `docs/projects.md`     | `packages/projects/` and related config                                           |
| `docs/README.md`       | Architecture blurb and links (include issues/plans ledgers when documenting them) |
| `docs/CONTRIBUTING.md` | Actual contribution / validation flow if claims drifted                           |

### 3. Delete-on-ship

When this change meets acceptance on a linked issue or finishes a plan:

1. Fix backlinks in related plans/docs/issues
2. **Delete** `docs/issues/<slug>.md` and/or `docs/plans/<slug>.md` in this
   change (operator commits later)
3. Do not keep a `closed/` tree — git history is the archive

See [`docs/issues/README.md`](../../../docs/issues/README.md) and
[`docs/plans/README.md`](../../../docs/plans/README.md).

If agent context also drifted, hand off to
[`reconcile-context`](../reconcile-context/SKILL.md) (protected paths need
confirmation).

### 5. Verify and hand off

```bash
python3 .agents/skills/reconcile-context/scripts/check_links.py --all
```

## Report

```markdown
## Reconcile docs

**Docs updated:** <files>
**Deleted (shipped):** <issue/plan paths or none>
**Context follow-up:** <none | run reconcile-context>
**Link check:** <pass | fixed N>
**Suggested commit:** <type(scope): description>
```

Clean pass: one line and stop.
