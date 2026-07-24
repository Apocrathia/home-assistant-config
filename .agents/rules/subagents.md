---
alwaysApply: true
description: Delegate work to subagents early and often; parallelize by default
---

# Subagents

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

| Agent                  | When                                                    |
| ---------------------- | ------------------------------------------------------- |
| `ha-config-expert`     | Deep HA configuration, packages, entities, traps        |
| `automation-architect` | Complex automation design (triggers/conditions/actions) |

Invoke by name or delegate explicitly. Run independent agents in parallel in one
message when fan-out helps.

## When to stay in the parent

- Single known file, single edit, no discovery — parent may edit directly.
- User asked you not to delegate.
- Subagent would need conversation context the prompt cannot carry (rare; write
  a detailed cold-start prompt instead).

## Prompt hygiene

Subagents start cold. State goal, constraints, paths, and what to return.
Ask for evidence (file paths, command output, root cause), not vibes.
Remind them: no commits, no worktrees, confirm before protected paths
([`protected-paths.md`](./protected-paths.md)).

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
- Implementer starts without acceptance criteria or file paths from the parent.
- Skipping validation because "it looks fine."
- Parent pastes subagent output or tool-call narration into the operator reply.
- Committing, pushing, or opening PRs (operator-owned).
