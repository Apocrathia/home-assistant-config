# Packages

Home Assistant [packages](https://www.home-assistant.io/docs/configuration/packages/)
keep related config together. `configuration.yaml` loads them with:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

`!include_dir_named` loads YAML recursively. The package id is the **filename
stem** (e.g. `packages/routines/doge.yaml` → package `doge`). Folder names are
for humans only — they do not appear in Home Assistant.

## Directory layout

```
packages/
├── areas/          # One file per location
├── functions/      # Cross-area functionality
├── integrations/   # Integration / platform config
├── projects/       # Multi-device projects
├── routines/       # Time / event routines
├── system/         # HA system management
├── test/           # Experimental / scratch packages
└── toys/           # Non-essential / fun
```

## Naming

| Layer         | Convention                                      | Example                       |
| ------------- | ----------------------------------------------- | ----------------------------- |
| File          | `snake_case.yaml` in the matching directory     | `packages/routines/doge.yaml` |
| Automation id | `routine_*`, `function_*`, `area_*`, `system_*` | `routine_doge_meals`          |
| Entity id     | `<type>_<area>_<description>` where applicable  | `light.kitchen_counter`       |

See `.agents/context/nomenclature.md` and `.agents/skills/package-organize/SKILL.md`
for entity prefixes, section order, and file size limits.

## Related docs

- [docs/packages.md](../docs/packages.md) — package types and practices
- [Home Assistant Packages](https://www.home-assistant.io/docs/configuration/packages/)
