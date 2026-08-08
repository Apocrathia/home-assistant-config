# Vertical slices

How to slice work so each piece delivers end-to-end behavior, not a horizontal
layer. Applies to plans, operator handoffs, and Launch briefs from
[`find-work`](../skills/find-work/SKILL.md).

## The principle

A vertical slice goes through every layer needed for an observable outcome.
A horizontal slice finishes one layer for the whole feature before the next.

**Vertical:** "closet motion turns on the light and turns it off after idle"
(automation + entity refs + config check + live spot-check).
**Horizontal:** "rename every entity_id string in packages/" (one layer only,
no prove-it loop).

In this Homelab, a slice is often: one package/ESPHome change +
`config-validate` + live entity/automation check — not "rewrite all areas."

## Why vertical

- Each slice is independently shippable (operator commit) and testable.
- Integration risk shows up early.
- Agent laps stay small (one Launch brief → one handoff-sized change).

## In plans

Each unchecked checkbox should be one vertical slice. If a step only touches
one layer without a feedback loop, split it.

## In find-work / implement-change

Scout laps **find** work; they do not own remediation end-to-end. Ranked Launch
briefs are agent-sized vertical slices. Broad findings default to
[`file-issue`](../skills/file-issue/SKILL.md); implement only when already one
slice with a named feedback loop.

See [`development-loop.md`](./development-loop.md).
