# Skill: Automation Debugging

## Purpose

Systematically diagnose and fix broken Home Assistant automations using a structured troubleshooting approach.

## When to Use

- Automations not firing as expected
- Automations firing at wrong times
- Automation actions failing silently
- Entity state not updating as expected
- Template/condition logic producing unexpected results

## Debugging Workflow

### Step 1: Reproduce the Issue

1. Identify the automation ID: `automation.<name>`
2. Check current state: Developer Tools → States → find entity
3. Check last triggered: Developer Tools → States → `last_triggered` attribute
4. Manually trigger: Developer Tools → Automations → three dots → Trigger

### Step 2: Check Triggers

```
Common trigger issues:
- State trigger waiting for wrong value (on/off vs true/false)
- Time-based triggers with wrong format (24h, no timezone)
- Template trigger syntax errors
- Event trigger missing event_type or event_data
```

Verify:

- Trigger values match actual entity states
- Time formats are correct (`"23:30:00"`, not `"11:30 PM"`)
- Template triggers have valid Jinja2 syntax
- Event triggers match actual event payloads

### Step 3: Check Conditions

```
Common condition issues:
- State condition checking wrong entity
- Time condition with inverted before/after
- Template condition returning unexpected boolean
- Numeric state condition comparing string vs int
```

Verify:

- Condition entities are available and have correct state
- Template conditions return true/false (not null)
- Numeric comparisons use correct types
- `and` vs `or` grouping is correct

### Step 4: Check Actions

```
Common action issues:
- Service name typo (light.turn_on vs light.turnON)
- Target entity doesn't exist
- Data template referencing wrong state attribute
- Variable scope issues in repeat/for loops
```

Verify:

- Service names are valid (check Developer Tools → Services)
- Target entities exist and are accessible
- Data templates evaluate correctly
- `mode` setting matches expected behavior (single, restart, queued)

### Step 5: Check Templates

```
Common template issues:
- Undefined variable (missing from context)
- Wrong state attribute (state vs attributes.value)
- Type coercion issues (string "25" vs int 25)
- Jinja2 syntax errors
```

Test templates in Developer Tools → Templates before applying.

## Logging and Diagnostics

### Enable Debug Logging

```yaml
logger:
  default: warn
  logs:
    homeassistant.components.automation: debug
    homeassistant.helpers.template: debug
```

### Check Automation Log

```bash
# Check Home Assistant logs for automation errors
ha logs --log-level debug | grep automation
```

### Use `input_boolean` for Testing

Create a test boolean to manually control automation flow:

```yaml
input_boolean:
  automation_test_mode:
    name: 'Automation Test Mode'
```

## Common Fix Patterns

| Issue                        | Fix                                        |
| ---------------------------- | ------------------------------------------ | --------------- | -------------- |
| Automation not triggering    | Check `initial_state` — may be `off`       |
| Template returning undefined | Use `                                      | default('')`or` | int(0)` filter |
| State trigger not firing     | Check actual state value in States panel   |
| Action fails silently        | Add `mode: restart` or `mode: queued`      |
| Time trigger wrong timezone  | Set `time_zone` in `homeassistant:` config |
| Condition always true        | Check `and`/`or` grouping with parentheses |

## Output Format

```
Debug Results for automation.kitchen_night_light:

❌ ISSUE (trigger): State trigger expects "on" but sensor reports "active"
⚠️  WARNING (condition): Template references undefined variable 'states.sensor.kitchen_humidity'
ℹ️  INFO: Automation mode is 'single' — rapid triggers will be ignored

FIX:
- Change trigger to: to: "active"
- Add null check: {{ states('sensor.kitchen_humidity') | default(0) > 60 }}
- Consider mode: 'restart' if rapid triggers are expected
```

## Notes

- Always test changes in Developer Tools → YAML Configuration → Reload before restarting
- Use `automation.trigger` service to test without waiting for real conditions
- Template debugging is the #1 source of automation issues — test templates in isolation first
