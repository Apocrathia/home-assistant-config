# Skill: Config Validation

## Purpose

Validate Home Assistant YAML configurations for syntax, structure, and best practices before applying changes.

## When to Use

- Writing or modifying any YAML config file
- Before suggesting changes to `packages/` files
- When the user asks "does this look right?" or "validate my config"
- After any automation or integration change

## Steps

1. **Identify target file** — Determine which package file is being modified
2. **Check YAML syntax** — Validate indentation, quoting, special characters
3. **Verify entity references** — Ensure `entity_id`, `device_id`, `area_id` references exist
4. **Check for duplicates** — No duplicate entity IDs, automation aliases, or service calls
5. **Validate structure** — Ensure top-level keys match HA schema (light, sensor, automation, etc.)
6. **Review secrets usage** — Flag any hardcoded credentials
7. **Report findings** — List issues by severity (error, warning, info)

## Common Validation Checks

| Check                    | Severity | Example                                                   |
| ------------------------ | -------- | --------------------------------------------------------- |
| Indentation              | Error    | Mixed tabs/spaces, wrong indent level                     |
| Duplicate entity_id      | Error    | Two entities with same ID                                 |
| Missing required field   | Error    | `service:` without `service:` value                       |
| Invalid entity reference | Warning  | `entity_id: light.nonexistent`                            |
| Hardcoded secret         | Warning  | `api_key: "my-secret-key"` instead of `!secret`           |
| Deprecated option        | Info     | Using old-style `latitude:` instead of `recorder:` config |
| Missing description      | Info     | Automation without `description:` field                   |

## Output Format

```
Validation Results for packages/areas/kitchen.yaml:

❌ ERROR (line 12): Duplicate entity_id 'light_kitchen_counter'
⚠️  WARNING (line 28): Hardcoded API key found, use !secret
ℹ️  INFO: Automation missing 'description' field
```

## Tools

- `ha config check` — Built-in Home Assistant YAML validator
- `yamllint` — External YAML linting tool
- `pre-commit` — Git hook for pre-commit validation

## Notes

- This skill is procedural — it guides the agent through validation, not code
- Always validate in the context of the full configuration, not just the modified file
- Entity references may be defined in other packages — check across `packages/`
