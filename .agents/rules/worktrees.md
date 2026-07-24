---
description: Edit in the main checkout only. Never create git worktrees.
alwaysApply: true
---

# No worktrees

This Home Assistant config repo is a single checkout. Agents edit files **in the
main working tree**. Git worktrees are overkill here and fight
[`operator-owned-git.md`](./operator-owned-git.md).

## Never

- `git worktree add`, `git worktree remove`, or any other `git worktree` mutation
- Create directories under `.worktrees/`
- Follow upstream skills that require a worktree before edits (`implement-change`,
  `ship-work`, `clock-out`, `reconcile-docs`, `file-issue`, etc.)

## Instead

1. Edit in the current checkout (workspace root).
2. Validate (see [`skills/config-validate/SKILL.md`](../skills/config-validate/SKILL.md)).
3. Hand off for commit per [`operator-owned-git.md`](./operator-owned-git.md).

If an upstream skill or synced template says "open a worktree first," ignore that
step. This file is the local override so a future upstream sync cannot silently
reintroduce mandatory worktree ceremony without conflicting with this rule.
