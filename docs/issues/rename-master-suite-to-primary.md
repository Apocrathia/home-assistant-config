---
title: 'Rename Master Bedroom & Bathroom → Primary'
kind: feature
status: open
severity: medium
source: human
found_at: 2026-08-07
area: areas
slice: hitl
plan: docs/plans/2026-08-08-rename-master-suite-to-primary.md
---

# Rename Master Bedroom & Bathroom → Primary

## Problem / desired state

Suite naming still uses “Master …” / `master_*` in entity*ids, device names,
YAML packages, secrets keys, UI references, and nomenclature. Desired state:
“Primary …” / `primary*\*` for both bedroom and bathroom, with entity_ids
moved via the HA registry (not ESPHome hostname hope).

## Repro

N/A — rename / nomenclature work.

## Acceptance

- Tracked repo has no suite Master / `master_bed` / `master_bath` tokens
  outside intentional docs/history exceptions called out in the plan.
- Live entity_ids, device `name_by_user`, and area display names use Primary
  for the suite (operator Phase 2).
- Spot-checks in the linked plan’s verify tasks pass (bedroom + bathroom).

## Feedback loop

- `rg` patterns named in the linked plan
- `config-validate` / HA Check Configuration after YAML deploys
- HA MCP / UI entity and device registry inspection (operator)

## Implementation hint

How-work lives in
[`docs/plans/2026-08-08-rename-master-suite-to-primary.md`](../plans/2026-08-08-rename-master-suite-to-primary.md).
Do not expand this issue into a second plan.

## Notes

Coordinate with in-flight bathroom vanity-clock / IR work so that branch and
this rename do not thrash each other.
