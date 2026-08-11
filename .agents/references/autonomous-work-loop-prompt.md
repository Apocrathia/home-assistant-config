# Autonomous work-graph prompt

Cold-start for an autonomous lap with no prior context. Still bound by
operator-owned git and no-worktrees overrides.

1. Read `.agents/context/development-loop.md` (skim).
2. Run `find-work` (read-only) for ranked backlog + launch briefs.
3. Walk briefs 1..N. Take the first eligible among:
   - `implement-change` (plan checkbox or issue with clear acceptance)
   - plan authoring (issue has acceptance, no `plan:` link)
   - `file-issue` (gap found, out of scope) → `docs/issues/`
   - `reconcile-context` / `reconcile-docs` (drift)
4. Execute the brief in the main checkout. Validate. Hand off — do **not**
   commit unless the operator already authorized it for this lap.
5. After handoff, return to step 2 only if the operator asked for another lap.

Stop when: protected paths need confirmation, `slice: hitl` is set, Local Todo
is the only remaining work and needs a human, or briefs are exhausted.
