---
alwaysApply: true
description: Scannable reply structure — answer first, evidence second, bulk in files
---

# Response shape

The operator cannot read at agent speed. Default to scannable output.
Match [`.agents/context/voice.md`](../context/voice.md) and
[`.agents/context/output.md`](../context/output.md) when writing YAML or docs.

## Inverted pyramid

First 1–3 sentences: answer, verdict, or what changed. Supporting detail after,
only if needed.

## Length by task type

| Task                            | Shape                                                 |
| ------------------------------- | ----------------------------------------------------- |
| Trivial (yes/no, single lookup) | Short paragraph                                       |
| Implementation done             | Summary + paths touched + validation result           |
| Exploration                     | Bullets: path, line range, finding. Not a prose tour. |
| Review                          | Numbered findings with severity. No preamble essay.   |
| Multi-step work                 | Summary + bullets. Not a play-by-play of tool calls.  |

Match depth to complexity. A one-line YAML fix does not need five paragraphs.

## Route bulk out of chat

- Plans → plan doc or `docs/`, not a wall of text in the thread
- Large reviews → numbered findings; detail per finding, not upfront
- Data-heavy output → canvas or a file when the product supports it

Chat is the index, not the warehouse.

## Parent and subagent synthesis

When subagents return, summarize outcomes for the operator. Do not restate their
full output. The parent coordinates; it does not hoard context in the reply.

## Structured output overrides shape

When the caller or task requires strict structured output (JSON, YAML, fixed
schema), follow that format. Do not prepend prose or wrap the payload in
markdown unless the schema asks for it.

## After implementation

Summarize what changed and suggest a Conventional Commit message. Do not commit
([`operator-owned-git.md`](./operator-owned-git.md)).

## Omit from final replies

- Tool-call narration ("I read X, then grep'd Y…")
- File-by-file diff replay when a summary suffices
- Repeated restatement of the user's question
- Sections that only announce what the next section will say
