---
name: reconcile-context
description: >-
  Fix drift in Home Assistant Homelab agent context (AGENTS.md, CLAUDE.md,
  .agents/context/, rules, skills, agents) against the repo. Run check_links and
  check_discovery. Use when asked to sync, reconcile, or update agent context.
disable-model-invocation: true
---

# Reconcile context

Keep the agent context true and thin. Stale context is worse than none.

**Surface:** `AGENTS.md`, `CLAUDE.md`, `.agents/context/*.md`, `.agents/rules/`,
`.agents/skills/`, `.agents/agents/`. Upstream pin: `.agents/upstream-ref`.

**HA modules (do not rename):** `constraints`, `traps`, `nomenclature`, `voice`,
`output`, `questions`, `work-sources`, `loading`, plus `README.md`. If
prime-context uses different names (invariants, pitfalls, vocabulary,
writing-style), map conceptually — never force a rename.

**Checkout:** edit in the main working tree only. No git worktrees, no branch
ceremony.

Git is operator-owned ([`operator-owned-git`](../../rules/operator-owned-git.md)):
edit after confirmation on protected paths, validate, hand off with a suggested
Conventional Commit. Do not commit, push, or open PRs.

## Workflow

```
- [ ] 1. check_links + check_discovery
- [ ] 2. Structural drift (hub, routing, loading)
- [ ] 3. Reality drift (claims vs packages/docs/skills)
- [ ] 4. Harvest <!-- drift: --> notes
- [ ] 5. Propose fixes (thin; confirm protected paths)
- [ ] 6. Re-run checks; hand off
```

### 1. Deterministic checks

```bash
python3 .agents/skills/reconcile-context/scripts/check_links.py
python3 .agents/skills/reconcile-context/scripts/check_discovery.py
```

Use `check_links.py --all` when docs or non-context markdown may have broken
links too. Fix broken links/anchors or drop dead references.

### 2. Structural drift

- **Context hub** ([`.agents/context/README.md`](../../context/README.md)): module
  table matches files on disk; skills/agents/rules lists match reality.
- **Router** ([`AGENTS.md`](../../../AGENTS.md) / `CLAUDE.md`): every routing row
  points at a real path; every context module except `README.md` appears in
  routing or loading guidance.
- **Loading** ([`loading.md`](../../context/loading.md)): named surfaces still exist.
- **Missing upstream concepts:** if prime-context has a useful module this repo
  lacks, **suggest** a structural add (new thin file + hub/routing rows). Do not
  invent content by copying upstream verbatim, and do not rename existing HA
  modules to match upstream.

### 3. Reality drift

Check claims against the repo:

- Package dirs, docs list (`docs/README.md`, `packages.md`, `projects.md`,
  `CONTRIBUTING.md`, `LICENSE.md` — no `docs/issues/`, `docs/plans/`,
  `docs/backlog/`).
- Skills/agents listed in the hub exist; work sources match
  [`work-sources.md`](../../context/work-sources.md).
- Do not overwrite project-specific prose with upstream text. Reconcile facts;
  preserve HA voice and decisions.

### 4. Drift notes

```bash
grep -rn "<!-- drift:" AGENTS.md CLAUDE.md .agents/context/ .agents/rules/
```

Act when clear; delete the comment. Leave ambiguous notes for the operator.

### 5–6. Apply, verify, hand off

Protected paths need confirmation
([`protected-paths`](../../rules/protected-paths.md)). Stay thin; link out; don't
invent decisions. Re-run both scripts. Report and suggest a commit message —
operator ships.

## Report

```markdown
## Context reconciliation

**Drift found:** <N>

- <file> — <stale> → <fixed or proposed>

**Needs judgment:** <…>
**Links:** <pass | N fixed>
**Discovery:** <pass | failures>
**Suggested commit:** <type(scope): description>
```

Clean pass: one line and stop.
