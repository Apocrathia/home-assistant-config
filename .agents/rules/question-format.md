---
alwaysApply: true
description: Context → Ask → Suggestion → Gaps format for non-trivial questions
---

# Question format

When you surface a non-trivial question or decision point, use this layout per
item. Order is fixed. Also see [`.agents/context/questions.md`](../context/questions.md)
for when to ask vs. when to infer.

**Context:** Why this matters. 1–3 sentences. What's at stake.

**Ask:** The explicit question. **Bold**, on its own line, never buried in a
paragraph.

**Suggestion:** Your recommendation with brief reasoning. If you have no preference,
say so.

**Gaps/concerns:** What you couldn't verify or what could go wrong. Omit the block
if there are none; don't write "none".

## Tool choice

Prefer the IDE's `AskQuestion` affordance for 2–4 discrete options. Use prose for
open-ended questions or when threading multiple related items.

Trivial single-concern factual questions ("did you mean `kitchen.yaml` or
`office.yaml`?") don't need the structure — short options are enough.
