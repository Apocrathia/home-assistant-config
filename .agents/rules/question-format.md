---
alwaysApply: true
description: Context → Ask → Suggestion or Strawman → Gaps format for non-trivial questions
---

# Question format

When you surface a non-trivial question or decision point and no
structured-question tool applies, use this layout per item. Order is fixed.
Also see [`.agents/context/questions.md`](../context/questions.md) for when
to ask vs. when to infer.

**Context:** Why this matters. 1-3 sentences. What's at stake.

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

## Prefer the structured-question tool when present

When the tool list includes a structured-question / interview tool (often
something like `AskQuestion`) and the decision has 2-4 discrete options,
**call it**. Do not replace it with numbered option lists or multiple prose
Ask blocks. Do not hard-require a specific tool name; if it is absent, fall
back.

Independent discrete choices may share **one** structured-question turn. If an
answer gates later asks, ask one, wait, continue.

If no structured-question tool is in the tool list, do not invent the call and
do not hunt the filesystem or MCP catalog for it. Use one prose Ask (above) and
stop.

Trivial single-concern factual questions ("did you mean `kitchen.yaml` or
`office.yaml`?") don't need the structure.

## Forbidden

- Multiple `Context -> Ask -> Suggestion` stacks in one chat reply
- Restating structured-question tool options as a markdown wall under the tool
  call

## Alignment and grilling

**One decision per turn** by default: ask, wait for the operator's answer,
then ask the next. Batching several questions into one turn is for
**independent factual gaps** only, with one exception:
[`/alignment`](../skills/alignment/SKILL.md) runs **frontier rounds** (all
questions whose prerequisites are settled, in one numbered round with
recommendations; dependent questions wait for later rounds). Dependent
design decisions still get one question per turn everywhere else. Presenting
options for a decision is fine; stacking dependent questions bewilders
instead of aligning.
