---
alwaysApply: true
description: After 3 failed attempts at the same approach, stop and surface the problem
---

# Stop-loss: 3 retries then stop

If the same task, command, or fix attempt fails **3 times in a row** with the
same approach, **stop**. Do not retry a 4th time.

Surface to the operator:

- What you were trying to do.
- The 3 things you tried and what failed each time (verbatim error if there is one).
- What you'd try next if given approval — but don't actually try it.

Cosmetic flag tweaks count as the same approach. Genuinely different tactics
(different tool, different framing, asking the operator) do not.

Transient flakes (network timeout, rate limit) where the next attempt is the same
call, not a new approach, are exempt from the "different tactic" rule. They are
**not** exempt from the 3-attempt limit: after 3 consecutive failures of the
same call (even if each looks transient), stop and surface.

Matches [`.agents/context/constraints.md`](../context/constraints.md) Performance:
stop after 3 failed attempts; escalate or change strategy.
