# Home Assistant Packages

Modular YAML packages under `packages/`, loaded via
`homeassistant.packages: !include_dir_named packages` in `configuration.yaml`.

The package id is the filename stem. Subdirectory names organize the repo; they
are not part of the package id.

## Directory structure

```
packages/
├── areas/          # Location-specific config
├── functions/      # Cross-area functionality
├── integrations/   # Core / integration config
├── private/        # Local-only packages (gitignored except README)
├── projects/       # Multi-device projects
├── routines/       # Time- and event-based routines
├── system/         # HA system management
├── test/           # Experimental packages
└── toys/           # Non-essential / fun
```

## Package types

### Areas (`areas/`)

One file per location: lights, room automations, sensors, scenes.

Examples: `back_yard.yaml`, `office.yaml`, `master_bathroom.yaml`

### Functions (`functions/`)

Cross-cutting behavior: energy, HVAC, presence, security, dimmers.

Examples: `energy.yaml`, `hvac.yaml`, `presence.yaml`

### Integrations (`integrations/`)

Platform and integration settings (HomeKit, InfluxDB, Awtrix, etc.).

### Projects (`projects/`)

Self-contained multi-device projects (mycology, aquaponics, blinds).

### Routines (`routines/`)

Schedules and recurring flows (day, night, work, doge, events).

### System (`system/`)

Core management: areas registry helpers, Lovelace, maintenance, shell commands.

### Toys (`toys/`)

Optional / seasonal behavior (halloween, party lights).

### Private (`private/`)

Local-only packages loaded by Home Assistant but not committed. Use for personal
or sensitive routines (health, habits, private reminders). See
`packages/private/README.md`.

## Practices

1. One concern per package file
2. Prefer entity ids and automation ids from `.agents/context/nomenclature.md`
3. Follow section order and size limits in `.agents/skills/package-organize/SKILL.md`
4. Document non-obvious dependencies in-file with comments
5. Validate config after changes (Developer Tools → YAML, or config-validate skill)

## Adding a package

1. Pick the directory that matches the concern
2. Add `snake_case.yaml` (filename stem becomes the package id)
3. Use the package-organize section headers and naming prefixes
4. Validate before relying on it in production

## Related

- [packages/README.md](../packages/README.md)
- [Home Assistant Packages](https://www.home-assistant.io/docs/configuration/packages/)
- [YAML configuration](https://www.home-assistant.io/docs/configuration/yaml/)
- [Automations](https://www.home-assistant.io/docs/automation/)
