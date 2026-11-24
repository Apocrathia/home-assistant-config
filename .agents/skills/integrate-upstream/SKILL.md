---
name: integrate-upstream
description: >-
  Pull changes from the context-engine core into Home Assistant Homelab's
  .agents/ tree — diff shared rules, skills, and scripts, reconcile layer 1 and
  2 changes, and preserve project-specific content. Use when the user says sync
  upstream, integrate upstream changes, pull updates from the core, or update
  .agents/ from the context-engine core.
disable-model-invocation: true
---

# Integrate upstream — Home Assistant Homelab

This repo's `.agents/` is built from the
context-engine core. The
core evolves — new rules, improved skills, better scripts, new templates. This
skill pulls those upstream changes in while preserving Homelab-specific content
(layer 3).

**Apply in the main checkout after operator confirmation.** This repo does not
use git worktrees. Do not create a `chore/integrate-upstream` branch or
worktree. Git is operator-owned
([`operator-owned-git.md`](../../rules/operator-owned-git.md)) — propose, apply
on confirm, update the pin, validate, hand off. No commits, pushes, or PRs.

Three layers:

| Layer                | What                                             | How this skill handles it                   |
| -------------------- | ------------------------------------------------ | ------------------------------------------- |
| 1 — Generic          | Rules, byte-identical skills, scripts            | Direct diff; copy or reconcile              |
| 2 — Templatized      | Skills marked `templatized: true` in frontmatter | Diff after token normalization; reconcile   |
| 3 — Project-specific | Context modules, HA agents/skills, routing       | **Do not overwrite.** Structural check only |

`contribute-upstream` and `integrate-upstream` are layer 1 even though they
contain `{{project_name}}`: those mentions document the token convention, and
substituting the project name into them corrupts the consumer copy (issue
#32). Never replace the token in either skill. `check_tokens.py` compares
those copies to the `token_counts` recorded in `.agents/upstream-ref`; step 9
refreshes that manifest.

## When to run

- Operator says sync upstream, update from the core, pull the core, or
  integrate upstream
- After the core ships changes that affect shared rules/skills/scripts
- Before a [`reconcile-context`](../reconcile-context/SKILL.md) pass when shared
  files may be stale

## Defaults for this project

| Input                  | Default                                                                          |
| ---------------------- | -------------------------------------------------------------------------------- |
| **Upstream core path** | operator's local core checkout — ask the operator (path stays out of repo files) |
| **Project name**       | `Home Assistant Homelab` (for `{{project_name}}` substitution)                   |
| **Baseline pin**       | [`.agents/upstream-ref`](../../upstream-ref) — SHA of last sync                  |
| **Checkout**           | Main workspace only — no worktree                                                |

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
- [ ] 9. Update .agents/upstream-ref to $upstream_rev (only on a complete apply)
- [ ] 10. Run link + discovery + frontmatter + token checks
- [ ] 11. Report and hand off (operator commits)
```

### 1. Locate and load the upstream core

```bash
upstream="<core checkout — ask the operator>"
# Or operator-supplied path / temp clone of a remote
```

Verify the upstream looks like the core: top-level `rules/`, `skills/`,
`templates/` (or `.agents/` equivalents depending on core layout). If the
structure does not match, stop and ask.

Pin the **canonical tip**, not whatever branch the checkout happens to be on —
fetch, never re-checkout or fast-forward the supplied clone. If the checkout's
`origin` is a fork, fetch the canonical remote
(`PrimeIntellect-ai/prime-context`) instead; a fork's `origin/main` can be
stale:

```bash
git -C "$upstream" fetch origin
upstream_rev=$(git -C "$upstream" rev-parse origin/main)
echo "Upstream revision: $upstream_rev"
```

Every later read (`diff`, `show`, copies) uses `$upstream_rev`, not the
working tree — a behind or dirty checkout is expected and must not leak into
the sync.

### 2. Baseline from upstream-ref

```bash
baseline_rev=$(python3 -c 'import json; print(json.load(open(".agents/upstream-ref")).get("sha") or "")' 2>/dev/null || echo "")
```

The pin is JSON: `sha` (the baseline), `synced_at`, optional `version`, and
`token_counts` — the expected `{{project_name}}` mention count per
token-bearing doc skill; the step-9 pin write refreshes it. A bare SHA (older
pins) is read as-is.

Verify the pin is an object in `$upstream` **and** an ancestor of
`$upstream_rev`:

```bash
git -C "$upstream" cat-file -e "$baseline_rev" 2>/dev/null   && git -C "$upstream" merge-base --is-ancestor "$baseline_rev" "$upstream_rev"   || echo "baseline not verifiable — stop and ask the operator for the SHA"
```

Never pass a consumer-repo SHA to `git -C "$upstream"` without resolving it
there first. If the baseline is missing or unverifiable, **do not degrade to
a 2-way diff** — a 2-way consumer-vs-HEAD diff cannot tell a local
customization from stale core text. Stop and ask.

### 3. Inventory this project's `.agents/`

```bash
agents_dir="$(git rev-parse --show-toplevel)/.agents"
find "$agents_dir/rules" -name '*.md' 2>/dev/null | sort
find "$agents_dir/skills" -name 'SKILL.md' 2>/dev/null | sort
find "$agents_dir/skills" -type f ! -name 'SKILL.md' ! -name '*.pyc' ! -path '*/__pycache__/*' 2>/dev/null | sort
find "$agents_dir/context" -name '*.md' 2>/dev/null | sort
find "$agents_dir/agents" -name '*.md' 2>/dev/null | sort
```

Record the full file list, including agent personas (`.agents/agents/`) and
skill auxiliaries (`scripts/`, `references/`) — a file that existed at the
baseline but is gone from `$upstream_rev` is **removed upstream**: surface it
for decision, do not silently keep it.
Check that Homelab has personas (or documented role mappings in
[`subagents.md`](../../rules/subagents.md)) for roles shared skills invoke
(`/implementer`, `/reviewer`, `/verifier`, plus any HA domain agents).

**Leave alone (layer 3 / HA-native):** context modules tailored to Homelab,
HA agents, and domain skills `automation-debug`, `config-validate`,
`package-organize`, plus any Homelab-only rules (e.g. operator-owned-git,
work-sources).

### 4–6. Layer, diff, reconcile

Discover upstream files dynamically from `$upstream_rev`
(`git -C "$upstream" ls-tree -r --name-only "$upstream_rev"`), do not hardcode
skill names, and diff against `$upstream_rev` (`git show "$upstream_rev:<file>"`)
— never the working tree. Classify a skill as layer 2 from the
`templatized: true` frontmatter marker, never by grepping for
`{{project_name}}`: `contribute-upstream` and `integrate-upstream` mention the
token as documentation and stay byte-identical.

| Layer                       | Upstream source                             | Local                                 | Action                                                   |
| --------------------------- | ------------------------------------------- | ------------------------------------- | -------------------------------------------------------- |
| 1 — Rules                   | `rules/*.md`                                | `.agents/rules/*.md`                  | Direct diff                                              |
| 1 — Byte-identical skills   | `skills/<name>/SKILL.md` (no project token) | `.agents/skills/<name>/SKILL.md`      | Direct diff                                              |
| 1 — Skill auxiliaries       | `skills/<name>/**` except `SKILL.md`        | same under `.agents/skills/<name>/`   | Direct diff                                              |
| 2 — Templatized skills      | skills marked `templatized: true`           | local skill                           | Diff after replacing token with `Home Assistant Homelab` |
| 3 — Context / root / refs   | `templates/**`                              | `.agents/context/`, `AGENTS.md`, etc. | Structural suggestions only — never overwrite            |
| 3 — Agent persona templates | `templates/agents/*.tmpl`                   | `.agents/agents/*.md`                 | Structural only — verify role coverage in `subagents.md` |

For modified files, 3-way when baseline is known:

1. What changed upstream: `git -C "$upstream" diff <baseline_rev>..$upstream_rev -- <file>`
2. What changed locally beyond project-name substitution
3. Decide: clean apply | conflict (propose merge) | local improvement (push back via [`contribute-upstream`](../contribute-upstream/SKILL.md))

Categories: unchanged | added upstream | modified | removed upstream |
project-specific | **opt-in upstream** — optional skills absent locally (the
visual suite here) are surfaced as available, never auto-copied.

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

1. Copy new files (token-replace layer 2), always from `$upstream_rev`
   (`git show`), never from the working tree.
2. Replace clean-apply files.
3. Apply agreed reconciliations.
4. Handle removals per operator decision.
5. Do **not** overwrite layer 3 / HA-native skills.

### 9. Update the pin — only on a complete apply

```bash
synced_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
counts=$(python3 - <<'PY'
import json
counts = {}
for skill in ("contribute-upstream", "integrate-upstream"):
    with open(f".agents/skills/{skill}/SKILL.md", encoding="utf-8") as fh:
        counts[skill] = fh.read().count("{{project_name}}")
print(json.dumps(counts))
PY
)
python3 - "$upstream_rev" "$synced_at" "$counts" <<'PY'
import json, sys
sha, synced_at, counts = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
with open(".agents/upstream-ref", "w") as f:
    json.dump({"sha": sha, "synced_at": synced_at, "token_counts": counts}, f, indent=2)
    f.write("\n")
PY
```

The pin is a JSON object: `sha`, `synced_at`, and `token_counts` — the
`{{project_name}}` mention count for the two doc skills. Count from the
reconciled local copies (equal to the upstream counts when the copies are
byte-identical) so `check_tokens.py` verifies the copies that actually
shipped. Do not stage; the operator commits the pin with the sync.

Bump the pin **only** when every confirmed layer-1/2 file was applied and
the checks pass. If the operator declined any layer-1/2 update or a check
fails, leave `upstream-ref` unchanged and say why in the report — the next
sync 3-ways from the stale pin, and
[`contribute-upstream`](../contribute-upstream/SKILL.md) reads it as its
baseline.

Include `upstream-ref` in the handoff so the operator commits it with the sync.

### 10. Checks

```bash
python3 .agents/skills/reconcile-context/scripts/check_links.py
python3 .agents/skills/reconcile-context/scripts/check_discovery.py
python3 .agents/skills/reconcile-context/scripts/check_frontmatter.py
```

Run `check_tokens.py` **after** the step-9 pin write — it reads
`token_counts` from `.agents/upstream-ref`, so running it sooner compares the
new copies against the previous pin:

```bash
python3 .agents/skills/reconcile-context/scripts/check_tokens.py
```

If a script is missing locally and exists upstream, include copying it in the
confirmed change set (layer 1). Note pass/fail in the report.
`check_links.py` walks tracked files — brand-new files are invisible until
the operator stages them (`git add -N`); agents never stage. On new link-check
breakage, filter consumer-layout false positives first
(`skills/contribute-upstream/scripts/check_consumer_links.py filter-layout`)
before treating a break as real.

### 11. Report and hand off

```markdown
## Upstream integration

**Upstream:** <path> @ <sha>
**Baseline was:** <old sha>
**Result:** <N clean applies, N reconciled, N new, N removed>
**Pin:** bumped to <sha> | left unchanged — <reason>

### Changes applied

- …

### Structural suggestions (not applied)

- …

### Local improvements to contribute back

- …

### Checks

- link: <pass | N issues>
- discovery: <pass | N issues>
- tokens: <pass | N issues>

### Next

- Operator validates and commits (suggested message below)
- Do **not** open a PR or create a branch from this skill
- Generic local improvements go back to the core via
  [`contribute-upstream`](../contribute-upstream/SKILL.md) — separate lap,
  operator owns the core commit/PR
```

Suggest a Conventional Commit message, e.g.
`chore(agents): sync .agents from the core (<short-sha>)`.

A clean pass with nothing to change is valid — say so, still confirm whether
to bump `upstream-ref` if HEAD moved with no file deltas (a declined or failed
apply leaves it untouched).

## Do not

- Create worktrees or `chore/integrate-upstream` branches
- Apply changes without operator confirmation
- Overwrite layer 3 / HA-native skills and Homelab context
- Commit, push, or open PRs — hand off to the operator
- Skip link/discovery/frontmatter checks after writes
- Assume the upstream path without verifying structure
- Blindly take either side of a conflict — propose the merge first
- Copy from the upstream working tree or a non-canonical branch — use
  `$upstream_rev`
- 2-way on a missing/unverifiable baseline — stop and ask for the SHA
- Bump `upstream-ref` past a declined or failed apply
- Auto-copy optional upstream skills (visual suite) — surface, wait for a
  yes
