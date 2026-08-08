---
alwaysApply: true
description: Delegate work to subagents early and often; parallelize by default
---

# Subagents

Subagent delegation is graph orchestration: each subagent is a node, the parent
wires the edges, and atomic tasks report back for compilation by the parent or
another node. This is graph engineering — multiple agents, each running their
own loop, connected through a directed acyclic graph (DAG). A single agent
doing everything is a degenerate graph (one node).

The parent agent coordinates; it does not hoard context. Delegate before you
burn turns on exploration, shell work, or review. When subagents return,
summarize outcomes for the operator; do not restate their full output (see
[`response-shape.md`](./response-shape.md)).

Edit in the main checkout. Do not open worktrees
([`worktrees.md`](./worktrees.md)). Do not commit or push
([`operator-owned-git.md`](./operator-owned-git.md)).

## Project agents (prefer these)

Custom subagents live in `.agents/agents/` (Cursor copies under
`.cursor/agents/`). Use them when the task matches:

| Agent                  | When                                                     |
| ---------------------- | -------------------------------------------------------- |
| `ha-config-expert`     | Deep HA configuration, packages, entities, traps         |
| `automation-architect` | Complex automation design (triggers/conditions/actions)  |
| `security-analyst`     | Adversarial audit of config posture / dependency vectors |
| `/implementer`         | Atomic config/code unit against a Bar                    |
| `/reviewer`            | Judge Artifact against Bar (pair with implementer)       |
| `/verifier`            | Post-pair arbiter (`config-validate` / tools.md)         |
| `/context-steward`     | Context drift detection after renames / doc moves        |

Invoke by name or delegate explicitly. Run independent agents in parallel in one
message when fan-out helps.

`security-analyst` is **on-demand and audit-only** — spawn it when the operator
asks for a security pass. The parent may _suggest_ (never auto-run) a spawn when
a change touches locks/alarms/cameras, presence/away/vacation, auth/tokens/
`secrets.yaml` refs, `custom_components/`, or anything expanding external reach.
It reports findings and stops; it does not edit. Not a `review-loop` gate.
Domain reviewers (including `security-analyst`) fill the **reviewer** Role when
the Bar is security-shaped.

## When to stay in the parent

- Single known file, single edit, no discovery — parent may edit directly.
- User asked you not to delegate.
- Subagent would need conversation context the prompt cannot carry (rare; write
  a detailed cold-start prompt instead).

## Prompt contract (always-on)

Subagents start cold. Every Task prompt includes these fields:

| Field        | Meaning                                                                                      |
| ------------ | -------------------------------------------------------------------------------------------- |
| **Slice**    | Shared id for an implementer↔reviewer pair (omit for verifier and unpaired roles)           |
| **Goal**     | Role-specific: what _this_ agent must do                                                     |
| **Bar**      | Inspectable standard (acceptance, config check, threat model, clean reviewers). Never vibes. |
| **Role**     | `implementer` \| `reviewer` \| `verifier` \| unpaired (`scout`, `planner`, …)                |
| **Artifact** | Concrete thing to produce or inspect (paths, commands, diff, rendered output)                |
| **Return**   | Structured evidence handoff                                                                  |

Ask for evidence (file paths, command output, root cause), not vibes.
Remind them: no commits, no worktrees, confirm before protected paths
([`protected-paths.md`](./protected-paths.md)).

> Homelab skills (`implement-change`, `review-loop`, …) are thin and may omit
> formal contract fields when the parent supplies equivalent context inline.
> Use the full contract for new Task prompts and any multi-agent fan-out.

### Implementer ↔ reviewer pairs

For each **independent** unit of work that needs an independent judge, treat
implementer and reviewer as an **inseparable pair**. Domain reviewers
(`security-analyst`, cold-start Tasks) fill the **reviewer** slot. Do not invent
parallel role names for the same jobs.

```
implementer → reviewer → pass | gap
                ↑___________|  (new Tasks both sides on gap)
```

- **Same Bar and Artifact; different Goals.** The implementer changes the
  artifact toward the Bar. The reviewer judges the artifact against the Bar and
  returns `pass` or `gap` (the single biggest remaining miss).
- **Implementer never grades itself.** Pass against the Bar is the reviewer's
  job. Local smoke checks are fine; they are not a pass.
- **Reviewer does not inherit implementer rationale.** Give Goal, Bar,
  Artifact, constraints — not the implementer's narrative.
- **Each round is a new Task for both sides.** On `gap`, spawn a **new**
  implementer (gap + Bar + Artifact) and then a **new** reviewer.
- **Fan out only independent slices.** Coupled surfaces get one implementer
  (sequential).
- **Pair stop** when the reviewer returns `pass`, or when stop-loss / an
  explicit skill cap / the operator stops the run.

For trivial single-file edits, skip the pair — parent edits and validates.

### Verifier (arbiter)

The verifier is **not** in the pair. It runs **after** the implementer↔reviewer
pair returns `pass` (or after the parent finishes a trivial edit). Prefer the
`/verifier` persona, or run [`config-validate`](../skills/config-validate/SKILL.md)
/ [`review-loop`](../skills/review-loop/SKILL.md) as the arbiter.

- On **pass**: continue to operator handoff.
- On **issue**: fix or escalate; do not declare ready.

Unpaired roles (scouts, planners) still fill Goal, Bar, Role, Artifact, and
Return. Their Bar is usually coverage of the scoped sources with evidence.

## Typical pipeline

**Unclear scope:** [`alignment`](../skills/alignment/SKILL.md) (read-only) until
the operator confirms proceed, then implement in the main checkout.

**Non-trivial work (scope clear):** implement → validate
([`config-validate`](../skills/config-validate/SKILL.md) when touching YAML) →
hand off per [`operator-owned-git.md`](./operator-owned-git.md). Prefer
[`implement-change`](../skills/implement-change/SKILL.md) over hand-rolling
fan-out — ignore any worktree/ship steps that skill still mentions upstream.

**Trivial** (single file, obvious edit): parent edits in place; skip subagent
delegation.

## Anti-patterns

- Creating worktrees or editing under `.worktrees/`.
- Parent jumps to implementation on a vague ask without alignment.
- Sequential `Read`/`Grep` across many files when an explorer subagent fits.
- Implementer starts without a Bar, acceptance criteria, or file paths from the parent.
- Implementer grades its own work against the Bar (skips an independent check).
- Skipping validation because "it looks fine."
- Parent pastes subagent output or tool-call narration into the operator reply.
- Committing, pushing, or opening PRs (operator-owned).
