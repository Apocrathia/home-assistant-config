# Grafana HA History — Reference

Datasource: Grafana uid `homeassistant` → InfluxDB database `homeassistant`,
InfluxQL (not Flux). Query only through Grafana MCP
`grafana_api_request`.

Base endpoint:

```
GET /api/datasources/proxy/uid/homeassistant/query?db=homeassistant&q=<URL-encoded InfluxQL>
```

Optional jq filter (example): `.results[0].series[0] | {columns, values}`

---

## Schema

### `"state"` measurement (non-numeric / discrete)

| Kind   | Names                     | Notes                                      |
| ------ | ------------------------- | ------------------------------------------ |
| Tags   | `domain`, `entity_id`     | `entity_id` = object_id only (`back_door`) |
| Fields | `state` (string), `value` | e.g. `off` / `0`, `locked` / `1`           |

Domains present include: `binary_sensor`, `lock`, `cover`, `person`,
`light`, `switch`, `climate`, `automation`, `media_player`, …

### Unit-named measurements (numeric series)

~95 measurements named by unit: `"°F"`, `"W"`, `"%"`, `"A"`, `"V"`,
`"lx"`, `"hPa"`, `"GB"`, … Same `entity_id` (and often `domain`) tags.
Prefer the `"value"` field.

Discover which measurement holds an entity:

```influxql
SHOW MEASUREMENTS WHERE "entity_id" = 'outdoor_temperature'
```

---

## Recipes

Entity examples below are illustrative — substitute real domain/object_id.

### 1. Point-in-time (last value at or before T)

```influxql
SELECT "state", "value" FROM "state"
WHERE "domain" = 'lock' AND "entity_id" = 'back_door'
  AND time <= '2026-07-25T08:15:00Z'
ORDER BY time DESC LIMIT 1
```

### 2. Window changes (ordered events)

```influxql
SELECT "state", "value" FROM "state"
WHERE "domain" = 'cover' AND "entity_id" = 'garage_door'
  AND time >= '2026-07-25T06:00:00Z'
  AND time < '2026-07-25T14:00:00Z'
ORDER BY time ASC
```

Add `LIMIT 200` (or similar) if the window may be noisy.

### 3. Numeric series (raw)

```influxql
SELECT "value" FROM "°F"
WHERE "entity_id" = 'outdoor_temperature'
  AND time > now() - 24h
```

### 4. Numeric series (downsampled)

```influxql
SELECT MEAN("value") FROM "W"
WHERE "entity_id" = 'whole_house_power'
  AND time > now() - 7d
GROUP BY time(1h) fill(null)
```

### 5. Discovery

```influxql
SHOW MEASUREMENTS
SHOW TAG VALUES FROM "state" WITH KEY = "domain"
SHOW TAG VALUES FROM "state" WITH KEY = "entity_id" WHERE "domain" = 'lock'
SHOW MEASUREMENTS WHERE "entity_id" = 'outdoor_temperature'
SHOW FIELD KEYS FROM "state"
```

---

## MCP call pattern

1. Build InfluxQL.
2. URL-encode the full query string (spaces → `%20`, quotes → `%22` /
   `%27`, etc.).
3. Call `grafana_api_request`:

```json
{
  "endpoint": "/api/datasources/proxy/uid/homeassistant/query?db=homeassistant&q=<ENCODED>",
  "method": "GET",
  "jq": ".results[0].series[0] | {columns, values}"
}
```

Encoded example for recipe 1:

```
/api/datasources/proxy/uid/homeassistant/query?db=homeassistant&q=SELECT%20%22state%22%2C%20%22value%22%20FROM%20%22state%22%20WHERE%20%22domain%22%20%3D%20%27lock%27%20AND%20%22entity_id%22%20%3D%20%27back_door%27%20AND%20time%20%3C%3D%20%272026-07-25T08%3A15%3A00Z%27%20ORDER%20BY%20time%20DESC%20LIMIT%201
```

---

## Traps

- **Timestamps are UTC** unless you pass an offset. Prefer ISO-8601 with `Z`
  or relative `now() - 6h`. Local wall-clock questions need explicit conversion.
- **`entity_id` tag has no domain prefix.** Filtering
  `entity_id = 'lock.back_door'` returns nothing; use `domain` + `entity_id`.
- **Booleans are dual-coded** — `state='off'` and `value=0` (or on/1). Report
  the string `state` to humans; `value` is fine for aggregates.
- **Unit measurement names need quoting** — `"°F"`, `"%"`, `"W"`. Always
  URL-encode; `°` becomes UTF-8 percent-encoding (`%C2%B0`).
- **Empty series ≠ no history.** Confirm tags/measurement first
  (`SHOW TAG VALUES` / `SHOW MEASUREMENTS WHERE …`).
- **No dedicated Influx MCP tool** — always go through
  `grafana_api_request` on this datasource proxy. Do not use Prometheus/Loki
  tools for HA entity history.
- **Cap results.** Wide windows without `LIMIT` / `GROUP BY time()` can dump
  huge payloads into context.
