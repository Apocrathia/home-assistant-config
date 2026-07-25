# Context Loading — Home Assistant Homelab

## Routing Table

Load context modules on demand. Start at the hub; pull constraints/traps before
non-trivial edits.

1. **`.agents/context/README.md`** — 60-second model + hub
2. **`.agents/context/constraints.md`** — Hard limits (always before config changes)
3. **`.agents/context/traps.md`** — Known pitfalls (before non-trivial changes)
4. **`.agents/context/nomenclature.md`** — Naming (when creating entities)
5. **`.agents/context/voice.md`** — Tone (substantive replies)
6. **`.agents/context/output.md`** — Format (docs / YAML presentation)
7. **`.agents/context/questions.md`** — Clarification (fuzzy scope)
8. **`.agents/context/work-sources.md`** — Work discovery (finding work)
9. **`.agents/context/tools.md`** — HA MCP, Grafana HA history, config check, shopping-list jq

## When to Load What

| If you're…                            | Then read                                                                   |
| ------------------------------------- | --------------------------------------------------------------------------- |
| New / unsure                          | `README.md` only                                                            |
| Starting non-trivial work             | `traps.md` + `constraints.md`                                               |
| Creating entities or automations      | `nomenclature.md` + `output.md` + `constraints.md`                          |
| Scope is fuzzy                        | `questions.md` (+ `skills/alignment/` if still fuzzy)                       |
| Writing docs or agent tone            | `voice.md` + `output.md`                                                    |
| Finding work to do                    | `work-sources.md` + `skills/find-work/SKILL.md`                             |
| Implementing a scoped change          | `constraints.md` + `skills/implement-change/SKILL.md` → hand off, no commit |
| Validating YAML configs               | `tools.md` + `skills/config-validate/SKILL.md`                              |
| Restructuring packages                | `skills/package-organize/SKILL.md`                                          |
| Fixing broken automations             | `skills/automation-debug/SKILL.md`                                          |
| Past HA entity state / history        | `tools.md` + `skills/grafana-ha-history/SKILL.md`                           |
| Syncing `.agents/` from upstream      | `skills/integrate-upstream/SKILL.md` + `rules/operator-owned-git.md`        |
| Context claims drifted from repo      | `skills/reconcile-context/SKILL.md`                                         |
| Tempted to commit / push / open PR    | `rules/operator-owned-git.md` — don't; operator-owned                       |
| Tempted to follow `ship-work` commits | Same — override; stop at validation + handoff                               |
| Need HA MCP / Grafana history / jq    | `tools.md`                                                                  |
| Deep HA config knowledge needed       | `agents/ha-config-expert/agent.md`                                          |
| Complex automation design needed      | `agents/automation-architect/agent.md`                                      |

## Handoff (implement-change)

After edits and validation:

1. Summarize what changed (paths + intent).
2. Suggest a Conventional Commit message — do **not** run `git commit`.
3. Stop. Operator validates live and commits.

See [`skills/implement-change/SKILL.md`](../skills/implement-change/SKILL.md)
and [`rules/operator-owned-git.md`](../rules/operator-owned-git.md).

## Rules

1. Context modules are **lazy-loaded** — only load what the task needs
2. Each module is self-contained — reference others by path, not duplication
3. Keep modules focused — one concern per file
4. Update `README.md` (context hub) when adding new modules
