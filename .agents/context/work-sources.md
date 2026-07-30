# Work Sources — Home Assistant Homelab

Where agents look for open work during discovery (`find-work` or any "what
should I work on?" request). Project-specific sources layered on top of the
workflow in [`skills/find-work/SKILL.md`](../skills/find-work/SKILL.md).

**This module owns the source rules.** The find-work skill owns the discovery
workflow. If they disagree, prefer this file for what/how to read sources.

## Sources

| Source                 | Path                             | Access        | What it holds                                                |
| ---------------------- | -------------------------------- | ------------- | ------------------------------------------------------------ |
| Local Todo — Issues    | `.storage/local_todo.issues.ics` | **Read-only** | Confirmed problems / broken behavior (preferred bug channel) |
| Local Todo — Tasks     | `.storage/local_todo.tasks.ics`  | **Read-only** | Scoped HA work items                                         |
| Local Todo — Ideas     | `.storage/local_todo.ideas.ics`  | **Read-only** | Speculative / nice-to-have ideas                             |
| Shopping list (legacy) | `.shopping_list.json`            | **Read-only** | Older HA shopping-list to-dos (still in use)                 |
| TODO markers           | `packages/**`, `docs/**`         | Read-only     | `# TODO:` comments in tracked paths                          |
| Docs                   | `docs/`                          | Read-only     | Documented follow-ups / project notes                        |

Optional (nice-to-have, never blocking): live HA via MCP (`tools.md`); GitHub
issues/PRs if available. Prefer the ICS files over MCP for list discovery —
MCP may only expose a subset of lists.

## Local Todo (`.storage/local_todo.*.ics`)

Home Assistant **Local To-do** lists, stored as iCalendar `VTODO` calendars
under `.storage/`. Owned by Home Assistant; Syncthing-synced with the rest of
runtime state.

| List   | File                             | Role in discovery                                               |
| ------ | -------------------------------- | --------------------------------------------------------------- |
| Issues | `.storage/local_todo.issues.ics` | Highest-priority HA backlog (bugs / breaks); file new bugs here |
| Tasks  | `.storage/local_todo.tasks.ics`  | Active project work                                             |
| Ideas  | `.storage/local_todo.ideas.ics`  | Speculative / future ideas                                      |

Rules:

1. **Never write these files.** Completion and edits happen in the Home
   Assistant To-do UI (or MCP mutations only when the operator explicitly
   asks). Do not mark complete, add, delete, or reformat ICS.
2. **Surface only `STATUS:NEEDS-ACTION`** items as work candidates. Ignore
   `COMPLETED` (and any other status).
3. Cite each candidate with its **list name**, `SUMMARY` (title), and `UID`
   (evidence).
4. Vague titles route to scoping/`alignment` first — do not implement from a
   five-word title alone.
5. Failure is non-fatal: if a file is missing or unreadable, note
   `"local_todo <list> unavailable"` and continue. Skip `VTODO` blocks without
   a `SUMMARY`.

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

## `.shopping_list.json`

Legacy Home Assistant shopping-list runtime state: a JSON array of
`{ "name", "id", "complete" }` objects. Gitignored, Syncthing-synced, owned by
Home Assistant. Still a valid work source; not the same store as Local Todo.

Rules:

1. **Never write to this file.** Completion state is managed in Home Assistant.
   Do not mark items complete, add items, or reformat it.
2. **Surface only `"complete": false` items** as work candidates.
3. Cite each candidate with its `name` (title) and `id` (evidence).
4. Vague items (e.g. "Reminders to water plants") route to scoping/`alignment`
   first — do not implement autonomously from a five-word title.
5. Failure is non-fatal: if the file is missing, empty, not valid JSON, or not
   an array, skip the source, note "shopping list unavailable" in the report,
   and continue with other sources. Skip entries missing a `name`.

```bash
jq -r '.[] | select(.complete == false) | "\(.name) (\(.id))"' .shopping_list.json
```

## Ranking

Apply tiers in order. Within a tier (and within a single list), order does
**not** imply priority — treat items as an unordered set.

| Tier | What                                                               |
| ---- | ------------------------------------------------------------------ |
| 1    | Broken / urgent config or automation issues; open **Issues** items |
| 2    | Documented, already-scoped work in `docs/`                         |
| 3    | Open **Tasks** items; incomplete shopping-list items               |
| 4    | `# TODO:` markers                                                  |
| 5    | Open **Ideas** items; other speculative / nice-to-have             |

Dedupe: same outcome from two sources → one backlog row, cite both sources.

## Rules

1. Discovery is read-only. No file edits, no commits
   ([`rules/operator-owned-git.md`](../rules/operator-owned-git.md)).
2. Every surfaced candidate needs a source and evidence — no vibes.
3. The operator picks what to work on; agents recommend.
4. After the operator picks, hand off to `implement-change` / `alignment` —
   do not start shipping from discovery alone.
