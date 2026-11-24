---
alwaysApply: true
description: Ultra-short scannable replies; answer first, bulk in files, no interview walls
---

# Response shape

The operator cannot read at agent speed. Default to scannable output. Full
reply-shape contract: [`.agents/context/output.md`](../context/output.md);
voice: [`.agents/context/voice.md`](../context/voice.md).

## Non-negotiables

- **Lead with the answer** in 1-3 sentences. No throat-clearing.
- **Prefer bullets** over paragraphs. Cut restating the task or the prompt.
- **Half-screen rule:** longer than that → file under `.scratch/` and link.
  Chat stays the index.
- **Questions:** [`question-format.md`](./question-format.md). No multi-Ask
  markdown dumps.
- **Subagents:** summarize; never paste the full child output.
- **Structured output** (JSON/YAML/fixed schema): emit the payload only; no
  prose prepend unless the schema asks for it.
- **Omit:** tool narration, diff replay, question restatement, announcement
  sections.

## Hard caps

Operator-ratified numeric caps — on by default in every reply, no invocation
needed. These bind alongside the sections above:

1. Paragraphs ≤ 3 lines; one idea per line where possible. No prose walls.
2. Lists ≤ 5 items; split into do-now vs later when longer.
3. Lead with the answer or decision. Never open with context prose.
4. Restate any still-open question **in bold** in every reply until it is
   answered.
5. Tables only when the table **is** the answer. Never bury a decision or an
   ask inside, under, or after a table.
6. Long detail goes to a disk file with a link; chat stays the index.

Pre-send check: first line = what happened / the answer; last line = the next
action or the open ask. If not, reshape before sending.

## Length by task type

| Task                            | Shape                                                 |
| ------------------------------- | ----------------------------------------------------- |
| Trivial (yes/no, single lookup) | Short paragraph                                       |
| Implementation done             | Summary + paths touched + validation result           |
| Exploration                     | Bullets: path, line range, finding. Not a prose tour. |
| Review                          | Numbered findings with severity. No preamble essay.   |
| Multi-step work                 | Summary + bullets. Not a play-by-play of tool calls.  |

Match depth to complexity. A one-line YAML fix does not need five paragraphs.

## After implementation

Summarize what changed and suggest a Conventional Commit message. Do not commit
([`operator-owned-git.md`](./operator-owned-git.md)).
