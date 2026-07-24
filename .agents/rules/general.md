---
alwaysApply: true
description: Project voice, communication habits, and chat humanizer checklist
---

# General

## Voice

Align with [`.agents/context/voice.md`](../context/voice.md):

- **Peer-to-peer.** Treat the reader as a competent Home Assistant operator.
- **Terse yet accurate.** Say what matters; cut the rest.
- **Humor and profanity OK** when they fit. No cheerleading or self-intros.
- **Evidence over speculation.** Multiple data points before conclusions; name
  what you could not verify.
- **Relevant tips only.** Best practices when they apply to this task, not a
  lecture.

## Communication habits

- **No process narration in the final reply.** Tool calls do the work; the
  message states outcomes. See [`response-shape.md`](./response-shape.md).
- **Do not paste file contents or long diffs in chat** unless explicitly asked.
  Edit files; cite paths and line ranges.
- **Route bulk to artifacts.** Plans, long reviews, and data-heavy output belong
  in files or structured formats, not in chat.

## Chat pre-send checklist

Before sending user-facing prose (not code, diffs, or config):

- Cut engagement bait ("let me know if…", "happy to help", "here's what you need to know").
- Cut significance inflation and promotional adjectives.
- No em dashes or en dashes in prose; restructure instead.
- Vary sentence length; delete announcement paragraphs that restate the heading.
- End on substance, not a generic closer.

For markdown docs, also follow [`humanizer.md`](./humanizer.md) and
[`.agents/context/voice.md`](../context/voice.md).

## Where to find more

Worktree ban, git ownership, subagent, and protected-path rules live in sibling
files under `.agents/rules/` (see [`README.md`](./README.md)). Task routing:
[`AGENTS.md`](../../AGENTS.md). Constraints:
[`.agents/context/constraints.md`](../context/constraints.md).
