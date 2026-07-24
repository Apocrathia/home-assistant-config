---
name: autoresearch
description: >-
  Optional, operator-gated metric experiments under .scratch/ for Home Assistant
  Homelab. Prefer prototype for design questions. Use only when a measurable
  eval exists and the operator wants a short experiment log — not a swarm
  research loop or docs/research PR.
disable-model-invocation: true
---

# Autoresearch — Home Assistant Homelab

Honest fit check first: this is a **Home Assistant config repo**, not a
benchmark-heavy code swarm. Most questions here are better answered by
[`prototype`](../prototype/SKILL.md), live HA traces, or
[`architecture-review`](../architecture-review/SKILL.md).

There is **no** `docs/research/` surface and no research PRs. Git is
operator-owned ([`operator-owned-git.md`](../../rules/operator-owned-git.md)).
This repo does not use git worktrees — experiments stay under `.scratch/` in
the main checkout.

## When NOT to use this skill

Stop and route elsewhere when:

| Situation                                                        | Use instead                                                                                           |
| ---------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| "Does this automation/state model feel right?"                   | [`prototype`](../prototype/SKILL.md) in `.scratch/`                                                   |
| Package layout / coupling / design debt                          | [`architecture-review`](../architecture-review/SKILL.md)                                              |
| Vague idea needs scoping                                         | [`alignment`](../alignment/SKILL.md)                                                                  |
| Broken YAML / automation                                         | [`config-validate`](../config-validate/SKILL.md) / [`automation-debug`](../automation-debug/SKILL.md) |
| No measurable metric or eval command                             | Do not invent one — hand off                                                                          |
| Operator wants a durable research writeup under `docs/research/` | Decline — that path is not first-class here                                                           |

## When it _is_ appropriate (rare)

Only when **all** of these hold:

1. Operator explicitly wants metric-driven experiments (or find-work surfaces
   this as a last-resort brief with a clear metric).
2. There is a real **eval command** that produces a numeric metric (script
   runtime, entity count query, validation exit code over a corpus, etc.).
3. Experiments stay under [`.scratch/`](../../../.scratch/README.md) — never
   under `packages/` as throwaway.

## Slim workflow

```
- [ ] 1. Confirm fit (or refuse and route)
- [ ] 2. Agree hypothesis, in-scope scratch paths, eval, metric
- [ ] 3. Baseline under .scratch/<slug>/
- [ ] 4. Run a short experiment loop (keep notes in .scratch; no commits)
- [ ] 5. Stop when proven / disproven / exhausted / operator interrupts
- [ ] 6. Hand off: findings + recommended next skill; operator decides what to promote
```

### Contract (keep tiny)

| Field                   | Required                            |
| ----------------------- | ----------------------------------- |
| Hypothesis              | Yes — testable claim                |
| In-scope paths          | Yes — only under `.scratch/<slug>/` |
| Eval command            | Yes — no embedded secrets           |
| Metric name + direction | Yes — `lower` or `higher`           |
| Constraints             | Optional                            |

Do not change the contract mid-run. If the hypothesis evolves, stop and start
a new slug.

### Rules

- **No commits, pushes, or PRs**
  ([`operator-owned-git.md`](../../rules/operator-owned-git.md)).
- **No edits to `packages/`** as experimental throwaways — copy ideas into
  scratch, measure, then promote via implement-change if warranted.
- Log experiments as plain markdown/JSON under `.scratch/<slug>/` (gitignored).
- Cap the loop: prefer a handful of deliberate trials over an autonomous swarm.
- At the end, summarize findings for the operator. Do not open a docs PR.

## Hand off

```markdown
## Autoresearch handoff

**Hypothesis:** …
**Result:** proven | disproven | exhausted | interrupted
**Best metric:** … (baseline …)
**Scratch path:** `.scratch/<slug>/`
**Recommend next:** prototype | alignment | implement-change | drop
```

## Related

[`prototype`](../prototype/SKILL.md) · [`architecture-review`](../architecture-review/SKILL.md) ·
[`alignment`](../alignment/SKILL.md) · [`.scratch/README.md`](../../../.scratch/README.md)
