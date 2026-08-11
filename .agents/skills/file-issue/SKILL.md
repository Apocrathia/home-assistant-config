---
name: file-issue
description: >-
  Create or update an agent-reported issue under docs/issues/. Use when an
  agent finds a bug, feature gap, or spec-level ask that is out of scope for
  the current lap, or when asked to file an issue. Does not create GitHub
  issues. Never writes Local Todo ICS or .shopping_list.json.
disable-model-invocation: true
---

# File issue

Record a problem or desired state under `docs/issues/`. Issues define _what_;
plans under `docs/plans/` define _how_.

**Dual channel:** agents file here. Humans report via the Home Assistant Local
Todo UI (Issues / Tasks / Ideas). Agents discover Local Todo read-only — never
write `.storage/local_todo.*.ics` or `.shopping_list.json`. See
[`.agents/context/work-sources.md`](../../context/work-sources.md) and
[`docs/issues/README.md`](../../../docs/issues/README.md).

**Checkout:** main working tree only. No git worktrees
([`worktrees.md`](../../rules/worktrees.md)). Do not commit
([`operator-owned-git.md`](../../rules/operator-owned-git.md)).

Do not open GitHub issues unless the operator explicitly asks.

## When to file

| Situation                           | File?                                                                                    |
| ----------------------------------- | ---------------------------------------------------------------------------------------- |
| Fixable in the current lap          | No — fix it                                                                              |
| Out of scope for current lap        | Yes — `docs/issues/<slug>.md`                                                            |
| Architecture friction               | Yes (`kind: architecture`); see [`architecture-review`](../architecture-review/SKILL.md) |
| Feature or spec-level desired state | **Alignment first** if acceptance unclear; then yes                                      |
| Duplicate of existing open issue    | Update existing                                                                          |
| Already on Local Todo (human)       | Prefer pointing at that item; file here only when agent-owned acceptance/plan is needed  |
| Needs human / external visibility   | File locally; ask operator about GitHub or Local Todo UI                                 |

If the gap is a feature, spec, `slice: hitl`, or **multi-path bug** and
acceptance is not yet writable, run [`alignment`](../alignment/SKILL.md)
before this skill. Paste the alignment summary into the issue body when filing.

## Workflow

```
- [ ] 0. If feature/spec/hitl/multi-path bug and acceptance is fuzzy: /alignment first; stop until operator says proceed
- [ ] 1. Search docs/issues/*.md for duplicates (skip README, _template)
- [ ] 2. Dedupe against Local Todo ICS + shopping list (read-only) — cite if human already tracked it
- [ ] 3. If duplicate in docs: update that file; skip to step 6
- [ ] 4. If no docs duplicate: copy docs/issues/_template.md → docs/issues/<short-slug>.md
- [ ] 5. Fill frontmatter and body; include **Feedback loop**; do not write the plan here
- [ ] 6. Link plan if one exists; report path to the operator (no commit)
```

Dedupe Local Todo (never write):

```bash
python3 <<'PY'
from pathlib import Path
import re

for list_name, path in [
    ("issues", ".storage/local_todo.issues.ics"),
    ("tasks", ".storage/local_todo.tasks.ics"),
    ("ideas", ".storage/local_todo.ideas.ics"),
]:
    p = Path(path)
    if not p.is_file():
        print(f"{list_name}: unavailable")
        continue
    text = p.read_text().replace("\r\n", "\n").replace("\r", "\n")
    for block in re.split(r"\nBEGIN:VTODO\n", text)[1:]:
        status = re.search(r"^STATUS:(.+)$", block, re.M)
        summary = re.search(r"^SUMMARY:(.+)$", block, re.M)
        uid = re.search(r"^UID:(.+)$", block, re.M)
        if not summary or not status or status.group(1).strip() != "NEEDS-ACTION":
            continue
        title = summary.group(1).replace("\\,", ",")
        print(f"{list_name}\t{title}\t{uid.group(1).strip() if uid else ''}")
PY
```

## Frontmatter

Required: `title`, `kind` (`bug` | `feature` | `spec` | `architecture`),
`status`, `severity` (`low` | `medium` | `high` | `blocker`), `source`,
`found_at`.

Optional: `found_by`, `area`, `slice`, `plan`, `github`, `branch`, `closed_by`.

## Closure (in the shipping change)

When acceptance is met, [`reconcile-docs`](../reconcile-docs/SKILL.md) should
fix backlinks and **delete** `docs/issues/<slug>.md` in the same change the
operator will commit. Do not leave deletion for afterward.

## Report

```markdown
## Filed

**Path:** docs/issues/<slug>.md
**Kind / severity:** …
**Local Todo overlap:** none | <list SUMMARY UID>
**Plan linked:** none | docs/plans/…
**Do not:** write Local Todo ICS / shopping-list; commit
```
