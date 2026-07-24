---
description: Git operations and Home Assistant runtime state are operator-owned. Agents never commit, push, or open PRs.
alwaysApply: true
---

# Operator-owned git

This repository's git lifecycle belongs to the operator. This rule **overrides**
any upstream skill that commits, pushes, opens PRs, creates worktrees, or loops
autonomously through shipping (`ship-work`, `self-improve`, `clock-out`,
`watch-pr`, `file-issue` commit steps, etc.).

Sibling rule: [`worktrees.md`](./worktrees.md) — no worktrees; edit in the main
checkout only.

## Never

- `git commit`, `git push`, `git merge`, `git rebase`, tag, or open PRs/MRs
- Create branches or worktrees (see [`worktrees.md`](./worktrees.md))
- Write to `.storage/`, `.shopping_list.json`, or any HA-managed runtime state

## Instead

1. Make the requested changes in the working tree (main checkout).
2. Validate (YAML check, link check — see
   [`skills/config-validate/SKILL.md`](../skills/config-validate/SKILL.md)).
3. Stop and hand off: summarize what changed and suggest a Conventional Commit
   message (`type(scope): description`). The operator commits after the change
   is validated against the live system.

## Why

Changes here are applied to a running Home Assistant instance and validated
live before they are committed. Committing unvalidated config would put broken
state in history and desync git from the HA reality the operator maintains.
