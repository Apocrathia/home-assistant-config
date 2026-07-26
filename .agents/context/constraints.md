# Constraints — Home Assistant Homelab

## Hard Limits

### What You Can Do Freely

- Read files, explore, search the configuration
- Run validation, linting, YAML syntax checks
- Propose changes and present options
- Use `.scratch/` for throwaways (prefer over `/tmp`); see `.scratch/README.md`
- Use `packages/private/` for local-only HA packages (gitignored except README)
- Read `.shopping_list.json` and `.storage/local_todo.*.ics` as work sources
  (see `work-sources.md`)

### Requires Explicit Permission

- Modify `configuration.yaml` or any file in `packages/`
- Edit files in `.storage/` (JSON — runtime state, never edit directly)
- Create or modify automations that affect critical systems (security, safety, HVAC)
- Change `secrets.yaml` or any credential-related configuration
- Modify integrations that connect to external services
- Create branches (unless the operator explicitly asks)

### Never Do

- **Commit, push, merge, rebase, tag, or open PRs/MRs** — git is operator-owned
  ([`rules/operator-owned-git.md`](../rules/operator-owned-git.md)). This
  overrides upstream skills (`ship-work`, `clock-out`, `self-improve` shipping
  steps, etc.).
- **Write to `.shopping_list.json` or `.storage/local_todo.*.ics`** — HA-owned
  runtime to-dos; read-only work sources
  ([`work-sources.md`](work-sources.md)). Do not mark complete, add, delete, or
  reformat.
- Edit `.storage/` files directly (managed by Home Assistant)
- Hardcode credentials, API keys, or secrets
- Modify the UniFi or other infrastructure controllers directly

## Protected Paths

The following paths require confirmation before any edit:

- `.agents/` — Agent context and skills (don't break the routing)
- `configuration.yaml` — Main entry point
- `secrets.yaml` — All credentials
- `.storage/` — Runtime state
- `packages/system/` — Core HA system management

## Domain-Specific Constraints

### YAML Configuration

- Always validate indentation (2 spaces, no tabs)
- Use `secrets.yaml` for sensitive values, reference with `!secret`
- Follow package organization: `areas/`, `functions/`, `integrations/`, `private/`, `projects/`, `routines/`, `system/`, `toys/`
- Use descriptive naming with prefixes: `routine_morning`, `function_presence`, `light_kitchen`, `sensor_bedroom_temperature`

### Automations

- Use current automation YAML keys: `triggers:`, `conditions:`, `actions:`
- Inside a trigger item use `trigger:` (not `platform:`); inside an action item use `action:` (not `service:`)
- Nested condition type keys stay singular (`condition: state`, `condition: time`, etc.)
- Use `variables` for reusable values within actions
- Include proper error handling and logging where applicable
- Avoid tight loops or high-frequency polling

### Entities

- Use consistent naming: `<type>_<area>_<description>` (e.g., `light_kitchen_counter`)
- Group related entities by area and function
- Assign proper `area_id`, `device_class`, and `entity_category` where applicable

## Performance

- Stop after 3 failed attempts at the same approach — escalate or change strategy
- Don't suggest configurations that would cause excessive API calls or polling
- Consider database and history impact when configuring sensors and loggers
