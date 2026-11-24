---
description: Stop and confirm before editing agent-steering surfaces or HA critical paths
alwaysApply: true
---

# Protected paths

Some paths in this repo steer the agent stack or the live Home Assistant
instance; a careless edit propagates. Before editing **any file or directory**
matching the patterns below, **stop and ask** the operator:

> "About to edit `<path>`; this is a protected path. Confirm?"

Do not proceed until the operator explicitly confirms (e.g. "yes", "approved",
"do it"). A previous "proceed" or "go ahead" on a different topic does **not**
carry forward.

## Agent steering

- `AGENTS.md`: the router every harness reads first.
- `.agents/**`: portable agent config (context, skills, personas, rules,
  references). Silent edits change how every harness behaves.

## Home Assistant critical

- `configuration.yaml` — main entry point (packages include)
- `secrets.yaml` — credentials (use `!secret`; never hardcode)
- `.storage/` — HA runtime state (**never edit**; managed by Home Assistant)
- `packages/system/` — core HA system management packages
- `.shopping_list.json` — read-only work source (see
  [`work-sources.md`](../context/work-sources.md)); never write
- `.storage/local_todo.*.ics` — Local Todo Issues/Tasks/Ideas (same rules;
  never write)

## What "edit" means

- Creating, modifying, deleting, or moving a file inside a protected path.
- Editing **does not** include reading, grepping, or searching; those are always
  fine.

## Operator-initiated edits

When the operator explicitly asks you to change something inside a protected
path ("update the planner agent", "add a new rule"), the request itself is the
confirmation. You don't need a second "are you sure" round-trip, but you do need
to summarize what you're about to change before doing it, so the operator can
stop you if you misunderstood.

Confirmed edits do not imply git actions. Shipping stays operator-owned
([`operator-owned-git.md`](./operator-owned-git.md)).

## Additive

Other rules or future updates can extend this list. They cannot remove paths
from it without explicit operator approval.
