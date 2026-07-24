---
name: clock-out
description: >-
  Session wrap-up for Home Assistant Homelab: summarize what changed, what is
  still open, and suggested next steps. Does not sync main or clean up merges.
disable-model-invocation: true
---

# Clock out

Session wrap-up only. Summarize the lap and stop.

Does **not** delete branches, run `sync-main.sh`, prune Macroscope sandboxes,
or perform merge/PR cleanup. Override:
[`.agents/rules/operator-owned-git.md`](../../rules/operator-owned-git.md).

## Workflow

```
- [ ] 1. Note anything still running from this session (optional stop)
- [ ] 2. Summarize what changed
- [ ] 3. List what is still open
- [ ] 4. Suggest next steps for the operator
- [ ] 5. Stop — no new work
```

### Changed

Paths touched this session and one-line intent. Mention validation already done
and any suggested commit still pending operator action.

### Still open

Blockers, unsure review findings, live HA checks not yet done, deferred briefs.

### Next steps

Short operator list, e.g. reload automations, live-test entity X, commit when
satisfied, or re-run `find-work`. Do not start those unless asked.

## Report

```markdown
## Clock out

**Changed:** <brief>
**Open:** <brief or none>
**Suggested next:** <1–3 bullets>
**Stopped.** No git teardown performed.
```

## Do not

- `git branch -D`, `git clean`, or `sync-main`
- Commit, push, or open PRs
- Spawn follow-up implementation after the wrap
