---
name: implement-change
description: >-
  One change lap for Home Assistant Homelab: scope, edit, validate, hand off
  with a suggested Conventional Commit. Use when implementing a config fix,
  package change, or agent-context update.
disable-model-invocation: true
---

# Implement change

One logical change from request to **operator handoff**. Edit only in the main
checkout. Do **not** commit, push, or open PRs unless the operator explicitly
asks. Override:
[`.agents/rules/operator-owned-git.md`](../../rules/operator-owned-git.md).

## Scope

Config and agent work in this repo:

| Surface                              | Route                                                                    |
| ------------------------------------ | ------------------------------------------------------------------------ |
| YAML packages / `configuration.yaml` | edit here; validate via [`config-validate`](../config-validate/SKILL.md) |
| Package layout                       | [`package-organize`](../package-organize/SKILL.md)                       |
| Broken automations                   | [`automation-debug`](../automation-debug/SKILL.md)                       |
| Fuzzy scope                          | [`alignment`](../alignment/SKILL.md) first, then stop for operator       |

Load context as needed: `.agents/context/{constraints,traps,nomenclature,output,questions}.md`.

**Secrets:** never hardcode; use `!secret`. **Automations:** modern keys
(`triggers` / `conditions` / `actions`; item keys `trigger:` / `action:`).
**YAML:** 2-space indent.

Skip upstream swarm paths: no `docs/issues`, `docs/plans`, `sync-main.sh`,
cargo/TDD pipelines, or `ship-work` as a commit gate.

## Workflow

```
- [ ] 1. Frame scope (one change, done conditions)
- [ ] 2. Edit in place (packages/, docs/, .agents/ as needed)
- [ ] 3. Validate (config-validate + HA-oriented checks)
- [ ] 4. Hand off — stop for operator
```

### 1. Frame scope

One sentence goal + done conditions. If two unrelated outcomes, split and run
this skill once each. Protected paths need confirmation
([`.agents/rules/protected-paths.md`](../../rules/protected-paths.md)).

### 2. Edit

Make the minimal change. Prefer existing package patterns under `packages/`
(`areas/`, `functions/`, `integrations/`, `projects/`, `routines/`, `system/`,
`toys/`).

### 3. Validate

Follow [`config-validate`](../config-validate/SKILL.md). For automations, also
check entity refs and modern key usage. For `.agents/` prose, skim links and
naming against context modules.

### 4. Hand off

Stop. Do not run `ship-work` as a commit step — optionally summarize via
[`ship-work`](../ship-work/SKILL.md) (handoff only) when the operator wants a
structured wrap.

```markdown
## Implement change

**Goal:** <one sentence>
**Paths:** <files>
**Result:** ready for operator | blocked

### Validation

- <checks run + outcome>

### Suggested commit

`<type>(<scope>): <description>`

### Operator next

- Apply / reload HA as needed, validate live, then commit
```
