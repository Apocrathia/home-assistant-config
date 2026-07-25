---
name: grafana-ha-history
description: >-
  Query historical Home Assistant entity state via Grafana's Home Assistant
  InfluxDB datasource (InfluxQL). Use when the user asks about past states,
  "was X on/off", "when did…", history for an entity, overnight activity,
  or numeric sensor series over a time window — not for current/live state.
---

# Skill: Grafana HA History

## Purpose

Look up **past** Home Assistant entity state from Grafana → InfluxDB
(`uid: homeassistant`). Live/current state stays on the HA MCP.

## When to Use

- "Was the garage open at 2am?"
- "When did the front door unlock last night?"
- "What was outdoor temp over the last 24h?"
- Any historical entity state / change timeline / numeric series

**Not** for current state — use HA MCP `GetLiveContext` (or equivalent) first.

## Workflow

1. **Resolve the entity** — domain + object_id from the HA entity_id
   (`lock.back_door` → domain `lock`, object_id `back_door`).
2. **Route the question**
   - On/off, modes, locked/unlocked, open/closed, person home/away →
     measurement `"state"`
   - Continuous numbers (temp, power, humidity, …) → unit-named measurement
     (`"°F"`, `"W"`, `"%"`, …)
3. **Pick a recipe** in [reference.md](reference.md):
   - Point-in-time (last value before T)
   - Window changes (ordered events between T1 and T2)
   - Numeric series (raw or downsampled)
4. **Query** via Grafana MCP `grafana_api_request`:

   ```
   GET /api/datasources/proxy/uid/homeassistant/query?db=homeassistant&q=<URL-encoded InfluxQL>
   ```

5. **Answer** with timestamps + values. Cite the InfluxQL used. Cap results
   with `LIMIT` / a tight time window.
6. **Empty result** → verify `domain` / `entity_id` tags (and measurement for
   numerics) before claiming there is no history. See traps in reference.md.

## Hard rules

- Read-only. Do not write to Influx or mutate Grafana.
- Always URL-encode the `q` parameter.
- Influx tag `entity_id` is the **object_id only** (no domain prefix).
- Prefer `"state"` + `"value"` fields on the `"state"` measurement for
  non-numeric entities.
- Never invent measurement names — discover with `SHOW MEASUREMENTS` /
  `SHOW MEASUREMENTS WHERE "entity_id" = '…'` when unsure.

## Additional resources

- Schema, recipes, discovery queries, traps: [reference.md](reference.md)
