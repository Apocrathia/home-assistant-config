---
description: Merging a PR needs explicit authorization from the operator; never merge, approve, or push to main on your own
alwaysApply: true
---

# Merge authorization

Merging is the operator's action. An open PR with green CI and clean reviews is
a report to the operator, not a step the agent finishes. Agents have merged PRs
unasked; this rule is the correction. Extends
[`operator-owned-git.md`](./operator-owned-git.md) — the umbrella that bans
commits, pushes, and PRs here; this rule widens that ban to the merge/approve
family.

## Never without explicit authorization

- `gh pr merge` in any mode (`--merge`, `--squash`, `--rebase`, `--auto`) or
  the forge web/API equivalent, including merge-queue enqueue
- Approving a PR, or dismissing a submitted review to clear a review decision
- Pushing to `main` (or any protected branch), or merging a branch you are
  shipping into it, local or remote
- Running a command that would merge a branch you are shipping into `main`
  (or any protected branch) as a probe, even guarded with `|| true` or
  expecting rejection: if that command merges on success, running it is a
  merge attempt

## What does not authorize a merge

- CI green, `mergeStateStatus: CLEAN`, reviewers clean, merge-ready
- A plan, launch brief, issue, or skill whose exit is a "merged PR"
- "Ship it", "land it", "finish the lap": shipping ends at a report — a
  handoff with a suggested commit message here, an open PR where the operator
  delegates git
- Silence, elapsed time, or the operator being away

Only the operator naming the merge in the session ("merge #72") authorizes it.
Then do exactly that, nothing broader.

## Still the agent's job

Where the operator delegates git (upstream's default), pushing the feature
branch, opening and updating the PR, syncing that branch, replying to and
resolving review threads you addressed, and read-only state queries
(`gh pr view`, `gh pr checks`) stay the agent's job — merging and approving
never are. Here the umbrella stops the agent earlier still: validated edits
plus a suggested commit message. Read-only queries (`git log`, `git show`,
`git diff`, `gh pr view`) remain fine everywhere.

At merge-ready, report and stop. The operator merges or dismisses; do not
watch, poll, or nudge for the merge.

## Related

- Hard limits: [`.agents/context/constraints.md`](../context/constraints.md)
- Skills that stop at merge-ready:
  [`ship-work`](../skills/ship-work/SKILL.md),
  [`autoresearch`](../skills/autoresearch/SKILL.md)
