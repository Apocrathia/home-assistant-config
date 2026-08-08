---
name: pattern-mine
description: >-
  Mine Home Assistant history for automation trigger candidates from a
  narrative or structured event brief. Use when finding a reliable trigger,
  correlating a morning/evening sequence, ranking sensor signals for a new
  automation, or running the pattern-analyst ↔ pattern-reviewer pair.
---

# Skill: Pattern Mine

Read-only history mining for trigger candidates. Does not design automation
YAML. Query past state via [`grafana-ha-history`](../grafana-ha-history/SKILL.md);
resolve live entity IDs via HA MCP when needed.

## Steps

1. **Normalize the brief.** Turn narrative and/or structured events into an
   ordered anchor list: approximate time, what happened, optional entity hints,
   and the search window. Done when every anchor has a time (or relative order)
   and a plain-language label.

2. **Seed-episode forensics.** For the primary window, query state changes for
   hinted entities and obvious neighbors (same area, related domains: motion,
   presence, lock, door, alarm, light). Align timestamps to the anchors. Done
   when each anchor has supporting or contradicting sensor evidence cited.

3. **Neighborhood expand.** From entities that moved near anchors, discover
   related IDs (`SHOW TAG VALUES`, area packages, HA MCP). Drop noise (always-on
   chatter, unrelated rooms). Done when the candidate set is listed with why
   each was included.

4. **Tier confidence.**

   - Goal is episode understanding only → stop; label candidates
     `episode-only`.
   - Goal asks for **reliable** triggers → continue to step 5.
     Done when every candidate has a confidence tier.

5. **Multi-occurrence pass (reliable only).** Find comparable episodes in the
   parent window (default: last **14 days**, need **≥5** matches unless the Bar
   says otherwise). For each candidate, count hits / misses / false positives.
   Cite InfluxQL (or HA history calls) used. If history is too thin, label
   `insufficient-history` — **not** reliable. Done when each reliable claim
   meets the Bar or is explicitly demoted.

6. **Emit the Artifact.** Ranked candidates, rejected/noisy signals, evidence,
   confidence tier. Hand to `pattern-reviewer` (do not self-grade against the
   Bar).

## Default Bar

A candidate may be labeled **reliable** only if all hold (parent may tighten):

| #   | Requirement                                                                                       |
| --- | ------------------------------------------------------------------------------------------------- |
| 1   | Correlates with target anchors in the seed episode (cited timestamps)                             |
| 2   | Holds across ≥5 comparable episodes in the last 14 days (or parent N/window)                      |
| 3   | False-positive rate in those episodes is stated with evidence, or history is flagged insufficient |
| 4   | Every claim cites the query/tool used — no vibes                                                  |

## Return

```
Pattern mine — <slice or brief title>

Confidence: episode-only | reliable | mixed

Candidates (ranked):
- entity / event shape — why — evidence (times + query) — tier

Rejected / noisy:
- entity — why dropped — evidence

Gaps for reviewer:
- missing history, ambiguous anchors, open entity questions
```
