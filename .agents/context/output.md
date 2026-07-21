# Output — Home Assistant Homelab

## Output Format Expectations

### YAML Configuration Output

- Always include full YAML blocks, not partial snippets
- Use 2-space indentation consistently
- Include comments for non-obvious settings
- Prepend file path when showing changes: `packages/areas/kitchen.yaml:`

### Diff-Style Changes

When modifying existing files, show changes in SEARCH/REPLACE format:

```diff
packages/integrations/core.yaml:

------- SEARCH
recorder:
  purge_keep_days: 7
=======
recorder:
  purge_keep_days: 30
  exclude:
    domains:
      - camera
+++++++ REPLACE
```

### File Creation Output

When creating new files, show the complete file content:

````
New file: packages/areas/guest_room.yaml

```yaml
# Guest Room Configuration
# Last updated: 2026-07-20

input_boolean:
  guest_room_occupied:
    name: Guest Room Occupied
````

````

### Automation Output

When presenting automations, include all sections in order. Use current HA YAML keys
(`triggers` / `conditions` / `actions`, plus `trigger:` and `action:` on list items):

```yaml
automation:
  - alias: "Kitchen Motion Light On"
    description: "Turn on kitchen lights when motion detected at night"
    triggers:
      - trigger: state
        entity_id: binary_sensor.kitchen_motion
        to: "on"
    conditions:
      - condition: time
        after: "sunset - 00:30:00"
        before: "sunrise + 00:15:00"
    actions:
      - action: light.turn_on
        target:
          entity_id: light.kitchen_ceiling
        data:
          brightness: 200
          color_temp: 370
    mode: single
````

### Error/Debug Output

When troubleshooting, include:

1. The error message (verbatim)
2. The relevant config section
3. The fix
4. How to verify the fix

### Entity State Output

When reporting entity states, use this format:

```
entity: light.kitchen_counter
state: on
attributes:
  brightness: 254
  color_temp: 300
  area: kitchen
```

## Rules

1. Always show file paths alongside config snippets
2. Use code blocks for anything > 3 lines
3. Include line numbers when referencing specific lines
4. Mark TODO items with `# TODO:` comments in proposed changes
5. When suggesting multiple files, list them in load order
