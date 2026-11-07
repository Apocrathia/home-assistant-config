---
alwaysApply: true
description: Context → Ask → Suggestion or Strawman → Gaps format for non-trivial questions
---

# Question format

When you surface a non-trivial question or decision point, use this layout per
item. Order is fixed. Also see [`.agents/context/questions.md`](../context/questions.md)
for when to ask vs. when to infer.

**Context:** Why this matters. 1–3 sentences. What's at stake.

**Ask:** The explicit question. **Bold**, on its own line, never buried in a
paragraph.

**Suggestion:** Your recommendation with brief reasoning. If you have no preference,
say so. For an open-ended ask with no genuine recommendation, replace this block
with **Strawman** (below) — never nest one here, never add a fifth block.

**Gaps/concerns:** What you couldn't verify or what could go wrong. Omit the block
if there are none; don't write "none".

## Strawman drafts

For an open-ended ask (a definition, design, plan, or name), don't just ask.
Commit to a deliberately rough draft, labeled a **strawman**, and invite the
operator to tear it apart: critiquing a concrete artifact is cheaper than
generating from scratch, and a rough draft surfaces the operator's real
criteria faster than an open question.

The strawman **replaces** the Suggestion slot (Context → Ask → Strawman → Gaps).
With a genuine recommendation, keep Suggestion and skip the strawman — a
strawman is for open problems, not a hedge. Passing weak work off as your best
answer destroys trust.

## Tool choice

Prefer the IDE's `AskQuestion` affordance for 2–4 discrete options. Use prose for
open-ended questions or when threading multiple related items.

Trivial single-concern factual questions ("did you mean `kitchen.yaml` or
`office.yaml`?") don't need the structure — short options are enough.
