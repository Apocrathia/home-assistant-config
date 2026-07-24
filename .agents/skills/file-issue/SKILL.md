---
name: file-issue
description: >-
  Capture out-of-scope Homelab work without inventing docs/issues/. Recommend a
  Home Assistant shopping-list item, an operator note, and/or a short entry in
  an existing docs file. Use when filing a bug, gap, or follow-up. Never write
  .shopping_list.json.
disable-model-invocation: true
---

# File issue

Name kept for upstream identity. **Behavior is HA-specific.**

This repo has no `docs/issues/`, `docs/plans/`, or issue frontmatter system. Do
not create them. Do not open GitHub issues unless the operator explicitly asks.

**Checkout:** main working tree only. No git worktrees.

Work sources: [`.agents/context/work-sources.md`](../../context/work-sources.md).

## When to file

| Situation                                        | Action                                                              |
| ------------------------------------------------ | ------------------------------------------------------------------- |
| Fixable in current work                          | Fix it — don't file                                                 |
| Out of scope / follow-up                         | File via one of the channels below                                  |
| Duplicate of open shopping-list item or doc note | Point at the existing item; don't duplicate                         |
| Acceptance fuzzy                                 | Run [`alignment`](../alignment/SKILL.md) first if needed, then file |

## Channels (pick one or more)

### (a) Shopping list (preferred for operator to-dos)

Recommend the operator add an item in the **Home Assistant shopping list UI**.

- **Never write** `.shopping_list.json` (gitignored, HA-owned runtime state).
- Give a short suggested `name` (and optional note) the operator can paste.
- Discovery later reads incomplete items read-only (see work-sources).

### (b) Operator note

Propose a concise note in chat for the operator to keep however they like
(no repo write required). Include: problem, why it matters, suggested next
step, evidence (file/entity/path).

### (c) Existing docs only

If they want something tracked in-repo, suggest a **short** addition under an
existing page (`docs/README.md`, `docs/packages.md`, `docs/projects.md`, or
`docs/CONTRIBUTING.md`) — never a new issues tree or YAML/HTML frontmatter
swarm template.

Get confirmation before editing docs. Protected agent paths stay under
[`protected-paths`](../../rules/protected-paths.md).

## Workflow

```
- [ ] 1. Confirm it's out of scope (else fix)
- [ ] 2. Dedupe against shopping list (read-only) and docs/
- [ ] 3. Choose channel(s); draft the item/note/doc blurb
- [ ] 4. Hand off — no commit; no .shopping_list.json write
```

Read incomplete shopping-list candidates (never write):

```bash
jq -r '.[] | select(.complete == false) | "\(.name) (\(.id))"' .shopping_list.json
```

If the file is missing or invalid, skip dedupe against it and say so.

## Report

```markdown
## Filed (HA)

**Channel:** shopping-list recommendation | operator note | docs blurb
**Suggested shopping-list name:** <… or n/a>
**Note / doc text:** <draft>
**Docs path (if any):** <existing file only>
**Do not:** write `.shopping_list.json`; create `docs/issues/`
```
