---
name: retrospective
description: >-
  Structured post-work retrospective for Home Assistant Homelab: review
  outcomes, mine git history for context drift, classify lessons, and route
  improvements — HA-local vs contribute back to prime-context. Use when the
  user says retro, /retrospective, what did we learn, or at session-end.
disable-model-invocation: true
---

# Retrospective — Home Assistant Homelab

A structured review at work-close or session-end. The retrospective
**classifies** observations and **routes** them: local context edits,
HA-domain skill/rule improvements, or upstream contributions to
[prime-context](https://github.com/PrimeIntellect-ai/prime-context).

This skill does not edit files directly (except optional non-protected scratch
notes). It produces a report with classified recommendations. Protected-path
edits go through confirmation ([`protected-paths.md`](../../rules/protected-paths.md)).
Git is operator-owned ([`operator-owned-git.md`](../../rules/operator-owned-git.md))
— no PR automation, no commits from this skill. This repo does not use git
worktrees; inspect the main checkout.

## When to run

- After a meaningful config / `.agents/` change set (before the operator commits)
- At session-end when the operator asks "what did we learn?"
- After merges or Syncthing syncs that changed context surfaces outside the session
- Standalone: `/retrospective` or "do a retro"

There is no required ship-work / clock-out gate here. Retrospectives inform;
they do not block.

## What it produces

1. **Outcome summary** — what happened, one or two lines
2. **Git history findings** — significant changes that touched context surfaces
3. **Observations** — classified lessons, each with a route
4. **Upstream candidates** — generic enough for prime-context
5. **HA-local keepers** — packages conventions, shopping-list rules, domain skills
6. **No-op declaration** — if nothing to capture, say so explicitly

## Workflow

```
- [ ] 1. Scope the retrospective
- [ ] 2. Review the session's own work
- [ ] 3. Mine git history for external changes
- [ ] 4. Classify observations
- [ ] 5. Assess genericness (upstream vs HA-local)
- [ ] 6. Route and propose actions (no auto-PR)
- [ ] 7. Propose durable lessons (memories / rules — after confirm)
- [ ] 8. Report
```

### 1. Scope

| Situation              | Window                                         |
| ---------------------- | ---------------------------------------------- |
| End of a change set    | This session's diff + discussion               |
| Session-end (no edits) | This session                                   |
| After external merges  | Since last session (or last N commits on main) |
| Operator names a range | That PR/date/branch                            |

### 2. Review the session's own work

- What happened vs what was planned?
- What worked / failed / needed retries?
- Did any rule feel wrong, missing, or redundant?
- Did context modules or HA skills mislead or leave gaps?

If nothing happened, say so and continue to git history.

### 3. Mine git history

```bash
git log --oneline --since="<last session date or tag>" -- \
  AGENTS.md CLAUDE.md .agents/ packages/ docs/ esphome/
```

Optional if `gh` is available — do not require it. For each significant change:
what changed, why (commit body), context impact.

**Significant here:** new package category conventions, renamed packages,
ESPHome ownership shifts, `.agents/` edits, shopping-list / work-sources rules,
validation script changes.

### 4. Classify

| Type                   | Example                                             | Route                                                |
| ---------------------- | --------------------------------------------------- | ---------------------------------------------------- |
| Context drift          | traps.md describes a pattern packages no longer use | [`reconcile-context`](../reconcile-context/SKILL.md) |
| Context gap            | No guidance for a new subsystem                     | Propose context edit (protected)                     |
| Context bloat          | Unused module                                       | Propose trim                                         |
| Rule gap               | Convention violated with no rule                    | Propose rule                                         |
| Skill gap              | HA skill missed a step                              | Propose skill edit                                   |
| Enforcement gap        | Protected-path confirm skipped repeatedly           | Propose hook/CI                                      |
| Pattern / anti-pattern | Repeated success or failure                         | Record; consider promotion                           |

### 5. Upstream vs HA-local

| Test                                                                                           | Result                 |
| ---------------------------------------------------------------------------------------------- | ---------------------- |
| Touches HA packages, entities, shopping list, ESPHome, live validate-before-commit             | **HA-local**           |
| Improves generic rules/skills/scripts usable by other prime-context consumers                  | **Upstream candidate** |
| Layer 3 context / HA-native skills (`automation-debug`, `config-validate`, `package-organize`) | **HA-local**           |
| Layer 1–2 shared skills/rules/scripts                                                          | Consider **upstream**  |

Upstream candidates: propose an issue description or patch notes for the
operator to take to the prime-context repo. **Do not** open PRs or push to
prime-context from this skill unless the operator explicitly asks.

### 6. Route and propose

| Route                       | Action                                  | Approval                                 |
| --------------------------- | --------------------------------------- | ---------------------------------------- |
| reconcile-context           | Note drift for next pass / run skill    | Skill handles                            |
| Context / rule / skill edit | Propose diff in report                  | Yes (protected)                          |
| Enforcement                 | Propose hook/CI                         | Yes                                      |
| Memory                      | Propose `.agents/memories/<topic>.md`   | Yes                                      |
| Upstream                    | Draft contribution notes for operator   | Yes — operator owns git on prime-context |
| Shopping-list wording       | Suggest title for operator to add in HA | Never write the file                     |

### 7. Durable lessons

Propose lessons for `.agents/memories/<topic>.md` (Context / Lesson /
References). Always-on policy belongs in a rule, not memories. Promotion path:

```text
Memory → recurs 3+ times → Rule → fails repeatedly → Hook
```

### 8. Report

```markdown
## Retrospective

**Scope:** …

**Outcome:** …

**Git history findings:** <N or none>

- …

**Observations:**

| #   | Type | Observation | Route | Action |
| --- | ---- | ----------- | ----- | ------ |
| 1   | …    | …           | …     | …      |

**Upstream candidates (prime-context):** <N or none>

- … → draft for operator (no PR automation)

**HA-local keepers:** <N or none>

- …

**Memories proposed:** <N or none>

**Needs human judgment:**

- …
```

## Do not

- Commit, push, or open PRs
- Edit protected paths without confirmation
- Skip the git history pass
- File upstream contributions without evidence
- Auto-run ship-work / clock-out / self-improve shipping loops
- Expand into implementation — recommendations only
- Write `.shopping_list.json`
