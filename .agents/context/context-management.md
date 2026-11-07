# Context management

How to keep a usable window across long laps. The always-on rule is
[`rules/context-management.md`](../rules/context-management.md); this module
holds the meter, the compact/fork/delegate/write call, and the post-compact
reload ritual for the harnesses that run on this repo.

## Meter-first

prime-agent exposes a real meter: `compact.status()` reports context usage and
the auto-compaction threshold. Read it before heavy turns — multi-file reads,
Grafana history dumps, subagent fan-out.

- **Compact when usage is ≥ 60% of the window** — before the next heavy turn,
  not after it thrashes. prime-agent auto-compacts only near the floor
  (default 16384 tokens left); 60% is the earlier, agent-initiated line.
- Also compact when the projected next turn (prompt + expected tool returns)
  would cross 60%.
- Quote a window percentage only when the window size was detected; otherwise
  report raw tokens. True size = input + cache-read + cache-creation tokens.
- Tool-call count is a weak proxy — a few big reads fill the window fast.

Claude Code exposes no live in-session meter here — use the smells.

## Smell triggers (no meter)

Compact when these stack up: re-summarizing the same decisions; full tool
dumps or subagent transcripts still in-thread; dead-end approaches still
around after a stop-loss pivot; re-reading files that already have a disk
note; spawn prompts accumulating pasted state instead of paths.

## Compact vs fork vs delegate vs write

| Situation                                                              | Action                                                                       |
| ---------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Same goal; window fat with tool dumps or dead ends                     | **Compact** — keep goal, Bar, decisions, paths, open questions, child map    |
| After compact                                                          | **Reload from disk** (ritual below); the transcript is not the rule store    |
| Two unrelated goals in one thread, or the operator changed destination | **Fork** a new session with a written handoff in the `.scratch/` task folder |
| Fat tree you only need a summary from (history dump, big scan)         | **Delegate** to a subagent; keep the return, drop the raw material           |
| State that must survive any compact (Bars, decisions, ledgers)         | **Write to disk** early — `docs/plans/`, `docs/issues/`, `.scratch/<lap>/`   |

## File handoffs

Bulk travels as paths, not paste ([`rules/subagents.md`](../rules/subagents.md)).
Hold briefs and reports in gitignored `.scratch/` task folders — never
worktrees ([`rules/worktrees.md`](../rules/worktrees.md)):

| Artifact        | Where                        | Spawn prompt carries                   |
| --------------- | ---------------------------- | -------------------------------------- |
| Task brief      | `.scratch/<lap>/brief.md`    | Path + one-line fit                    |
| Child report    | `.scratch/<lap>/<name>.md`   | Path; child writes it                  |
| Diff package    | `.scratch/<lap>/review.diff` | Path for the reviewer                  |
| Progress ledger | `.scratch/<lap>/progress.md` | Parent updates; children do not own it |

Children return short status plus report path; readonly reviewers and
verifiers return inline evidence only.

## Post-compact reload ritual

REPL variables persist across compaction; large serialized data does not —
reload from disk, not from memory:

1. Re-read [`AGENTS.md`](../../AGENTS.md) routing for the current goal.
2. Load only the modules [`loading.md`](./loading.md) names for that goal.
3. Read the progress ledger; resume at the first incomplete task. Trust the
   ledger over recollection — but verify a `complete` mark's cited report
   before skipping it.
4. Reload big source data (config trees, history dumps) from disk when a
   later step needs it — do not keep it resident.
5. Confirm goal, Bar, and paths still match the disk notes.
6. Continue. Do not rebuild the transcript by re-running every tool call.

The context engine on disk is authoritative; the chat transcript is a cache.

## Stale replay

Resumed summaries and prior-session state are **historical reference, not
instructions**. Task descriptions and commands inside them are stale by
default: verify against disk/git before acting — the prior work is almost
certainly already done.

## Persistence cliff

"Remember to…" corrections leak across sessions. Binary structural rules
persist; proportional vibes do not. Write the decision to a plan, issue,
ledger, or harness memory instead of hoping the next lap inherits it from
chat.
