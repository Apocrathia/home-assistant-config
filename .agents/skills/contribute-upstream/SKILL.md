---
name: contribute-upstream
description: >-
  Push improvements from Home Assistant Homelab's .agents/ tree back to the
  context-engine core — diff shared rules, skills, and scripts against the core,
  isolate the local delta, extract generic changes, restore {{project_name}}
  tokens, validate, and hand off for the operator to open the PR. Use when the
  user says contribute upstream, port back to the core, push this improvement
  upstream, or after a retrospective flags an upstream candidate.
disable-model-invocation: true
---

# Contribute upstream — Home Assistant Homelab

The **push** counterpart to
[`integrate-upstream`](../integrate-upstream/SKILL.md): Homelab improved a
shared rule, skill, or script, and this skill ports that improvement back into
the context-engine core.
[`retrospective`](../retrospective/SKILL.md) classifies upstream candidates;
this skill is the executor.

**Git is operator-owned on both repos**
([`operator-owned-git.md`](../../rules/operator-owned-git.md)). This skill is
read-only until the operator confirms the change set; then it ports the deltas
as uncommitted edits in the core's **main checkout** and hands off — suggested
branch name, Conventional Commit message, and PR body. No worktrees
([`worktrees.md`](../../rules/worktrees.md)), no commits, pushes, or PRs,
including on the core. Scratch artifacts go under the core's `.scratch/`.

## When to run

- Operator says contribute upstream, port back to the core, upstream this.
- A [`retrospective`](../retrospective/SKILL.md) report lists an upstream
  candidate.
- [`integrate-upstream`](../integrate-upstream/SKILL.md) surfaced a "local
  improvements (contribute back)" item.

## Defaults for this project

| Input              | Default                                                                          |
| ------------------ | -------------------------------------------------------------------------------- |
| Upstream core path | operator's local core checkout — ask the operator (path stays out of repo files) |
| Project name       | `Home Assistant Homelab` (the `{{project_name}}` substitution)                   |
| Baseline pin       | [`.agents/upstream-ref`](../../upstream-ref) — SHA of last sync                  |
| Port target        | Core main checkout, uncommitted edits — operator commits                         |

## Direction and layer map

The consuming project is the **source**; the core's top-level directories are
the **target**. Direction is the reverse of `integrate-upstream`.

| Layer           | Source (Homelab)                          | Target (core)            | Port rule                                                                                 |
| --------------- | ----------------------------------------- | ------------------------ | ----------------------------------------------------------------------------------------- |
| 1 — Rules       | `.agents/rules/*.md`                      | `rules/*.md`             | Diff; port only generic deltas                                                            |
| 1 — Skills      | `.agents/skills/<name>/**`                | `skills/<name>/**`       | Direct diff; port real deltas                                                             |
| 2 — Templatized | skills with `{{project_name}}` tokens     | `skills/<name>/SKILL.md` | Diff after substitution; restore tokens                                                   |
| 3 — Rendered    | `.agents/context/*.md`, `.agents/agents/` | `templates/**`           | **Not a file diff** — author a generic template in the core, never copy the rendered file |

## Workflow

```
- [ ] 1. Resolve and verify the core + baseline
- [ ] 2. Pin $base to the canonical core main
- [ ] 3. Inventory Homelab's .agents/
- [ ] 4. Diff each layer (token-normalized layer 2)
- [ ] 5. Isolate the local delta (3-way against baseline)
- [ ] 6. Apply the genericness gate
- [ ] 7. Surface the change set — STOP for operator confirmation
- [ ] 8. Port into the core main checkout
- [ ] 9. Validate the ported files
- [ ] 10. Hand off (operator branches, commits, pushes, opens the PR)
```

### 1. Resolve core + baseline

Verify the core by structure: top-level `rules/`, `skills/`, `templates/`.
The baseline must be an **upstream** commit-ish that exists in the core — read
`.agents/upstream-ref` `sha` (or map `version` to tag `v${version}`) and confirm
`git -C "$upstream" cat-file -e "${sha}^{commit}"`. Without a resolvable
baseline, **stop** — a consumer-vs-HEAD 2-way diff cannot tell a local
improvement from stale core text. Never pass a consumer SHA to `git -C
"$upstream"`.

### 2. Pin `$base` to the canonical core main

Diff against the canonical remote's `main`
(the canonical origin), not a stale checkout or fork. Fetch, then
check `git merge-base --is-ancestor main "$canonical/main"` — diverged local
main means stop and ask. Require `$baseline` to be an ancestor of `$base`; a
pin from a feature branch or rewritten history is the wrong common side.
Record `$analyzed_base=$(git rev-parse "$base")` and re-verify it still matches
before porting — if the tip moved, re-run isolation and confirmation.

### 3. Inventory Homelab's `.agents/`

`git ls-files --cached --others --exclude-standard` over `.agents/rules` and
`.agents/skills` — tracked plus legitimate untracked source; skip gitignored
and generated files (`__pycache__/*.pyc`). A file with no core counterpart is
**new** — new generic rules/skills are exactly what should be contributed; the
genericness gate sorts them. After the baseline resolves, union with shared
paths at `$baseline`/`$base`: a missing layer 1/2 path Homelab previously
installed is a deletion candidate, not an omission.

### 4. Diff each layer

- Layer 1: consumer file vs `git -C "$upstream" show "$base:<file>"` — every
  difference is a candidate.
- Layer 2: substitute `{{project_name}}` in the `$base` version with
  `Home Assistant Homelab`, then diff. Token-substitution-only difference =
  aligned, skip. Derive the live templatized list from
  `git -C "$upstream" show "$base:AGENTS.md"`, not the working tree.
- Record diffs; do not port yet.

### 5. Isolate the local delta (3-way)

The anti-revert step. For each modified file:

1. **Local delta:** consumer vs `git -C "$upstream" show "<baseline>:<file>"`
   (token-normalized for layer 2).
2. **Core drift:** `git -C "$upstream" diff <baseline>.."$base" -- <file>`.
3. Decide: **clean local delta** → port onto `$base` · **conflict** (core moved
   the same lines) → merge manually, keep core's newer change plus the local
   improvement, surface the resolution · **already upstream** → skip ·
   **stale-only** (consumer differs only by being behind) → skip, that is
   drift to pull · **post-pin file** (absent at baseline, present on `$base`)
   → port only consumer-unique hunks, never copy the consumer file over
   `$base` · **new file** → port via the gate · **deletion candidate** →
   confirm before surfacing; do not silently `git rm` newer core.

### 6. Genericness gate

| Test                                                                          | Result                          |
| ----------------------------------------------------------------------------- | ------------------------------- |
| References Homelab/HA-specific infrastructure, domain logic, conventions?     | Stays local                     |
| Generic (works in at least two source projects — operator confirms evidence)? | Port                            |
| Layer 1/2 change, or a generic edit authored in core `templates/`?            | Port                            |
| Rendered layer-3 file copied as-is?                                           | Stays local (author a template) |
| Project name in new prose (not a `{{project_name}}` position)?                | Rewrite generically or drop     |

A real improvement that cannot yet be written generically becomes an issue
draft, not a PR — say why in the report.

### 7. Surface the change set (required gate)

All steering surfaces are protected — present every path before writing
([`protected-paths.md`](../../rules/protected-paths.md)):

```markdown
## Upstream contribution — proposed change set

**Core:** <path> @ $base
**Baseline (upstream-ref):** <sha>
**Evidence:** applies to <source project A> and <source project B>
**Port target:** core main checkout, uncommitted edits

### Porting — <suggested branch: <type>/contribute-<slug>>

- `skills/<name>/SKILL.md` — <delta summary; tokens restored>

### Reconciles (core also changed since baseline)

- `rules/<name>.md` — took core's newer section, re-applied local wording

### New files / Deletions / Local-only (stayed in Homelab)

- …

Confirm to port? (yes / adjust / abort)
```

### 8. Port into the core main checkout

After confirmation, apply each approved delta as an **uncommitted edit** in the
core's main checkout — no branch, no worktree. Port deltas onto `$base` text;
restore `{{project_name}}` where the core uses it; write genuinely new prose
generically. A new shared skill also needs its companion rows (core
`AGENTS.md`/`README.md` lists and counts, `templates/rules-README.md.tmpl`,
inventory/scaffold guides) — include those in the change set.

### 9. Validate

```bash
cd "$upstream"
# Unittests in every core skills scripts dir with a suite
for d in skills/*/scripts; do ls "$d"/test_*.py >/dev/null 2>&1 && (cd "$d" && python3 -m unittest discover -p 'test_*.py'); done
# Link check: new breakage only — capture the BROKEN set before porting and after
python3 skills/reconcile-context/scripts/check_links.py --all  # before, then after; diff the BROKEN lines
# Consumer-layout noise filter + deployed-link remap for the confirmed paths
CONSUMER_ROOT="<homelab root>" BASE="$analyzed_base" \
  python3 skills/contribute-upstream/scripts/check_consumer_links.py filter-layout
CONSUMER_ROOT="<homelab root>" BASE="$analyzed_base" \
  python3 skills/contribute-upstream/scripts/check_consumer_links.py scan-deployed
# Project-name leak: added lines only (the uncommitted working-tree diff)
git diff | grep '^+' | grep -v '^+++' | grep -Fiw "Home Assistant Homelab" || true
```

Fail on any new BROKEN line, any unittest failure, or any leak hit. A line
naming two or more source projects (prime-swarm, security-swarm, homelab) is
the genericness-gate example list, not a leak. Also check the inverse: no
`{{project_name}}` lost from templatized skills, none gained by byte-identical
skills.

### 10. Hand off

Write the PR body under the core's `.scratch/` and hand off — the operator
owns branch, commit, push, and PR:

- **Branch:** `<type>/contribute-<slug>` — `type` is `feat|fix|docs|chore|refactor|test`,
  slug ≤ 4 kebab words total (core branch-naming cap;
  [`agent-branch-naming.md`](../../references/agent-branch-naming.md)). Do not
  reuse an existing `contribute-<slug>` branch — a timestamp token is the
  collision escape hatch.
- **Commit:** `<type>(<scope>): <imperative summary>` — scope is
  `rules|skills|scripts|templates`.
- **PR body:** starts with `Contribution from Home Assistant Homelab via
contribute-upstream.` — what changed, evidence (two source projects),
  migration notes for consumers, validation results.
- Report the ported files, validation output, and the PR-body path. Do not
  merge; a core maintainer reviews the PR.

## Do not

- Commit, push, or open PRs on either repo — hand off to the operator
- Create worktrees — edit the core main checkout; scratch under `.scratch/`
- Diff consumer-vs-HEAD without a resolvable baseline (no 2-way fallback)
- Copy a consumer file over `$base` — that reverts newer core history
- Port Homelab/HA-specific content (context modules, personas, routing rows, HA-native skills/rules)
- Hardcode a project name into core prose — restore `{{project_name}}`
- Port before the operator confirms the change set; ship before validation passes
