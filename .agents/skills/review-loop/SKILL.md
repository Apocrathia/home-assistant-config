---
name: review-loop
description: >-
  Pre-handoff quality gate for Home Assistant YAML, docs, and agent context.
  Lint, validate, and smoke-check the working-tree diff. Use before handing
  changes to the operator.
disable-model-invocation: true
---

# Review loop

Pre-handoff quality gate — **not** build+test+PR. Run in the main checkout:
inspect the uncommitted (or named) diff, fix valid issues, re-check, then stop
for the operator.

Does **not** commit, push, open PRs, or run Macroscope/Bugbot/Codex/cargo
swarm loops. Override:
[`.agents/rules/operator-owned-git.md`](../../rules/operator-owned-git.md).

Upstream of [`ship-work`](../ship-work/SKILL.md) (handoff). No `watch-pr`.

## Checks

Pick what matches the touched files:

| Touch                                            | Check                                                                           |
| ------------------------------------------------ | ------------------------------------------------------------------------------- |
| `packages/**`, `configuration.yaml`, automations | [`config-validate`](../config-validate/SKILL.md)                                |
| Package structure                                | [`package-organize`](../package-organize/SKILL.md) patterns                     |
| Broken automation behavior                       | [`automation-debug`](../automation-debug/SKILL.md)                              |
| `.agents/` / docs links                          | `python3 .agents/skills/reconcile-context/scripts/check_links.py` when relevant |
| Secrets                                          | no hardcoded credentials; `!secret` only                                        |

Also: YAML 2-space; modern automation keys (`triggers` / `conditions` /
`actions`); entity/device/area refs look sane; no edits to `.storage/` or
`.shopping_list.json`.

Protected paths: confirm before fixing
([`.agents/rules/protected-paths.md`](../../rules/protected-paths.md)).

## Workflow

```
- [ ] 1. Diff scope (uncommitted default)
- [ ] 2. Run matching checks
- [ ] 3. Triage findings: valid / wrong / unsure
- [ ] 4. Fix valid findings (minimal); re-check
- [ ] 5. Report; hand off — no commit
```

Cap at a few fix iterations. If blocked (protected path, unsure finding, check
failure), stop and surface it.

## Report

```markdown
## Review loop

**Scope:** uncommitted | named paths
**Result:** clean | blocked

### Checks

- <command or skill + outcome>

### Fixes

- <path> — <what changed>

### Left open

- <finding or blocker>

### Next

- [`ship-work`](../ship-work/SKILL.md) handoff when the operator wants a wrap
```
