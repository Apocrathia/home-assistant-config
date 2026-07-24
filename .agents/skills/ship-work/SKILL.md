---
name: ship-work
description: >-
  Hand off completed Home Assistant Homelab work to the operator: summarize
  diffs, suggest a Conventional Commit, list validation done, and remind them
  to apply/reload HA and commit. Does not commit or push.
disable-model-invocation: true
---

# Ship work

**Handoff to operator** — not commit/push/PR. Read and summarize the main
checkout only.

This skill does **not** run `git commit`, `git push`, open PRs/MRs, create
branches, or watch PRs. Folder name `ship-work` is kept for upstream sync
identity only. Override:
[`.agents/rules/operator-owned-git.md`](../../rules/operator-owned-git.md).

Prefer a clean [`review-loop`](../review-loop/SKILL.md) first. Downstream:
[`clock-out`](../clock-out/SKILL.md) for session wrap (optional).

## Workflow

```
- [ ] 1. Summarize the working-tree diff
- [ ] 2. List validation already run
- [ ] 3. Suggest a Conventional Commit message
- [ ] 4. Remind operator: apply/reload HA → live-check → commit
- [ ] 5. Stop
```

### Diff summary

`git status` + `git diff` (staged and unstaged). Call out secrets risk, protected
paths, and packages touched under `packages/`.

### Validation already done

Cite checks from this lap (e.g. [`config-validate`](../config-validate/SKILL.md),
YAML/modern-key review, link check). If review-loop was skipped, say so.

### Suggested commit

Conventional Commits: `type(scope): description` (optional body). Examples:
`fix(packages): correct basement occupancy trigger`,
`chore(agents): shorten ship-work handoff skill`.

### Operator next

1. Apply / reload Home Assistant as needed for the change surface.
2. Validate against the live instance.
3. Commit (and push) when satisfied — **operator owns git**.

## Report

```markdown
## Ship work (handoff)

**Result:** ready for operator | blocked
**This skill did not commit or push.**

### Changed

- <path> — <one line>

### Validation

- <check + outcome>

### Suggested commit
```

<type>(<scope>): <description>

```

### Operator next
- Apply/reload HA → live validate → commit
```

## Do not

- Commit, push, merge, rebase, tag, or open PRs
- Create branches
- Run `watch-pr`, `sync-main.sh`, or overnight ship loops
- Write `.storage/` or `.shopping_list.json`
