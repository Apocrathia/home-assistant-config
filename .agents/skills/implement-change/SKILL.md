---
name: implement-change
description: >-
  One change lap for Home Assistant Homelab: scope, edit, validate, hand off
  with a suggested Conventional Commit. Use when implementing a config fix,
  package change, plan checkbox, or agent-context update.
disable-model-invocation: true
---

# Implement change

One logical change from request to **operator handoff**. Edit only in the main
checkout ([`worktrees.md`](../../rules/worktrees.md)). Do **not** commit, push,
or open PRs unless the operator explicitly asks
([`operator-owned-git.md`](../../rules/operator-owned-git.md)).

## Scope

| Surface                              | Route                                                                      |
| ------------------------------------ | -------------------------------------------------------------------------- |
| YAML packages / `configuration.yaml` | edit here; validate via [`config-validate`](../config-validate/SKILL.md)   |
| Package layout                       | [`package-organize`](../package-organize/SKILL.md)                         |
| Broken automations                   | [`automation-debug`](../automation-debug/SKILL.md)                         |
| Docs issue / plan checkbox           | implement slice; update plan checkboxes; delete-on-ship via reconcile-docs |
| Fuzzy scope                          | [`alignment`](../alignment/SKILL.md) first, then stop for operator         |

Load context as needed: `.agents/context/{constraints,traps,nomenclature,output,questions,vertical-slices,development-loop}.md`.

**Secrets:** never hardcode; use `!secret`. **Automations:** modern keys
(`triggers` / `conditions` / `actions`; item keys `trigger:` / `action:`).
**YAML:** 2-space indent.

Plan/issue templates: `docs/plans/_template.md`, `docs/issues/_template.md`.

Ignore upstream steps that require worktrees or agent commits.

## Workflow

```
- [ ] 1. Frame scope (one change, done conditions; link issue/plan if any)
- [ ] 2. Edit in place (packages/, esphome/, docs/, .agents/ as needed)
- [ ] 3. Validate (config-validate + HA-oriented checks)
- [ ] 4. Update plan checkboxes / reconcile-docs if acceptance met
- [ ] 5. Hand off — stop for operator
```

### 1. Frame scope

One sentence goal + done conditions. Prefer one vertical slice
([`vertical-slices.md`](../../context/vertical-slices.md)). If two unrelated
outcomes, split. Protected paths need confirmation
([`protected-paths.md`](../../rules/protected-paths.md)).

### 2. Edit

Make the minimal change. Prefer existing package patterns under `packages/`.

### 3. Validate

Follow [`config-validate`](../config-validate/SKILL.md). For automations, also
check entity refs and modern key usage.

### 4. Docs ledger

If working from a plan: tick completed checkboxes. If acceptance on the linked
issue is fully met, run [`reconcile-docs`](../reconcile-docs/SKILL.md)
delete-on-ship in this change.

### 5. Hand off

```markdown
## Implement change

**Goal:** <one sentence>
**Paths:** <files>
**Issue/plan:** <paths or none>
**Result:** ready for operator | blocked

### Validation

- <checks run + outcome>

### Suggested commit

`<type>(<scope>): <description>`

### Operator next

- Apply / reload HA as needed, validate live, then commit
```
