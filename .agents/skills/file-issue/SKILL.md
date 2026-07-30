---
name: file-issue
description: >-
  Capture out-of-scope Homelab work without inventing docs/issues/. Recommend a
  Home Assistant Local Todo Issues item (preferred for bugs), Tasks/Ideas when
  appropriate, an operator note, and/or a short entry in an existing docs file.
  Never write .storage/local_todo.*.ics or .shopping_list.json.
disable-model-invocation: true
---

# File issue

Name kept for upstream identity. **Behavior is HA-specific.**

This repo has no `docs/issues/`, `docs/plans/`, or issue frontmatter system. Do
not create them. Do not open GitHub issues unless the operator explicitly asks.

**Checkout:** main working tree only. No git worktrees.

Work sources: [`.agents/context/work-sources.md`](../../context/work-sources.md).

## When to file

| Situation                                     | Action                                                              |
| --------------------------------------------- | ------------------------------------------------------------------- |
| Fixable in current work                       | Fix it — don't file                                                 |
| Out of scope / follow-up                      | File via one of the channels below                                  |
| Duplicate of open local_todo or shopping item | Point at the existing item; don't duplicate                         |
| Acceptance fuzzy                              | Run [`alignment`](../alignment/SKILL.md) first if needed, then file |

## Channels (pick one or more)

### (a) Local Todo — Issues (preferred for bugs / broken behavior)

Recommend the operator add an item in the **Home Assistant Issues** Local Todo
list UI.

- **Never write** `.storage/local_todo.issues.ics` (HA-owned runtime state).
- Give a short suggested `SUMMARY` (and optional DESCRIPTION) the operator can
  paste.
- Discovery later reads `STATUS:NEEDS-ACTION` items read-only (see
  work-sources).

Use **Tasks** for scoped project work and **Ideas** for speculative / nice-to-
have — same read-only rule for their ICS files.

### (b) Shopping list (legacy)

Only when the operator prefers the legacy shopping-list UI, or the item is a
non-HA chore already tracked there.

- **Never write** `.shopping_list.json`.
- Give a short suggested `name` (and optional note).

### (c) Operator note

Propose a concise note in chat for the operator to keep however they like
(no repo write required). Include: problem, why it matters, suggested next
step, evidence (file/entity/path).

### (d) Existing docs only

If they want something tracked in-repo, suggest a **short** addition under an
existing page (`docs/README.md`, `docs/packages.md`, `docs/projects.md`, or
`docs/CONTRIBUTING.md`) — never a new issues tree or YAML/HTML frontmatter
swarm template.

Get confirmation before editing docs. Protected agent paths stay under
[`protected-paths`](../../rules/protected-paths.md).

## Workflow

```
- [ ] 1. Confirm it's out of scope (else fix)
- [ ] 2. Dedupe against local_todo ICS + shopping list (read-only) and docs/
- [ ] 3. Choose channel(s); draft the item/note/doc blurb
- [ ] 4. Hand off — no commit; no local_todo / shopping-list write
```

Dedupe against Local Todo (never write):

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

Legacy shopping list (never write):

```bash
jq -r '.[] | select(.complete == false) | "\(.name) (\(.id))"' .shopping_list.json
```

If a source is missing or invalid, skip dedupe against it and say so.

## Report

```markdown
## Filed (HA)

**Channel:** local_todo Issues | Tasks | Ideas | shopping-list | operator note | docs blurb
**Suggested title:** <SUMMARY / shopping name / n/a>
**Note / description:** <draft>
**Docs path (if any):** <existing file only>
**Do not:** write `.storage/local_todo.*.ics` or `.shopping_list.json`; create `docs/issues/`
```
