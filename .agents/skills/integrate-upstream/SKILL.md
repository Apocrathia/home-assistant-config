---
name: integrate-upstream
description: >-
  Pull changes from the prime-context core into Home Assistant Homelab's
  .agents/ tree — diff shared rules, skills, and scripts, reconcile layer 1 and
  2 changes, and preserve project-specific content. Use when the user says sync
  upstream, integrate upstream changes, pull updates from the core, or update
  .agents/ from prime-context.
disable-model-invocation: true
---

# Integrate upstream — Home Assistant Homelab

This repo's `.agents/` is built from the
[prime-context](https://github.com/PrimeIntellect-ai/prime-context) core. The
core evolves — new rules, improved skills, better scripts, new templates. This
skill pulls those upstream changes in while preserving Homelab-specific content
(layer 3).

**Apply in the main checkout after operator confirmation.** This repo does not
use git worktrees. Do not create a `chore/integrate-upstream` branch or
worktree. Git is operator-owned
([`operator-owned-git.md`](../../rules/operator-owned-git.md)) — propose, apply
on confirm, update the pin, validate, hand off. No commits, pushes, or PRs.

Three layers:

| Layer                | What                                       | How this skill handles it                   |
| -------------------- | ------------------------------------------ | ------------------------------------------- |
| 1 — Generic          | Rules, byte-identical skills, scripts      | Direct diff; copy or reconcile              |
| 2 — Templatized      | Skills with `{{project_name}}` tokens      | Diff after token normalization; reconcile   |
| 3 — Project-specific | Context modules, HA agents/skills, routing | **Do not overwrite.** Structural check only |

## When to run

- Operator says sync upstream, update from the core, pull prime-context, or
  integrate upstream
- After the core ships changes that affect shared rules/skills/scripts
- Before a [`reconcile-context`](../reconcile-context/SKILL.md) pass when shared
  files may be stale

## Defaults for this project

| Input                  | Default                                                         |
| ---------------------- | --------------------------------------------------------------- |
| **Upstream core path** | `/Users/ianyoung/Projects/prime-context` (ask if missing/wrong) |
| **Project name**       | `Home Assistant Homelab` (for `{{project_name}}` substitution)  |
| **Baseline pin**       | [`.agents/upstream-ref`](../../upstream-ref) — SHA of last sync |
| **Checkout**           | Main workspace only — no worktree                               |

All `.agents/**` paths are protected — surface the full change set before
writing ([`protected-paths.md`](../../rules/protected-paths.md)).

## Workflow

```
- [ ] 1. Locate and load the upstream core
- [ ] 2. Read baseline from .agents/upstream-ref
- [ ] 3. Inventory this project's .agents/
- [ ] 4. Categorize files by layer
- [ ] 5. Diff each layer (token-normalize layer 2)
- [ ] 6. Categorize changes + reconcile modified files
- [ ] 7. Surface the change set — STOP for operator confirmation
- [ ] 8. Apply in the main checkout after confirmation
- [ ] 9. Update .agents/upstream-ref to the upstream HEAD SHA
- [ ] 10. Run link + discovery checks
- [ ] 11. Report and hand off (operator commits)
```

### 1. Locate and load the upstream core

```bash
upstream="/Users/ianyoung/Projects/prime-context"
# Or operator-supplied path / temp clone of a remote
```

Verify the upstream looks like the core: top-level `rules/`, `skills/`,
`templates/` (or `.agents/` equivalents depending on core layout). If the
structure does not match, stop and ask.

```bash
upstream_rev=$(git -C "$upstream" rev-parse HEAD)
echo "Upstream revision: $upstream_rev"
```

### 2. Baseline from upstream-ref

```bash
baseline_rev=$(cat .agents/upstream-ref 2>/dev/null || echo "")
```

If missing or unknown, ask the operator or degrade to a 2-way diff and flag
that in the change set.

### 3. Inventory this project's `.agents/`

```bash
agents_dir="$(git rev-parse --show-toplevel)/.agents"
find "$agents_dir/rules" -name '*.md' 2>/dev/null | sort
find "$agents_dir/skills" -name 'SKILL.md' 2>/dev/null | sort
find "$agents_dir/skills" -path '*/scripts/*.py' 2>/dev/null | sort
find "$agents_dir/context" -name '*.md' 2>/dev/null | sort
find "$agents_dir/agents" -name '*.md' 2>/dev/null | sort
```

Record the full file list, including agent personas (`.agents/agents/`).
Check that Homelab has personas (or documented role mappings in
[`subagents.md`](../../rules/subagents.md)) for roles shared skills invoke
(`/implementer`, `/reviewer`, `/verifier`, plus any HA domain agents).

**Leave alone (layer 3 / HA-native):** context modules tailored to Homelab,
HA agents, and domain skills `automation-debug`, `config-validate`,
`package-organize`, plus any Homelab-only rules (e.g. operator-owned-git,
work-sources).

### 4–6. Layer, diff, reconcile

Discover upstream files dynamically — do not hardcode skill names.

| Layer                       | Upstream source                             | Local                                 | Action                                                   |
| --------------------------- | ------------------------------------------- | ------------------------------------- | -------------------------------------------------------- |
| 1 — Rules                   | `rules/*.md`                                | `.agents/rules/*.md`                  | Direct diff                                              |
| 1 — Byte-identical skills   | `skills/<name>/SKILL.md` (no project token) | `.agents/skills/<name>/SKILL.md`      | Direct diff                                              |
| 1 — Scripts                 | `skills/reconcile-context/scripts/*.py`     | same under `.agents/`                 | Direct diff                                              |
| 2 — Templatized skills      | skills with `{{project_name}}`              | local skill                           | Diff after replacing token with `Home Assistant Homelab` |
| 3 — Context / root / refs   | `templates/**`                              | `.agents/context/`, `AGENTS.md`, etc. | Structural suggestions only — never overwrite            |
| 3 — Agent persona templates | `templates/agents/*.tmpl`                   | `.agents/agents/*.md`                 | Structural only — verify role coverage in `subagents.md` |

For modified files, 3-way when baseline is known:

1. What changed upstream: `git -C "$upstream" diff <baseline_rev>..HEAD -- <file>`
2. What changed locally beyond project-name substitution
3. Decide: clean apply | conflict (propose merge) | local improvement (consider contributing back via [`retrospective`](../retrospective/SKILL.md))

Categories: unchanged | added upstream | modified | removed upstream | project-specific.

### 7. Surface the change set (required gate)

Present the full change set **before writing anything**.

```markdown
## Upstream integration — proposed changes

**Upstream core:** <path>
**Upstream HEAD:** <sha>
**Baseline (upstream-ref):** <sha or unknown>
**Project name:** Home Assistant Homelab
**Apply target:** main checkout (no worktree)

### Clean applies (replace)

- …

### Needs reconciliation (conflict)

- … — Proposed: … **Review before applying.**

### New files (copy)

- …

### Removed upstream

- … — Remove locally?

### Structural suggestions (layer 3 — not applied)

- …

### Skip (unchanged)

N files

### Local improvements (consider contributing back)

- …

Confirm to apply? (yes / adjust / abort)
```

### 8. Apply after confirmation

Only after explicit operator confirmation:

1. Copy new files (token-replace layer 2).
2. Replace clean-apply files.
3. Apply agreed reconciliations.
4. Handle removals per operator decision.
5. Do **not** overwrite layer 3 / HA-native skills.

### 9. Update the pin

```bash
git -C "$upstream" rev-parse HEAD > .agents/upstream-ref
```

Include `upstream-ref` in the handoff so the operator commits it with the sync.

### 10. Checks

```bash
python3 .agents/skills/reconcile-context/scripts/check_links.py
python3 .agents/skills/reconcile-context/scripts/check_discovery.py
```

If a script is missing locally and exists upstream, include copying it in the
confirmed change set (layer 1). Note pass/fail in the report.

### 11. Report and hand off

```markdown
## Upstream integration

**Upstream:** <path> @ <sha>
**Baseline was:** <old sha>
**Result:** <N clean applies, N reconciled, N new, N removed>

### Changes applied

- …

### Structural suggestions (not applied)

- …

### Local improvements to contribute back

- …

### Checks

- link: <pass | N issues>
- discovery: <pass | N issues>

### Next

- Operator validates and commits (suggested message below)
- Do **not** open a PR or create a branch from this skill
```

Suggest a Conventional Commit message, e.g.
`chore(agents): sync .agents from prime-context (<short-sha>)`.

A clean pass with nothing to change is valid — say so, still confirm whether
to bump `upstream-ref` if HEAD moved with no file deltas.

## Do not

- Create worktrees or `chore/integrate-upstream` branches
- Apply changes without operator confirmation
- Overwrite layer 3 / HA-native skills and Homelab context
- Commit, push, or open PRs — hand off to the operator
- Skip link/discovery checks after writes
- Assume the upstream path without verifying structure
- Blindly take either side of a conflict — propose the merge first
