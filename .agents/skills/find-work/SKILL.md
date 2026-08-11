---
name: find-work
description: >-
  Orient on Home Assistant Homelab, scout read-only work sources (docs/issues
  + docs/plans, local_todo Issues/Tasks/Ideas ICS, shopping list, docs, TODO
  markers), rank a backlog with evidence, and emit launch briefs. Use when the
  user says find work, /find-work, what's left to do, or what should I work on.
disable-model-invocation: true
---

# Find work — Home Assistant Homelab

Read-only discovery. Orient, scout sources, rank and dedupe, then recommend
with **launch briefs**. Do not edit files, create worktrees, commit, push, or
open PRs. Git is operator-owned
([`operator-owned-git.md`](../../rules/operator-owned-git.md)).

Authoritative source rules live in
[`.agents/context/work-sources.md`](../../context/work-sources.md) — follow
that module; this skill is the workflow around it.

## Workflow

```
- [ ] 1. Orient (project model + constraints)
- [ ] 2. Scout sources (parallel, read-only)
- [ ] 3. Rank and dedupe into a backlog
- [ ] 4. Recommend top items + emit launch briefs
- [ ] 5. Hand off — wait for operator pick (or continue if they say so)
```

## 1. Orient

Read these (skim is fine):

| File                                                                       | Why                                     |
| -------------------------------------------------------------------------- | --------------------------------------- |
| [`AGENTS.md`](../../../AGENTS.md)                                          | Router                                  |
| [`.agents/context/README.md`](../../context/README.md)                     | Context hub                             |
| [`.agents/context/constraints.md`](../../context/constraints.md)           | Hard limits                             |
| [`.agents/context/traps.md`](../../context/traps.md)                       | Known pitfalls                          |
| [`.agents/context/work-sources.md`](../../context/work-sources.md)         | What to scan + dual-channel issue rules |
| [`.agents/context/development-loop.md`](../../context/development-loop.md) | Lap shape (find → implement → handoff)  |

## 2. Scout sources

Scan in parallel. Every candidate needs **source + evidence**. Missing sources
are non-fatal — note and continue.

| Source                 | How                                                                              | Notes                                                                            |
| ---------------------- | -------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| **Docs issues**        | `docs/issues/*.md` (skip README, `_template`)                                    | Agent ledger. Honor frontmatter status. Cite title + path + found_at.            |
| **Docs plans**         | `docs/plans/*.md` (skip README, `_template`)                                     | How-work. Honor status; note checkbox progress when cheap.                       |
| **Local Todo Issues**  | `.storage/local_todo.issues.ics` (`STATUS:NEEDS-ACTION`)                         | Human-reported. Cite SUMMARY + UID.                                              |
| **Local Todo Tasks**   | `.storage/local_todo.tasks.ics` (`STATUS:NEEDS-ACTION`)                          | Human-scoped. Cite SUMMARY + UID.                                                |
| **Local Todo Ideas**   | `.storage/local_todo.ideas.ics` (`STATUS:NEEDS-ACTION`)                          | Speculative. Cite SUMMARY + UID.                                                 |
| **Shopping list**      | Read `.shopping_list.json`                                                       | Legacy; still valid.                                                             |
| **Other docs**         | `docs/README.md`, `docs/packages.md`, `docs/projects.md`, `docs/CONTRIBUTING.md` | Documented follow-ups outside the issue/plan ledgers.                            |
| **TODO markers**       | `# TODO:` under `packages/**` and `docs/**`                                      | Cite path + line.                                                                |
| **Live HA (optional)** | Home Assistant MCP / live context                                                | Prefer when it clarifies broken entities/automations. Discovery stays read-only. |
| **GitHub (optional)**  | Issues/PRs if MCP/gh available                                                   | Nice-to-have; do not require or block on it.                                     |

### Do not scan

`docs/backlog/roadmap.md`, `docs/design/technology.md` (unless they exist and
operator asked), `ponytail:` comments, Linear, Notion, `sync-main.sh`,
Macroscope, agent-loop state, PR eligibility scripts. Do not invent worktrees.

### Docs issues / plans

Per [`work-sources.md`](../../context/work-sources.md) and the READMEs under
`docs/issues/` and `docs/plans/`. Skip closed/wontfix/superseded/promoted
issues and done plans.

### Local Todo + shopping list

Same read-only jq/python snippets as in `work-sources.md`. Never write those
files.

### TODO scan

```bash
rg -n '# TODO:' packages docs
```

## 3. Rank and dedupe

| Tier | What                                                             |
| ---- | ---------------------------------------------------------------- |
| 1    | Broken / urgent: open docs/issues bugs + human Local Todo Issues |
| 2    | Open docs/plans with work left; issues ready for plan authoring  |
| 3    | Open Local Todo Tasks; incomplete shopping-list items            |
| 4    | `# TODO:` markers; other documented follow-ups                   |
| 5    | Open Local Todo Ideas; speculative / nice-to-have                |

Dedupe: same outcome from two sources → one backlog row, cite both sources.

## 4. Recommend + launch briefs

### Hand-off routing

| Situation                                          | Next                                                                                                                                                     |
| -------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Vague title / unclear acceptance                   | [`alignment`](../alignment/SKILL.md)                                                                                                                     |
| Issue has acceptance, no plan                      | Plan authoring → `docs/plans/<slug>.md` + set issue `plan:`                                                                                              |
| Scoped config/package/automation change            | [`implement-change`](../implement-change/SKILL.md)                                                                                                       |
| Out-of-scope gap found while scouting              | [`file-issue`](../file-issue/SKILL.md) (agent channel)                                                                                                   |
| YAML validity / package layout / broken automation | [`config-validate`](../config-validate/SKILL.md), [`package-organize`](../package-organize/SKILL.md), [`automation-debug`](../automation-debug/SKILL.md) |
| Deep HA config questions                           | [`ha-config-expert`](../../agents/ha-config-expert/agent.md)                                                                                             |
| Complex automation design                          | [`automation-architect`](../../agents/automation-architect/agent.md)                                                                                     |

**Stop at:** implement → validate → "operator validates & commits". Never
recommend commits, pushes, PRs, or worktrees.

### Launch brief template

```
## Launch brief: <short title>

Source: <docs/issues | docs/plans | local_todo issues|tasks|ideas | shopping-list | docs | TODO | HA live | GitHub>
Evidence: <path + title | list + SUMMARY + UID | name + id | path:line>
Tier: <1–5>
Next skill: <alignment | file-issue | plan authoring | implement-change | …>

### Goal
<one paragraph>

### Acceptance
- [ ] …

### Constraints
- Dual channel: agent issues → docs/issues; human → Local Todo (read-only)
- Operator-owned git — no commit/push/PR/worktree
- Never write `.storage/local_todo.*.ics` or `.shopping_list.json`
- Validate before handoff (config-validate where relevant)
- Stop at: operator validates & commits

### Paste into new chat (or continue here)
<self-contained prompt the next agent can run cold>
```

## 5. Hand off

Present the backlog and briefs. **Wait for the operator** to pick an item
unless they already said to continue with the top recommendation.

Do not start implementation during find-work.
