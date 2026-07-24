---
description: Stop and confirm before editing agent-steering surfaces or HA critical paths
alwaysApply: true
---

# Protected paths

These paths steer the agent stack or the live Home Assistant instance. A careless
edit propagates. Before editing any of them, **name the path and surface the
change; don't apply until the operator confirms.**

## Agent steering

- `AGENTS.md`, `CLAUDE.md`
- `.agents/**` — context, skills, agents, rules, references (canonical source;
  Cursor shim `.cursor/rules/homeassistant.mdc` points here — don't break routing)
- `.cursor/hooks.json`, `.cursor/hooks/**`
- `.cursor/README.md`

## Home Assistant critical

- `configuration.yaml` — main entry point (packages include)
- `secrets.yaml` — credentials (use `!secret`; never hardcode)
- `.storage/` — HA runtime state (**never edit**; managed by Home Assistant)
- `packages/system/` — core HA system management packages
- `.shopping_list.json` — read-only work source (see
  [`work-sources.md`](../context/work-sources.md)); never write

## Confirmation

If a task already has an approved plan that names one of these paths, that's the
confirmation — still name the path before you write.

Edits here do not imply git actions. Shipping stays operator-owned
([`operator-owned-git.md`](./operator-owned-git.md)).
