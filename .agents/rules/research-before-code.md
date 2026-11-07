---
alwaysApply: true
description: Search prior art before writing net-new code; prefer adopting or porting a proven implementation; record the search
---

# Research before net-new code

Research-and-reuse discipline adapted from [ECC](https://github.com/affaan-m/ECC) (MIT),
`rules/common/development-workflow.md`.

Before writing a new utility, integration, or skill from scratch, search for
prior art. Prefer adopting or porting a proven implementation over net-new code
when it meets the requirement. Search in this order:

1. **This repo.** A helper, script, dependency, or skill that already does the
   job.
2. **The language's package registry.** A maintained, widely used library over
   a hand-rolled version of anything nontrivial.
3. **Public open source.** Search public repositories for implementations that
   solve most of the problem and can be forked, ported, or wrapped. A
   battle-tested skeleton or reference project is a valid foundation: clone the
   best match and iterate within its structure.
4. **Vendor docs.** Confirm API behavior and version-specific details from
   primary documentation before implementing.

Record the search in one line in the lap's notes (`.scratch/` status report or
`docs/plans/` entry): what you found and adopted, or that you found nothing.
Nothing found is a valid result; it is what licenses writing net-new code.

In-repo reuse is rung 2 of the ladder in
[`surgical-edits.md`](./surgical-edits.md); this rule extends the search past
the repo boundary.
