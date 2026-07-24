---
name: find-work
description: >-
  Orient on Home Assistant Homelab, scout read-only work sources (shopping list,
  docs, TODO markers), rank a backlog with evidence, and emit launch briefs for
  a new chat or continue-with implement/alignment. Use when the user says find
  work, /find-work, what's left to do, or what should I work on.
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

| File                                                               | Why                                |
| ------------------------------------------------------------------ | ---------------------------------- |
| [`AGENTS.md`](../../../AGENTS.md)                                  | Router                             |
| [`.agents/context/README.md`](../../context/README.md)             | Context hub                        |
| [`.agents/context/constraints.md`](../../context/constraints.md)   | Hard limits                        |
| [`.agents/context/traps.md`](../../context/traps.md)               | Known pitfalls                     |
| [`.agents/context/work-sources.md`](../../context/work-sources.md) | What to scan + shopping-list rules |

Build a 60-second model: packages layout, what "done" means here (validate live,
operator commits), and which HA skills/agents exist.

## 2. Scout sources

Scan in parallel. Every candidate needs **source + evidence**. Missing sources
are non-fatal — note and continue.

| Source                 | How                                                                              | Notes                                                                                                                      |
| ---------------------- | -------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| **Shopping list**      | Read `.shopping_list.json`                                                       | Primary. See below.                                                                                                        |
| **Docs**               | `docs/README.md`, `docs/packages.md`, `docs/projects.md`, `docs/CONTRIBUTING.md` | Documented follow-ups / scoped notes. No `docs/issues/`, `docs/plans/`, backlog, or design trees — they do not exist here. |
| **TODO markers**       | `# TODO:` under `packages/**` and `docs/**`                                      | Cite path + line.                                                                                                          |
| **Live HA (optional)** | Home Assistant MCP / live context                                                | Prefer when it clarifies broken entities/automations. Discovery stays read-only.                                           |
| **GitHub (optional)**  | Issues/PRs if MCP/gh available                                                   | Nice-to-have; do not require or block on it.                                                                               |

### Do not scan

`docs/issues/`, `docs/plans/`, `docs/backlog/roadmap.md`, `docs/design/technology.md`,
`ponytail:` comments, Linear, Notion, `sync-main.sh`, ordered plan sequences,
Macroscope, agent-loop state, PR eligibility scripts.

### Shopping list

Per [`work-sources.md`](../../context/work-sources.md):

- **Read-only.** Never write, complete, or reformat `.shopping_list.json`.
- Surface only `"complete": false`. Cite `name` + `id`.
- Vague titles → [`alignment`](../alignment/SKILL.md) first.
- Missing / empty / invalid JSON / not an array → note "shopping list unavailable"
  and continue. Skip entries without `name`.

```bash
jq -r '.[] | select(.complete == false) | "\(.name) (\(.id))"' .shopping_list.json
```

### TODO scan

```bash
rg -n '# TODO:' packages docs
```

## 3. Rank and dedupe

Apply tiers in order. Within a tier, prefer clearer scope and stronger evidence.
Shopping-list items are an **unordered set** within their tier.

| Tier | What                                                   |
| ---- | ------------------------------------------------------ |
| 1    | Broken / urgent config or automation issues (if found) |
| 2    | Documented, already-scoped work in `docs/`             |
| 3    | Incomplete shopping-list items                         |
| 4    | `# TODO:` markers                                      |
| 5    | Speculative / nice-to-have                             |

Dedupe: same outcome from two sources → one backlog row, cite both sources.
Do not invent work.

## 4. Recommend + launch briefs

Report:

1. Short orient snapshot (1–3 sentences).
2. Ranked backlog table: tier, title, source, evidence, suggested next skill.
3. Top 1–3 **launch briefs** (copy-paste fences).

### Hand-off routing

| Situation                                          | Next                                                                                                                                                     |
| -------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Vague title / unclear acceptance                   | [`alignment`](../alignment/SKILL.md)                                                                                                                     |
| Scoped config/package/automation change            | [`implement-change`](../implement-change/SKILL.md) or continue in-session after operator pick                                                            |
| YAML validity / package layout / broken automation | [`config-validate`](../config-validate/SKILL.md), [`package-organize`](../package-organize/SKILL.md), [`automation-debug`](../automation-debug/SKILL.md) |
| Deep HA config questions                           | [`ha-config-expert`](../../agents/ha-config-expert/agent.md)                                                                                             |
| Complex automation design                          | [`automation-architect`](../../agents/automation-architect/agent.md)                                                                                     |

**Stop at:** implement → validate → "operator validates & commits". Never
recommend commits, pushes, PRs, worktrees, `ship-work`, or watch-PR loops.

### Launch brief template

```
## Launch brief: <short title>

Source: <shopping-list | docs | TODO | HA live | GitHub>
Evidence: <name + id | path:line | doc section>
Tier: <1–5>
Next skill: <alignment | implement-change | config-validate | …>

### Goal
<one paragraph>

### Acceptance
- [ ] …

### Constraints
- Read work-sources.md shopping-list rules if applicable
- Operator-owned git — no commit/push/PR/worktree
- Validate before handoff (config-validate where relevant)
- Stop at: operator validates & commits

### Paste into new chat (or continue here)
<self-contained prompt the next agent can run cold>
```

## 5. Hand off

Present the backlog and briefs. **Wait for the operator** to pick an item
unless they already said to continue with the top recommendation.

Then either:

- Open a **new chat** with the pasted brief, or
- Continue in this session with the named skill (alignment / implement-change /
  HA skill).

Do not start implementation during find-work.
