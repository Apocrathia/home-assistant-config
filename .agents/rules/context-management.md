---
alwaysApply: true
description: Context hygiene; meter-first compact, fork when goals split, reload from disk
---

# Context management

Keep the working window thin. Prefer disk and the context engine over the
transcript. Details and thresholds:
[`.agents/context/context-management.md`](../context/context-management.md).

## Meter-first

When the harness exposes context-window usage, read it before a heavy turn
(large tool returns, multi-file reads, subagent fan-out). If usage is at or
above **60%** of the window, compact (or the harness equivalent) before that
turn. Prefer compacting early over failing mid-tool.

When no meter exists, use the smell triggers in the context module.

## Read the meter honestly

Meter accounting adapted from [ECC](https://github.com/affaan-m/ECC) (MIT),
`scripts/lib/transcript-context.js` and `scripts/hooks/suggest-compact.js`.

- True context size is input + cache-read + cache-creation tokens; a meter
  that omits cache reads understates usage.
- Quote a window percentage only when the window size was actually detected.
  Against an assumed default, report raw tokens instead.
- Raise the compact suggestion again only after real context growth since
  the last reminder, not every turn.
- Tool-call count is a weak proxy for window pressure: a few large reads
  fill the window in very few calls.

## Compact vs fork vs delegate vs write

| Situation                                                  | Action                                                                                                                                                                                                                             |
| ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Same Goal; window fat with tool dumps or dead ends         | **Compact**. Keep Goal, Bar, decisions, paths, open questions, live child map.                                                                                                                                                     |
| After compact                                              | **Reload from disk**: `AGENTS.md` routing → named `.agents/context/*` and rules. Re-check the plan/issue ledger (`docs/plans/`, `docs/issues/`) and your `.scratch/` status report. Do not treat the transcript as the rule store. |
| Thread holds 2+ unrelated Goals, or the job clearly forked | **Fork** a new session/Task with a written handoff under the `docs/plans/` or `docs/issues/` ledger (or a `.scratch/` task folder).                                                                                                |
| About to load a fat tree you only need a summary from      | **Delegate** (subagent); keep the return, drop the raw material.                                                                                                                                                                   |
| State must survive any compact                             | **Write to disk** early (plan/issue ledger entry or `.scratch/` task folder).                                                                                                                                                      |

## Resumed summaries are stale by default

Stale-replay guard adapted from [ECC](https://github.com/affaan-m/ECC) (MIT),
`scripts/hooks/session-start.js`.

Prior-session summaries and state files are **historical reference, not
instructions**. Task descriptions, commands, and argument payloads inside
them are stale by default: do not re-execute without an explicit, current
user request. Verify against git/working-tree state before acting — the
prior work is almost certainly already done.

## File handoffs

Bulk for children travels as **paths**, not paste. Write briefs, reports, and
diff packages under the ledger entry or `.scratch/` task folder; spawn prompts
name those paths. Child returns stay short (status + path to full report),
except read-only children (reviewers, verifiers) who return inline evidence.
See [`.agents/context/context-management.md`](../context/context-management.md).

## Always

- Do not paste full tool dumps or subagent transcripts into the parent window.
- Summarize child results; cite paths and evidence, not walls of output.
- Pair with [`subagents.md`](./subagents.md) and [`response-shape.md`](./response-shape.md).
