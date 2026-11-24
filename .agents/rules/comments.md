---
description: Comments and docs state current durable facts; git history carries the why.
alwaysApply: true
---

# Current state only

Code, configuration, and docs state current, durable facts. Git history
carries the why. If a reason is not findable in the commit that made the
change, it belongs in the commit message, not in the artifact.

## Comments

- **Show current state only.** When removing something, delete the lines
  outright; never leave "removed because <reason>" blocks or commented-out
  code with notes.
- **No history or rationale comments** ("pinned back to X because
  <incident>", "changed from Y on <date>", "kept this way after <bug>").
- **Allowed:** comments documenting live semantics the reader needs to use
  the value correctly (field meaning, operating constraints, a non-obvious
  contract), and tooling directive lines (formatters, dependency bots).
  Test: history explains how the value got there; semantics explain what it
  does.
- **No dated witnesses.** "As of <date>", "verified live <date>",
  "relocated on <date>" rot immediately. State the fact, or mark the gap
  once; never record the observation date.
- **No incident narration** attached to durable rules or config. "Same
  rule as the <incident> outage" becomes the rule itself.

## Docs

- Do not describe problems that were fixed or improvements that were made;
  future readers (and agents) lack that context. Git history carries it.
- Do not duplicate change-liable values (versions, limits, intervals,
  rosters, addresses) in prose. They drift. Point at the file that owns
  the value instead.
- Do not narrate cross-system architecture in every touched file; the
  story lives once, in the owning doc.
