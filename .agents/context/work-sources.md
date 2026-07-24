# Work Sources — Home Assistant Homelab

Where agents look for open work during discovery (`find-work` or any "what
should I work on?" request). Project-specific sources layered on top of the
workflow in [`skills/find-work/SKILL.md`](../skills/find-work/SKILL.md).

**This module owns the source rules.** The find-work skill owns the discovery
workflow. If they disagree, prefer this file for what/how to read sources.

## Sources

| Source                | Path                     | Access        | What it holds                         |
| --------------------- | ------------------------ | ------------- | ------------------------------------- |
| Home Assistant to-dos | `.shopping_list.json`    | **Read-only** | Tasks captured in HA's shopping list  |
| TODO markers          | `packages/**`, `docs/**` | Read-only     | `# TODO:` comments in tracked paths   |
| Docs                  | `docs/`                  | Read-only     | Documented follow-ups / project notes |

Optional (nice-to-have, never blocking): live HA via MCP (`tools.md`); GitHub
issues/PRs if available.

## `.shopping_list.json`

Home Assistant runtime state: a JSON array of `{ "name", "id", "complete" }`
objects. Gitignored, Syncthing-synced, owned by Home Assistant.

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

Shopping-list items rank as project tasks: below anything urgent (broken
automations, failing config validation) and below documented, already-scoped
work, but above speculative new ideas. Within the shopping list, order does
not imply priority — treat items as an unordered set.

## Rules

1. Discovery is read-only. No file edits, no commits
   ([`rules/operator-owned-git.md`](../rules/operator-owned-git.md)).
2. Every surfaced candidate needs a source and evidence — no vibes.
3. The operator picks what to work on; agents recommend.
4. After the operator picks, hand off to `implement-change` / `alignment` —
   do not start shipping from discovery alone.
