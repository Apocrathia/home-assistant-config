---
alwaysApply: true
description: Ask when ambiguous; distinguish advice from action; permission-question discipline
---

# Clarify, don't guess

When the request has two or more reasonable interpretations, **do not guess**.
Ask per [`question-format.md`](./question-format.md) (prefer the structured-question
tool when it is in the tool list). Prove what you can first; flag irreducible
ambiguity with `[NEEDS CLARIFICATION]` ([`ambiguity-goes-back-to-source.md`](./ambiguity-goes-back-to-source.md)).

## Triggers

- Two valid scopes for the same instruction (e.g. "fix the lights"; which area).
- Two valid approaches with different tradeoffs.
- A constraint that conflicts with another constraint.
- A reference to a file, package, or entity whose identity isn't obvious.
- A success criterion you can't measure without more information.

## Distinguish advice from action

When the operator uses consultative language; "advice", "please advise", "what
should I do", "considering", "thinking about"; provide options and
recommendations only. **Do not implement or mutate repo state** (no edits,
staging, branches, or worktrees). Read-only investigation is allowed
and expected: read files, run diagnostic commands, reproduce behavior. Wait for
an explicit request to implement.

An explicit implement instruction in the same message overrides consultative
phrasing (e.g. "please advise, then fix it" → fix it).

Never treat "implement" as permission to commit or push
([`operator-owned-git.md`](./operator-owned-git.md)).

## Permission-question discipline

If you ask a permission question; "Want me to…?", "Should I…?", "Do you want me
to…?"; **stop and wait for the answer**. Never batch the permission ask with the
action itself. A previous "proceed" on a different topic does not carry forward.

Protected-path edits always need confirmation
([`protected-paths.md`](./protected-paths.md)).

## Extended ambiguity

When ambiguity spans several **dependent** decisions (not one clarify question
or several independent facts), use
[`alignment`](../skills/alignment/SKILL.md) instead of ad-hoc back-and-forth.
Alignment works the decision tree in **frontier rounds**: every question whose
prerequisites are settled goes in one numbered round; dependent questions wait
for later rounds. For several **independent** gaps outside alignment, use one
structured-question turn (or one prose Ask) covering them. Alignment is
read-only until the operator asks to proceed.

## Not ambiguity

Low-stakes details where the choice is unambiguous (one matching package path,
one obvious entity name, ordering of unrelated steps): pick it, mention briefly,
proceed. If multiple files match a path reference, ask; do not default.
