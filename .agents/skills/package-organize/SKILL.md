# Skill: Package Organization

## Purpose

Restructure, create, or reorganize Home Assistant packages following the homelab's established directory structure and naming conventions.

## When to Use

- Restructuring existing packages
- Creating new package files
- Moving entities between packages
- Consolidating or splitting large package files
- Adding new areas or modifying the area registry

## Package Directory Structure

```
packages/
├── areas/          # Room/location-specific configs
├── functions/      # Bundled functionality configs
├── integrations/   # Integration/device configs
├── projects/       # Multi-device projects
├── routines/       # Time/event-based automations
├── system/         # HA system management
├── toys/           # Fun/non-essential automations
└── README.md       # Package documentation
```

## Steps

1. **Determine target package** — Use nomenclature.md to select the right directory
2. **Check existing files** — Read the target package file to see if the entity already exists
3. **Follow naming conventions** — Use prefixes from nomenclature.md
4. **Maintain file structure** — Keep consistent section headers and ordering
5. **Update area registry** — If adding a new area, update `packages/system/areas.yaml`
6. **Validate** — Run config-validate skill after changes

## File Structure Convention

Each package file should follow this section order:

```yaml
# <Area/Function> Configuration
# Last updated: YYYY-MM-DD

# ============================
# Lights
# ============================
light: ...

# ============================
# Sensors
# ============================
sensor: ...

# ============================
# Automations
# ============================
automation: ...
```

## Consolidation Rules

- **Areas**: One file per location, max ~200 lines. Split if larger.
- **Functions**: One file per functionality, max ~150 lines. Split if larger.
- **Integrations**: One file per integration. Can grow large — split into sub-sections with headers.
- **Routines**: One file per routine type, max ~100 lines.

## Cross-File Dependencies

When moving entities between packages:

1. Check for references in other packages (grep for entity_id)
2. Update automation `entity_id` references
3. Update any `rest_command` or `template` references
4. Update `areas.yaml` if area ID changed

## Output Format

```
Restructuring packages/integrations/core.yaml:
- Moved recorder config to top-level section
- Added section headers for clarity
- Consolidated duplicate light: definitions
```

## Notes

- Never merge two files without checking for entity conflicts first
- `packages/system/areas.yaml` is the source of truth for area definitions
- New areas require: (1) new file in `packages/areas/`, (2) entry in `areas.yaml`, (3) area ID assignment in Home Assistant UI
