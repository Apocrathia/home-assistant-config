# Issue ledger — Home Assistant Homelab

In-repo backlog for **agent-reported** gaps, bugs, and desired state. Chat is
not the backlog. Git history is the archive.

## Dual channel

| Channel                | Who files        | Where                       | Agents may write?               |
| ---------------------- | ---------------- | --------------------------- | ------------------------------- |
| **Local Todo (HA UI)** | Humans           | `.storage/local_todo.*.ics` | **Never** — read-only discovery |
| **Docs ledger**        | Agents (default) | `docs/issues/*.md`          | Yes — this directory            |

Human-reported work stays in the Home Assistant Local Todo UI (Issues / Tasks /
Ideas). Agents discover those read-only via
[`.agents/context/work-sources.md`](../../.agents/context/work-sources.md).
Agents file **here** by default. Do not invent GitHub issues unless the
operator asks.

## Layout

Flat directory — no `open/` or `closed/` folders:

```
docs/issues/
  README.md       # this file
  _template.md    # copy when filing
  <slug>.md       # one issue per file
```

Slug is `kebab-case` and names the gap, not the date
(e.g. `closet-motion-false-triggers.md`).

## Issues vs plans

| Surface        | Holds                                                         |
| -------------- | ------------------------------------------------------------- |
| `docs/issues/` | **What** — problem / desired state, acceptance, feedback loop |
| `docs/plans/`  | **How** — steps, checkboxes, implementation detail            |

Plans live under [`docs/plans/`](../plans/README.md). Do not bury a full plan
inside an issue — link it via optional `plan:` frontmatter.

## Status and lifecycle

Status lives in YAML frontmatter only (`open` | `in-flight` | `blocked` |
`closed` | `wontfix` | `superseded` | `promoted`).

**Delete-on-ship:** when acceptance is met in the same change that ships the
fix, delete the issue file (and fix plan backlinks). Do not keep a `closed/`
tree. Git history is the archive. Optional `closed_by:` (commit SHA) is fine
while the file still exists during review.

Agents never `git commit` — operator commits
([`operator-owned-git.md`](../../.agents/rules/operator-owned-git.md)).
Edit in the main checkout only — no worktrees
([`worktrees.md`](../../.agents/rules/worktrees.md)).

## Filing rules

| Situation                               | Action                                                                                          |
| --------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Fixable in the current lap              | Fix it; do not file                                                                             |
| Real gap, not fixing now                | File from `_template.md` via [`file-issue`](../../.agents/skills/file-issue/SKILL.md)           |
| Duplicate of an existing open issue     | Update the existing file                                                                        |
| Human already tracked it in Local Todo  | Point at the ICS item; do not duplicate unless promoting agent-owned acceptance/plan work       |
| Scope fuzzy / multiple valid approaches | Run [alignment](../../.agents/skills/alignment/SKILL.md) first; file after shared understanding |

## Homelab constraints

- **No secrets in issue bodies.** Reference `!secret` names / 1Password items
  only.
- Filing does not authorize live HA mutate beyond normal edit rules — registry,
  Lovelace `.storage`, and ESPHome flash stay operator-owned unless asked.
- Never write `.storage/local_todo.*.ics` or `.shopping_list.json`.

## Frontmatter

Required:

| Field      | Values                                                                                        |
| ---------- | --------------------------------------------------------------------------------------------- |
| `title`    | Short human title                                                                             |
| `kind`     | `bug` \| `feature` \| `spec` \| `architecture`                                                |
| `status`   | `open` \| `in-flight` \| `blocked` \| `closed` \| `wontfix` \| `superseded` \| `promoted`     |
| `severity` | `low` \| `medium` \| `high` \| `blocker`                                                      |
| `source`   | `agent` \| `human` \| `dogfood` \| `review` \| `architecture-review` \| `ha-mcp` \| `grafana` |
| `found_at` | `YYYY-MM-DD`                                                                                  |

Optional: `found_by`, `area`, `slice` (`afk` \| `hitl`), `plan`, `github`,
`branch`, `closed_by`.

## Body sections

Copy from [`_template.md`](./_template.md): Problem / desired state → Repro →
Acceptance → Feedback loop → Implementation hint → Notes.

## Related

- [file-issue](../../.agents/skills/file-issue/SKILL.md)
- [alignment](../../.agents/skills/alignment/SKILL.md)
- [docs/plans/](../plans/README.md)
- [work-sources](../../.agents/context/work-sources.md)
