# Development loop

Find → rank → one Launch brief → fork by work type → validate → operator
handoff. Chat is not the backlog: agent issues = desired state; plans = how;
Local Todo = human reports; operator commits = durable behavior.

## Non-negotiables (loop)

| Constraint            | Implication                                                                                                                 |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| Operator-owned git    | No commit/push/PR — hand off with suggested Conventional Commit ([`operator-owned-git.md`](../rules/operator-owned-git.md)) |
| No worktrees          | Edit in the main checkout ([`worktrees.md`](../rules/worktrees.md))                                                         |
| Dual issue channel    | Agents → `docs/issues/`; humans → Local Todo UI (ICS read-only)                                                             |
| Discover is read-only | `find-work` does not edit                                                                                                   |
| Empty queue           | Lap-report and **stop**                                                                                                     |
| Stop-loss             | 3 identical failures → stop and surface                                                                                     |
| Protected paths       | Confirm before writing `.agents/**` etc.                                                                                    |

## State machine

```
find-work (read-only)
  → ranked Launch briefs
  → fork by work type:
       alignment (HITL / fuzzy)     → stop until proceed
       plan authoring               → docs/plans/ + issue plan: link
       implement-change             → edit → config-validate → handoff
       file-issue                   → docs/issues/ (agent channel)
       reconcile-docs / context     → after behavior/docs drift
  → operator validates live + commits
  → optional find-work again
```

Issue → plan → change (anti-rot: delete satisfied issues/plans; no `closed/`):

```
gap → (alignment if fuzzy) → file-issue (docs/issues/)
  → plan authoring (docs/plans/)
  → implement-change (one slice)
  → reconcile-docs (delete-on-ship when done)
  → operator commit
```

## Related

- [`work-sources.md`](./work-sources.md)
- [`vertical-slices.md`](./vertical-slices.md)
- [`skills/find-work/SKILL.md`](../skills/find-work/SKILL.md)
- [`skills/implement-change/SKILL.md`](../skills/implement-change/SKILL.md)
- [`docs/issues/README.md`](../../docs/issues/README.md)
- [`docs/plans/README.md`](../../docs/plans/README.md)
