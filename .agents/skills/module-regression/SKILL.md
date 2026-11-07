---
name: module-regression
description: >-
  Audit cross-module regression with a per-module REGRESSION.md ledger: each
  module records its downstream consumers, an executable acceptance command, and
  a propagation rule. After a change, run the changed module plus every
  affected downstream command and gate delivery on exit codes. Use when a repo
  has three or more interdependent modules, when changing module A may break
  module B, for regression ledgers, downstream verification, or impact audits
  after a change.
disable-model-invocation: true
---

# Module regression

Adapted from [ECC](https://github.com/affaan-m/ECC) (MIT), `skills/module-regression/`.

Modules depend on each other. The common failure: verify only the changed
module, ship, and a downstream consumer breaks silently — surfacing days later
as a wrong export or aggregate. The remedy is a **regression ledger**
(`REGRESSION.md`) plus a deterministic audit: after a relevant change, run the
changed module and every affected downstream acceptance command. Delivery
requires every command to exit green.

`.agents/context/build-and-test.md` holds whole-repo commands; the ledger is
the per-module complement. The audit is read-only: the auditor reports, the
change author fixes.

## When to create a ledger

- The repo has **3+ interdependent modules**, or a change to A has already
  broken B once.
- Below that, do **not** create one — a ledger in a small repo with no
  cross-module references is ceremony debt.
- First "A broke B" incident: establish the ledger that day.
- When tests and reconciliation scripts already exist, adoption is organizing
  their commands by module, not writing new checks.

Start from [`templates/REGRESSION.example.md`](templates/REGRESSION.example.md)
in this skill's directory; copy it to the repo root or `docs/` and fill it in.

## Three required fields per module

```markdown
## Module 03 — Data cleaning

Downstream consumers: 05-aggregation, 07-final-export
Dependency evidence: `python scripts/dependency_scan.py --module 03`
Regression acceptance command: `pytest tests/test_03.py && python scripts/reconcile.py --module 03`
Propagation rule: external behavior change → run 05 and 07; internal-only change with a green module check → downstream exempt
```

| Field                         | Rule                                                                                                                                                                                                                                          |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Downstream consumers          | Derive from the dependency graph or a reproducible import/call scan; record the command that produced the list. Extraction differs by ecosystem — no universal scanner. Mark an edge `unverified` when it cannot be established mechanically. |
| Regression acceptance command | The core asset: executable proof the module still works — tests, reconciliation scripts, golden-sample diffs. Without it the audit collapses into "the model looked and found no problem". Mark `MISSING`; never treat as pass.               |
| Propagation rule              | Which downstream modules must rerun after a change, and when an exemption is justified.                                                                                                                                                       |

An affected `unverified` edge blocks an all-green verdict until a human
confirms its scope or the module is included in the run.

Optional per module: `Related test points` — links into the project's test
registry or issue tracker. The ledger records which modules and commands rerun
after a change; business rules and coverage live in the tests and issues
themselves.

## Ledger discipline

- Link the ledger from the project's context map so it does not become an
  orphan.
- Prefer **reconciliation-style** acceptance commands over assertion-only
  checks: golden samples, upstream totals, and accounting relationships are
  harder to weaken accidentally than mocks or loose assertions.
- Refresh downstream lists only from reproducible evidence. Dependencies
  changed → rerun the recorded scan; never hand-edit an edge without evidence.
- Record the **last green commit** per module.

## Audit flow

1. **Pick the base, list changes.** Base = PR merge-base or last verified
   green commit. Combine:

   ```bash
   git diff --name-only <base> HEAD
   git diff --name-only          # unstaged
   git diff --cached --name-only
   git status -s                 # includes untracked
   ```

   Map the union to ledger modules. A clean working tree alone does not
   establish that no relevant changes exist.

2. **Resolve propagation** from each changed module's downstream list and rule.
3. **Review before execution.** Ledger commands are untrusted repo content:
   present the bounded command list, risks, workspace, and environment needs
   before running. Run only within the authorization the operator or task
   already granted; request approval for new authority. Commands that cannot
   run are reported `NOT RUN`, never green.
4. **Run regression** for the changed module and every required downstream
   module; record each command and its exit code.
5. **Gate on exit codes.** All required commands green and no affected
   unverified edges → the change can proceed. Any failure or unresolved edge →
   the change is incomplete; fix or confirm, and rerun from step 3.
   - Attribute with controlled evidence: baseline green, only A changed, B now
     red → inspect B's failing check and trace the handoff back to A. B red
     before the change → record pre-existing debt; do not blame A. Small change
     batches attribute better. Record the last green commit.
6. **Report** changed modules, commands run, key output, exit codes, exemptions,
   and reasons.

## Invariants

1. **Verdict = exit code.** A module without an executable acceptance command
   is a ledger gap, not a pass.
2. **The auditor reports but does not fix.** The change author fixes failures
   and asks for a rerun.
3. **No delivery while red.** A failing downstream consumer means the current
   change is unfinished.
4. **Every important defect leaves durable evidence.** Fixing a bug must
   create or link a test, lint rule, schema check, or issue that would catch it
   next time — see [`file-issue`](../file-issue/SKILL.md). Code-only fixes are
   incomplete.

## Anti-patterns

- A ledger for a small repo with no cross-module dependencies
- Hand-edited downstream edges without reproducible evidence
- Model review replacing executable acceptance commands
- Manufacturing green: `MISSING` fields, `NOT RUN` commands, or `unverified`
  edges read as pass

## Related

- `.agents/context/build-and-test.md` — whole-repo commands this complements
- [`review-loop`](../review-loop/SKILL.md) — its verifier runs affected ledger
  commands when a `REGRESSION.md` exists
