---
title: Pattern analyst ↔ reviewer pair
status: active
found_at: 2026-08-08
updated_at: 2026-08-08
# scaffolding complete; remaining step is operator smoke delegation
area: agents
---

# Pattern analyst ↔ reviewer pair

## Goal

Add a domain-atomic agent pair that mines Home Assistant history for reliable
automation trigger candidates. The parent (or `automation-architect`) briefs a
human timeline or event list; the pair returns evidence-backed candidates only.
YAML design stays with `automation-architect`.

## Scope

**In scope:**

- `.agents/agents/pattern-analyst/agent.md` — Role `implementer` for this domain
- `.agents/agents/pattern-reviewer/agent.md` — Role `reviewer` for this domain
- `.agents/skills/pattern-mine/SKILL.md` — shared mining procedure + default Bar
- Symlinks under `.cursor/agents/` (match existing agents)
- Routing updates: `.agents/rules/subagents.md`, `AGENTS.md` (and `CLAUDE.md` via symlink)

**Out of scope:**

- Automation YAML / package edits for any concrete routine (e.g. Good Morning)
- Declaring live HA config changes
- Absorbing `grafana-ha-history` into this skill (link and invoke it)
- Replacing generic `/implementer` or `/reviewer`

## Decisions

| Decision     | Choice                                                                                | Why                                                         |
| ------------ | ------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| Deliverable  | Candidate triggers only (no YAML)                                                     | Domain-atomic; architect designs                            |
| Brief format | Narrative and/or structured events                                                    | Parent normalizes either into the Task                      |
| Confidence   | Tiered: single-episode forensics → multi-occurrence before “reliable”                 | Matches gauntlet evidence bar                               |
| Structure    | Thin personas + `pattern-mine` skill + analyst↔reviewer pair                         | Procedure in skill; Roles fill implementer/reviewer pattern |
| Default Bar  | ≥5 comparable episodes in 14 days + cited queries + FP rate or “insufficient history” | Objective; parent may tighten                               |
| Readonly     | Both personas readonly                                                                | Scout/judge only; no repo or live mutation                  |

## Method (skill summary)

1. Normalize brief → ordered event anchors + window.
2. Single-episode forensics via `grafana-ha-history` (and HA MCP for live IDs if needed).
3. Expand neighborhood entities around anchors.
4. If Goal requires reliable triggers → multi-occurrence pass against default (or parent) Bar.
5. Emit Artifact: ranked candidates, rejected/noisy signals, evidence, confidence tier.
6. `pattern-reviewer` judges Artifact against Bar → `pass` \| `gap` (one blocking miss).
7. On `gap`, parent spawns a fresh analyst Task; on `pass`, hand candidates to `automation-architect`.

## Pipeline

```
parent sets Goal + Bar + Artifact
  → pattern-analyst (mine / propose)
  → pattern-reviewer (grade vs Bar)
       ↓ gap → new analyst Task
       ↓ pass → automation-architect (YAML design)
```

## Steps

- [x] Write `pattern-mine` skill (procedure, default Bar, return shape)
- [x] Write `pattern-analyst` persona (charter ≤60 lines, link skill)
- [x] Write `pattern-reviewer` persona (pass\|gap, no re-mine as primary job)
- [x] Add `.cursor/agents/` symlinks
- [x] Update `subagents.md` + `AGENTS.md` routing tables
- [x] Run `check_links.py` on new/changed agent context files
- [ ] Operator smoke: delegate weekend get-up / auto-disarm trigger hunt

## Feedback loop

- Personas load and describe Role / Bar / boundaries without editing packages
- `check_links.py` clean for new links
- First real Task: seed episode from 2026-08-08 morning get-up (bed empty, manual disarm, back door); reviewer refuses “reliable” without multi-occurrence evidence

## Notes

- Generic `/implementer` and `/reviewer` remain for config/code Slices. These
  personas are domain fillers of the same Roles for history-pattern Bars
  (same idea as `security-analyst` filling reviewer for security Bars).
- Operator owns git; agents do not commit.
- Spec approval gate: operator reviews this plan before scaffolding files.
