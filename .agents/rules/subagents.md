---
alwaysApply: true
description: Delegate early; congruent model and effort on children; thin parent context
---

# Subagents

Subagent delegation is graph orchestration: the parent wires a DAG of agents;
one agent doing everything is a degenerate graph (one node).

The parent agent coordinates; it does not hoard context. Delegate before you
burn turns on exploration, shell work, or review. When subagents return,
summarize outcomes for the operator; do not restate their full output (see
[`response-shape.md`](./response-shape.md)). Prefer **file handoffs** for
briefs, reports, and diffs: the spawn prompt names paths; the child writes the
long form to disk and returns a short status. **Readonly agents** (reviewers,
verifiers, scouts, `context-steward`) return short status only — no file
handoffs. Never paste tool dumps or subagent transcripts into the parent window.

**Main checkout only.** This repo bans worktrees
([`worktrees.md`](./worktrees.md)): never open one, never edit under
`.worktrees/`. Hold working files, briefs, and reports in gitignored `.scratch/`
task folders. Do not commit or push
([`operator-owned-git.md`](./operator-owned-git.md)).

## Route the moment the work is identified

The persona table is a routing surface, not a menu. The moment you can name
the work, route it — never work it yourself while a matching skill or persona
exists.

- A skill's trigger covers it → run the skill; its fan-out delegates per its
  own gates.
- Named work type → that persona, before you touch the work.
- No matching row or skill → an unnamed Task with the prompt contract below;
  can't name the work yet → scout first, then re-match.

## Project agents (prefer these)

Custom subagents live in `.agents/agents/`. Use them when the task matches:

| Agent                  | When                                                      |
| ---------------------- | --------------------------------------------------------- |
| `ha-config-expert`     | Deep HA configuration, packages, entities, traps          |
| `automation-architect` | Complex automation design (triggers/conditions/actions)   |
| `security-analyst`     | Adversarial audit of config posture / dependency vectors  |
| `pattern-analyst`      | Mine HA history for trigger candidates (implementer half) |
| `pattern-reviewer`     | Judge pattern-mine Artifact vs Bar (reviewer half)        |
| `/implementer`         | Atomic config/code unit against a Bar                     |
| `/reviewer`            | Judge Artifact against Bar (pair with implementer)        |
| `/verifier`            | Post-pair arbiter (`config-validate` / tools.md)          |
| `/context-steward`     | Context drift detection after renames / doc moves         |

`security-analyst` is **on-demand and audit-only** — spawn it when the operator
asks for a security pass. The parent may _suggest_ (never auto-run) a spawn when
a change touches locks/alarms/cameras, presence/away/vacation, auth/tokens/
`secrets.yaml` refs, `custom_components/`, or anything expanding external reach.
It reports findings and stops; it does not edit — not a `review-loop` gate.
Domain reviewers (including `security-analyst`) fill the **reviewer** Role when
the Bar is security-shaped. `pattern-analyst` ↔ `pattern-reviewer` are an
inseparable pair for history-pattern Bars (procedure:
[`pattern-mine`](../skills/pattern-mine/SKILL.md)); they do not write YAML —
hand `pass` candidates to `automation-architect`.

## When to delegate vs. stay in the parent

Delegate when sub-tasks are independent (fan out in parallel), read across
files you don't need to keep (keep the answer, not the raw material), or are
self-contained with goal, constraints, return shape. Stay in the parent when:

- Single known file, single edit, no discovery — parent may edit directly.
- User asked you not to delegate.
- Subagent would need conversation context the prompt cannot carry (rare; write
  a detailed cold-start prompt instead).

## Congruent model and effort

Assign a model **and**, when the harness exposes it, a thinking/effort level
congruent to the child's job — not the parent's. Soft preference; never
hard-fail when the harness does not accept per-Task picks.

| Child job                                             | Model slot         | Thinking/effort |
| ----------------------------------------------------- | ------------------ | --------------- |
| Scout, triage, status pack                            | Cheapest capable   | Lowest          |
| Mechanical implement from a complete spec (1–2 files) | Cheapest capable   | Low             |
| Implement from prose; multi-file integration          | Mid (floor)        | Mid             |
| Correctness / logic review                            | Cheapest capable   | Low             |
| Security or architecture review                       | Mid, distinct slot | Mid–high        |
| Broad, high-judgment whole-branch review              | Most capable       | Highest         |

- **Name both on spawn.** Omitted often means silent inherit of the expensive
  parent defaults; don't default a lighter job onto the parent model.
- **Cost control is congruence.** Max thinking on a mechanical scout is a
  miss; a too-cheap model thrashing 2–3× turns costs more than mid. Mid floors
  security / architecture reviews and prose implementers.
- Parallel lens reviewers should use **different** model slots when possible.

## Task lifecycle (one-shot leaves)

Leaf subagents are **disposable**: run one Goal, write the handoff, return a
short status, and stop. Only thin coordinators (`review-loop` parents,
multi-task orchestrators) stay live until their stop condition. Leaf status:
`DONE` (proceed), `DONE_WITH_CONCERNS` (fix correctness/scope concerns first),
`NEEDS_CONTEXT` (supply context, re-dispatch), `BLOCKED` (don't retry blindly:
add context, raise model, split, or escalate).

- The child's **Return is terminal.** Do not poll or hold the session open; the
  parent re-spawns the next Goal with a fresh cold-start prompt.
- Prefer **spawn over resume** for finished leaves; resume only to continue the
  same unfinished Task (`NEEDS_CONTEXT` gap, orchestrator mid-loop). Gap rounds
  are new Tasks, not warm continuations.
- Parents collect Returns and file-handoff paths; leaf transcripts are not
  working memory.

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
| **Model**    | Soft model slot for this child (congruence table), when the harness accepts it               |
| **Effort**   | Soft thinking/effort level (same table), when the harness accepts it                         |

Ask for evidence (file paths, command output, root cause), not vibes. Prefer
non-blocking tasks; await at the collection point. Remind them: no commits, no
worktrees, confirm before protected paths
([`protected-paths.md`](./protected-paths.md)).

> Homelab skills (`implement-change`, `review-loop`, …) are thin and may omit
> contract fields when the parent supplies equivalent context inline. Use the
> full contract for new Task prompts and any multi-agent fan-out.

### Implementer ↔ reviewer pairs

For each **independent** unit of work that needs an independent judge, treat
implementer and reviewer as an **inseparable pair**. Domain reviewers
(`security-analyst`, cold-start Tasks) and lens skills (`review-correctness`,
`review-security`, `review-fit`) fill the **reviewer** slot. Do not invent
parallel role names for the same jobs.

```
implementer → reviewer → pass | gap
                ↑___________|  (new Tasks both sides on gap)
```

- **Same Bar and Artifact; different Goals.** The implementer moves the
  artifact toward the Bar; the reviewer returns `pass` or `gap` (the single
  biggest remaining miss).
- **Implementer never grades itself.** Local smoke checks are not a pass.
- **Reviewer does not inherit implementer rationale.** Give Goal, Bar,
  Artifact, constraints — not the implementer's narrative. Hand the reviewer a
  diff or report file path, not a pasted wall of diff.
- **Don't pre-judge findings** in the reviewer prompt ("don't flag X", "at most
  Minor"). Let the reviewer raise it; adjudicate after.
- **Each round is a new Task for both sides** (one-shot leaves). On `gap`,
  spawn a **new** implementer (gap + Bar + Artifact), then a **new** reviewer.
- **Fan out only independent slices.** Coupled surfaces get one implementer;
  reviewers stay fresh either way.
- **One batch fixer.** After a broad final review returns many findings, spawn
  one fixer with the full list, not one fixer per finding.
- **Pair stop** when the reviewer returns `pass`, or when stop-loss / an
  explicit skill cap / the operator stops the run.

For trivial single-file edits, skip the pair — parent edits and validates.

### Verifier (arbiter)

The verifier is **not** in the pair. It runs **after** the implementer↔reviewer
pair returns `pass` (or after the parent finishes a trivial edit). Prefer the
`/verifier` persona, or run [`config-validate`](../skills/config-validate/SKILL.md)
/ [`review-loop`](../skills/review-loop/SKILL.md) as the arbiter. On **pass**,
continue to operator handoff; on **issue**, fix or escalate — never declare
ready. Unpaired roles (scouts, planners) still fill Goal, Bar, Role, Artifact, and
Return. Their Bar is usually coverage of the scoped sources with evidence.

### Pre-flight before multi-task execution

Before Task 1 of a written multi-task plan, scan once for tasks that
contradict each other or the plan's global constraints. Present every conflict
as **one batched question**; if clean, proceed without comment. Unclear scope
still goes through [`alignment`](../skills/alignment/SKILL.md) first.

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

- Worktrees, `.worktrees/` edits, commits, pushes, PRs (operator-owned).
- Parent implements on a vague ask without alignment; sequential `Read`/`Grep`
  when an explorer subagent fits; blocking when independent work could continue.
- Implementer starts without a Bar; grades its own work against the Bar;
  skipping validation because "it looks fine."
- `/verifier` inside the pair's gap loop; parallel implementers on coupled
  surfaces; skipping the verifier arbiter after the pair returns pass.
- Reusing a finished leaf's context across gap rounds; keeping leaves warm
  after Return.
- Parent pastes subagent output or tool-call narration into the operator reply.
- Every child on the parent model "for quality" when the job is thin; omitted
  model/effort; max thinking on a mechanical scout; cheapest+lowest on subtle
  security review.
- Telling a reviewer what not to flag; one fixer per finding when a single
  batch fixer would do.
