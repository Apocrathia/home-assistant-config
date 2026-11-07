---
alwaysApply: true
description: Harness entry classes (Memory, PromptNote, Skill, SubagentSpec) and validation rules R1-R6
---

# Ontology framework

The agent's durable harness state (memories, prompt notes, skills, subagent
specs) uses four entry classes. Before every response or tool call, check the
six validation rules (R1-R6) against the loaded entries.

## Entry classes

| Class        | Holds                                                                            |
| ------------ | -------------------------------------------------------------------------------- |
| Memory       | Durable facts: policies, domain facts, tool contracts, workflow rules            |
| PromptNote   | Behavioral constraints: output format, interaction rules, work-style preferences |
| Skill        | Reusable procedure: protocol for a multi-step task                               |
| SubagentSpec | Delegation pattern: role, goal, bar, artifact, return shape                      |

The full schema (properties, relationships, domain examples) and domain
entries live in [`.agents/context/ontologies.md`](../context/ontologies.md).

## Validation rules

Before acting, check these:

**R1 — No silent contradiction.** Two memories with overlapping domains must
not contradict without an explicit `overrides` edge.

**R2 — Constraint vs fact.** PromptNotes are behavioral constraints. Memories
are factual claims. A Memory may never override a PromptNote.

**R3 — Evidence for security_policy.** Any Memory tagged `security_policy`
must have at least one `evidences` edge. Without provenance, downgrade to
`domain_knowledge` and flag.

**R4 — Staleness expiry.** A `dated` entry past its expiry must not be loaded
without re-verification (confirm with user or find a current source).

**R5 — Delegation contract match.** When spawning a child where a matching
SubagentSpec exists, the spawn prompt must include all spec fields (Goal, Bar,
Role, Artifact, Return). Missing fields are an error.

**R6 — Skill over ad-hoc.** When a task matches a Skill by domain and action
type, use the skill's documented protocol. Do not invent an ad-hoc workflow.
