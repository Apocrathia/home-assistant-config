# Plan ledger — Home Assistant Homelab

In-repo living plans for multi-session **how**-work. Chat is not the plan.
Git history is the archive.

## Plans vs issues

| Surface        | Holds                                                         |
| -------------- | ------------------------------------------------------------- |
| `docs/issues/` | **What** — problem / desired state, acceptance, feedback loop |
| `docs/plans/`  | **How** — steps, checkboxes, decisions, implementation detail |

Agent-reported gaps start as [`docs/issues/`](../issues/README.md). Human
Local Todo items stay in the HA UI (read-only for agents). Do not invent
acceptance criteria here that belong on the issue.

## Layout

Flat directory — no `open/` or `closed/` folders:

```
docs/plans/
  README.md       # this file
  _template.md    # copy when authoring
  <slug>.md       # one plan per file
```

Slug is `kebab-case` and names the work, not the date. Skip `README.md` and
`_template.md` when enumerating plans.

## Status and lifecycle

Frontmatter only: `draft` | `active` | `blocked` | `done`.

Plans are **living documents**: update checkboxes and decisions as work
progresses. A stale plan is worse than no plan.

**Delete-on-ship:** when acceptance on the related issue (or the plan's own
done criteria) is met in the shipping change, delete the plan file. Do not
keep a `closed/` tree.

Agents never `git commit` — operator commits
([`operator-owned-git.md`](../../.agents/rules/operator-owned-git.md)).
Edit in the main checkout only — no worktrees
([`worktrees.md`](../../.agents/rules/worktrees.md)).

## Authoring rules

| Situation                            | Action                                                                          |
| ------------------------------------ | ------------------------------------------------------------------------------- |
| Light / obvious change               | Skip the plan doc; chat checklist is enough                                     |
| Multi-step or multi-session how-work | Copy `_template.md` → `docs/plans/<slug>.md`                                    |
| Related issue exists                 | Set `related_issue:`; keep what/how split                                       |
| Duplicate of an existing plan        | Update the existing file                                                        |
| Scope fuzzy / multiple approaches    | Run [alignment](../../.agents/skills/alignment/SKILL.md) first; plan after that |

Prefer vertical slices with a named feedback loop per checkbox — see
[`.agents/context/vertical-slices.md`](../../.agents/context/vertical-slices.md).

## Homelab constraints

- **No secrets in plan bodies.**
- Plans that imply live registry / flash / UI work still need the operator at
  execution time — planning is not authorize-to-mutate.
- Agents never write Local Todo ICS or `.shopping_list.json`.

## Frontmatter

Required: `title`, `status`, `found_at`, `updated_at`.

Optional: `related_issue`, `area`.

## Body sections

Copy from [`_template.md`](./_template.md): Goal → Scope → Decisions → Steps →
Feedback loop → Notes.

## Related

- [`_template.md`](./_template.md)
- [docs/issues/](../issues/README.md)
- [development-loop](../../.agents/context/development-loop.md)
- [implement-change](../../.agents/skills/implement-change/SKILL.md)
