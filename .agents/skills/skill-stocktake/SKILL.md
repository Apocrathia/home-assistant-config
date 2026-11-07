---
name: skill-stocktake
description: >-
  Periodic audit of the project's skill library: inventory, evaluation for
  overlap, staleness, and scope fit, and Keep / Improve / Update / Retire /
  Merge verdicts, with subagent batching and operator confirmation before any
  retire or merge. Use when the user says skill stocktake, audit the skills,
  or prune the library.
disable-model-invocation: true
---

# Skill stocktake

Adapted from [ECC](https://github.com/affaan-m/ECC) (MIT), `skills/skill-stocktake/`.

Skill libraries only grow. Without an audit they accumulate overlap, stale
references, and skills nothing triggers. The stocktake asks the question no
other surface asks: is each skill still worth its place?
[`reconcile-context`](../reconcile-context/SKILL.md) fixes drift between
context and repo; this skill judges the library itself. Evaluation is blind —
same checklist for every skill regardless of origin.

## When to run

- The operator asks for a stocktake, skill audit, or library prune.
- Periodically (monthly or quarterly) once the library passes ~20 skills.
- After an [`integrate-upstream`](../integrate-upstream/SKILL.md) sync lands
  several new skills at once.

## Results cache

`.scratch/skill-stocktake/results.json` — ephemeral, never committed; losing
it just means the next run is full. Update it as each batch lands (merge,
never overwrite — earlier verdicts survive). Set `evaluated_at` to the actual
UTC completion time, not a date approximation.

```json
{
  "evaluated_at": "<UTC>",
  "mode": "full",
  "status": "in_progress",
  "skills": { "skills/foo/SKILL.md": { "mtime": "…", "verdict": "Keep", "reason": "self-contained" } }
}
```

## Workflow

```
- [ ] 1. Inventory + mode selection
- [ ] 2. Evaluate in subagent batches
- [ ] 3. Summary table
- [ ] 4. Consolidation (operator decides)
```

### 1. Inventory + mode selection

Locate the skills tree — `skills/` in this repo, `.agents/skills/` in a
consuming project — and say up front which paths were found and scanned.
Skip archive directories (`.trash`-style): archived skills are not live
inventory. `find <skills-tree> -name SKILL.md -not -path '*/.trash/*'`.

Record per skill: path, frontmatter `name` and `description`, last-touch time
(`git log -1 --format=%cI -- <path>`, else mtime). Note which skills the
`AGENTS.md` routing table names — a skill the router never mentions deserves a
second look, and routing rows are where a retired skill leaves a hole.

Usage: most projects measure nothing. Record **unmeasured**, never zero —
missing usage data is never evidence for retiring. If the project keeps real
measurements (telemetry, run logs), count those in instead.

Then pick the mode:

- `status: "in_progress"` in the results file → **resume**: keep saved
  verdicts only for paths still present with unchanged last-touch time;
  evaluate the rest. If nothing remains, mark completed, go to step 3.
- Completed results file → **quick scan**: evaluate only skills changed since
  `evaluated_at`, plus any skill absent from the file. If the set is empty,
  report "No changes since last run." and stop. Carry unchanged verdicts.
- No results file, or the operator asks → **full stocktake**.

Changed set: `git log --name-only --format= --since=<evaluated_at>` over
`skills/ .agents/skills/` — or compare mtimes against `evaluated_at` when the
tree isn't tracked.

### 2. Evaluate in subagent batches

Fan out in batches of ~20 skills per subagent. Each batch subagent gets
inline (subagent prompts don't inherit this page): its batch's inventory rows
plus the full inventory list — overlap checks need the whole library — the
checklist, the verdict table, and the reason-quality spec. It reads each
`SKILL.md` and returns one verdict and reason per skill, keyed by path so
merges can't overwrite one skill with a same-named other.

Per-skill checklist:

```
- [ ] Overlap with other skills checked
- [ ] Overlap with AGENTS.md / .agents/context/ content checked
- [ ] Technical references verified at their source when tools/flags/APIs appear
- [ ] Trigger surface sane: the description says what it does and when to use it
- [ ] Usage considered when measured; unmeasured marked as such, never zero
```

Verdicts — holistic judgment, not a numeric rubric; weigh actionability
(usable examples, commands, steps), scope fit (name, trigger, and content
aligned), uniqueness (value not already in `AGENTS.md`, a context module,
or another skill), and currency (references hold in the current environment):

| Verdict        | Meaning                                                |
| -------------- | ------------------------------------------------------ |
| Keep           | Useful and current                                     |
| Improve        | Worth keeping; specific improvements needed            |
| Update         | References outdated technology (verified, not assumed) |
| Retire         | Low quality, stale beyond repair, or cost-asymmetric   |
| Merge into [X] | Substantial overlap with [X]; name the target          |

### Reason quality

Every `reason` must be self-contained and decision-enabling: a reader who
never opened the skill can act on it. Never "unchanged" alone.

- **Retire** — the specific defect, and what covers the same need.
  - Bad: `"Superseded."` Good: `"Superseded by retry-with-backoff, which
covers the same failure patterns plus jitter; no unique content remains."`
- **Merge** — the target, and what content integrates into it.
  - Bad: `"Overlaps with file-issue."` Good: `"42 lines; step 3 of file-issue
already covers this workflow. Fold the triage-label note into file-issue's
examples, delete the rest."`
- **Improve** — the specific change: section, action, target size.
  - Bad: `"Too long."` Good: `"276 lines; 'Framework comparison' (L80–140)
duplicates the technology module; cutting it reaches ~150."`
- **Update** — what is outdated and what changed upstream, with the source.
  - Bad: `"Docs moved."` Good: `"Step 2 calls v1/events; upstream deprecated
it for v2/streams (March changelog). Steps 2–4 need rewriting."`
- **Keep** — restate the core evidence, even when only the touch time moved.
  - Bad: `"Unchanged."` Good: `"mtime-only change; content identical. Documents
the one install matrix no other surface covers; no overlap found."`

### 3. Summary table

Report the run: paths scanned, skill count, mode, and the verdict table —
all skills for a full run, only changed skills for a quick scan.

| Skill | Verdict | Reason |
| ----- | ------- | ------ |

### 4. Consolidation (operator decides)

- **Retire / Merge**: present the per-skill justification before touching
  anything — the defect found, what covers the need now, and the impact of
  removal (dependent skills, `AGENTS.md` routing rows, links from other
  skills). Nothing is deleted or merged without operator confirmation: skill
  directories and `AGENTS.md` are steering surfaces, so apply through the
  repo's protected-path flow.
- **Improve / Update**: present the concrete suggestion and its sources; the
  operator decides whether to act.

## Do not

- Treat missing usage data as evidence for retiring — unmeasured is not dead
- Retire or merge anything without operator confirmation
- Write a reason that is not self-contained ("unchanged", "superseded" alone)
- Evaluate a batch without the full inventory — overlap needs the whole library
- Run unasked or block on it — the stocktake informs, it doesn't gate
