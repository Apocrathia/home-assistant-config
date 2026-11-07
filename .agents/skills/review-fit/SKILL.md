---
name: review-fit
description: >-
  Read-only design-fit lens for a branch diff, uncommitted changes, or named
  Artifact. Use when review-loop spawns the fit pass, or when asked for an
  architecture fit review, scope check, or coupling review on a diff.
disable-model-invocation: true
---

# Review fit

Read-only lens: design fit, boundaries, and scope against existing architecture.
Return `pass` or numbered findings. Do not edit files, commit, push, or invoke
named review CLIs.

Called by [`review-loop`](../review-loop/SKILL.md) or standalone. Isolation uses
**task folders** when the parent needs a sandbox; do not require worktrees.

For deep exploration that files follow-up notes instead of loop findings, see
[`architecture-review`](../architecture-review/SKILL.md). This lens judges
the current Artifact for merge readiness.

## Soft model slot

**Different mid/light.** Use a distinct slot from correctness and security
(prefer mid or light with strong context reading). Do not default-inherit the
parent model when the harness exposes a separate slot.

## Persona

Load the repo's architect persona (`.agents/agents/architect/agent.md`)
when present.

**Fallback (inline):** Judge design fit only. Read surrounding modules and
layout conventions. Flag coupling, boundary violations, and scope creep with
evidence. No edits, no fixes, no self-grade.

## Bar

**Design fit:** the change belongs in the codebase as structured: right
boundaries, acceptable coupling, and intent/scope aligned with existing
architecture and project layout. Actionable means a concrete misfit that will
slow the next change or duplicate a home for the same concept.

Out of scope: logic bugs (`review-correctness`), security defects
(`review-security`), style-only nits, and pre-existing debt untouched by the
Artifact unless the diff makes it worse.

## Artifact

Parent or operator supplies:

| Field      | Meaning                                                      |
| ---------- | ------------------------------------------------------------ |
| Repository | Absolute repo root                                           |
| Scope      | Branch diff (default), uncommitted only, or named paths      |
| Base       | Merge base branch when scope is branch diff                  |
| Slice      | Optional label (e.g. `review-loop/2`) for fresh Task context |

Orient from `AGENTS.md`, project layout modules when present (for example
`.agents/context/layout.md`), and neighbors of
changed files before judging fit.

## What to judge

- Wrong layer or module: transport logic in domain, policy in UI, etc.
- New coupling across seams that should stay separate
- Duplicate homes for the same topic (layout violations, second bucket)
- Scope creep: drive-by refactors or features outside stated intent
- Shallow boundaries: interface as large as implementation with no test seam
- Missing extension point when the change clearly forks an existing pattern
- Ticket or bucket placement wrong for what the diff actually does

Prefer one clear finding over a laundry list of taste disagreements.

## Task prompt (when parent spawns)

Use the contract in [`.agents/rules/subagents.md`](../../rules/subagents.md):

```text
Slice: <slice or review-fit>
Role: reviewer
Goal: Judge the Artifact against the design-fit Bar. Return findings only.
Bar: design fit; boundaries, coupling, and scope aligned with existing architecture
Artifact: <repository>; scope <branch diff | uncommitted | named paths>
Repository: <absolute path>
Checkout: <absolute main-checkout path>
Scope: <branch diff against base | uncommitted | paths>
Base: <base branch if branch diff>
Task folder: <absolute task folder path when parent binds one>
Report path: <task-folder>/iter-<N>-fit.md

Constraints:
- Read-only. Do not edit files (except writing the named report).
- Do not run named review CLIs.
- Load persona from .agents/agents/architect/agent.md when present.
- Write the full report to Report path; return short status + report_path.

Return (short):
## Fit
result: pass | gap
report_path: <absolute path>
findings: numbered list (path, line/area, severity, summary)  # full body in report
errors: … (if blocked)
```

## Return

Write the long report to the parent-named task-folder path
(`iter-<N>-fit.md` when following review-loop). Return a short status plus
`report_path`; do not paste the full report into chat.

**Pass:** `result: pass`, `report_path`, and a one-line confirmation.

**Gap:** numbered findings in the report. Each finding includes:

1. **Path** and **line/area**
2. **Severity:** blocker | major | minor
3. **Summary:** one line
4. **Full body:** misfit, affected boundary, and a minimal direction (not a full redesign)

Parent triages valid / wrong / unsure. This lens does not fix or re-run itself.

## Do not

- Edit, format, or commit in this skill
- Invoke named review CLIs or substitute them for reading the Artifact
- File correctness or security findings (other lenses own those Bars)
- Require worktrees; task folders are enough when isolation is needed
