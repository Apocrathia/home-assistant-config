---
alwaysApply: true
description: Prove what you can from available data before asking the user. Bring only genuinely unanswered questions.
---

# Ground before asking

Before surfacing questions to the user: prove what you can from the data provided
(packages, docs, configs, entity patterns, the disk). Say what you don't know.
Bring only what's genuinely unanswered. Do not ask the human things you can
concretely, reliably, honestly answer yourself from the project's documented
truth — including [`.agents/context/`](../context/) and package conventions.

Pairs with [`clarify-dont-guess.md`](./clarify-dont-guess.md): that rule handles
irreducible ambiguity; this rule handles avoidable questions. Prefer
[`.agents/context/questions.md`](../context/questions.md) for HA-specific
ask-vs-infer guidance.
