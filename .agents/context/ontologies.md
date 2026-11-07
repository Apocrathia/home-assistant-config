# Ontologies

The schema behind the agent's durable harness state: what classes of entries
exist, how they relate, and the validation rules checked before acting. The
domain: how agents work on the Home Assistant Homelab and what they must not
get wrong. Normative rule: [`rules/ontology-framework.md`](../rules/ontology-framework.md).

## Entry classes

| Class          | Holds                                                                                               | Agent behavior                                  |
| -------------- | --------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| `Memory`       | Durable facts: HA entity behavior, tool contracts, 1Password/ESO facts                              | Load and follow; do not re-derive               |
| `PromptNote`   | Behavioral constraints: output shape, interaction rules, work style                                 | Apply every session; overrides defaults         |
| `Skill`        | Reusable procedure — e.g. `config-validate`: target → syntax → refs → duplicates → secrets → report | Follow the SKILL.md protocol; no ad-hoc variant |
| `SubagentSpec` | Delegation pattern: role, goal, Bar, artifact, return                                               | Spawn matching the spec                         |

## Properties

prime-agent harness entries carry `id`, `kind`, `title`, `content`, `path`
(category), `scope` (local/global), `source` (agent/refine), timestamps, and
`version`. Model new entries on:

```
scope: local | global
path: general | policy | <domain>   (e.g. environment/1password)
staleness: evergreen | dated: YYYY-MM-DD
provenance: session-id | plan/issue path
```

## Relationships

```
Memory -contradicts-> Memory        (resolve before acting)
Memory -overrides-> Memory          (resolved contradiction; winner takes all)
Memory -specializes-> Memory        (specific entry refines a general one)
Skill -requires-> Memory            (procedure assumes the fact)
Memory -evidences-> session | plan | issue
```

## Validation rules (R1–R6)

One line each; full text in [`rules/ontology-framework.md`](../rules/ontology-framework.md):

- **R1 — No silent contradiction.** Overlapping memories must not conflict
  without an `overrides` edge; flag both, act on neither until resolved.
- **R2 — Constraint vs fact.** A Memory is a factual claim and never
  overrides a PromptNote; a PromptNote makes no factual claims.
- **R3 — Evidence for security claims.** A security-tagged memory without
  provenance is downgraded and flagged.
- **R4 — Staleness expiry.** A dated entry past expiry re-verifies before it
  loads — confirm with the operator or find a current source.
- **R5 — Delegation contract match.** A spawn prompt for a task with a
  matching spec includes Goal, Bar, Role, Artifact, Return.
- **R6 — Skill over ad-hoc.** A skill-covered task uses the skill's protocol.

## HA domain examples

Real entries, kept as shape examples — retire when stale:

```
Memory: grafana_is_the_ha_history_source
  scope: global | path: environment/influxdb | evergreen
  content: "Past HA entity state lives in Grafana datasource uid
  `homeassistant` (InfluxQL) — never via HA MCP."
  evidences: context/tools.md
```

```
PromptNote: adhd_output_shape
  scope: global | path: operator-preferences
  content: "Paragraphs ≤3 lines; lists ≤5; answer first; bold open asks;
  tables only when the table is the answer." (behavioral constraint — R2)
```

```
Memory: eso_1password_pushsecret_item_category
  scope: global | path: environment/1password | dated
  content: "ESO hardcodes item category SERVER on create; API_CREDENTIAL
  needs out-of-band pre-create."
```

SubagentSpec example: the `pattern-analyst` ↔ `pattern-reviewer` pair under
`.agents/agents/` — implementer/reviewer roles, readonly, Bar from
`pattern-mine`, artifact and return shapes fixed in their `agent.md` files.

## Routing

| If you're…                    | Read                                              |
| ----------------------------- | ------------------------------------------------- |
| Proposing a new harness entry | This module + R1–R6 against same-domain entries   |
| Seeing two memories conflict  | R1 — flag both; `overrides` edge or delete one    |
| Unsure Memory vs PromptNote   | R2 — behavioral rule = PromptNote; claim = Memory |
| Writing a delegation prompt   | R5 — check `.agents/agents/` for a spec           |
| A task matches a skill        | R6 — use the skill's protocol, not an ad-hoc one  |
