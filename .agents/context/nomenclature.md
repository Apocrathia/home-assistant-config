# Nomenclature — Home Assistant Homelab

## Shared Vocabulary

### Entity Naming Convention

Format: `<type>_<area>_<description>`

| Component       | Examples                                                                                                                                                   |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Type**        | `light`, `switch`, `sensor`, `binary_sensor`, `cover`, `lock`, `fan`, `vacuum`, `media_player`, `climate`, `input_boolean`, `input_number`, `input_select` |
| **Area**        | `kitchen`, `living_room`, `master_bedroom`, `office`, `basement`, `front_porch`, `garage`, `back_yard`, `master_bathroom`, `downstairs_bathroom`           |
| **Description** | `counter`, `ceiling`, `tv`, `bed`, `desk`, `door`, `window`, `motion`, `temperature`, `humidity`                                                           |

Examples:

- `light_kitchen_counter` — Kitchen counter lights
- `sensor_master_bedroom_temperature` — Bedroom temperature sensor
- `binary_sensor_office_door` — Office door contact sensor
- `cover_living_room_blinds` — Living room blind covers
- `input_boolean.away_mode` — Global away mode boolean

### Package Organization Prefixes

| Prefix           | Package               | Purpose                                                                    |
| ---------------- | --------------------- | -------------------------------------------------------------------------- |
| `routine_`       | `packages/routines/`  | Time/event-based recurring tasks (morning, night, astronomy)               |
| `function_`      | `packages/functions/` | Bundled configurations for specific functionality (presence, HVAC, energy) |
| `area_`          | `packages/areas/`     | Location-specific configurations (room-level)                              |
| `system_`        | `packages/system/`    | Home Assistant system management (lovelace, maintenance, areas)            |
| `alert_`         | Root packages         | Alert definitions                                                          |
| `shell_command_` | `packages/system/`    | Helper scripts and shell commands                                          |

### Area Names (Canonical)

| Area ID               | Display Name        |
| --------------------- | ------------------- |
| `kitchen`             | Kitchen             |
| `living_room`         | Living Room         |
| `master_bedroom`      | Master Bedroom      |
| `master_bathroom`     | Master Bathroom     |
| `office`              | Office              |
| `basement`            | Basement            |
| `downstairs_bathroom` | Downstairs Bathroom |
| `sitting_room`        | Sitting Room        |
| `studio`              | Studio              |
| `laundry_room`        | Laundry Room        |
| `front_porch`         | Front Porch         |
| `back_yard`           | Back Yard           |
| `garage`              | Garage              |

### Device Classes

| Category         | Common Device Classes                                           |
| ---------------- | --------------------------------------------------------------- |
| **Temperature**  | `temperature`, `humidity`, `pressure`                           |
| **Binary**       | `motion`, `door`, `window`, `gas`, `smoke`, `cold`, `vibration` |
| **Energy**       | `power`, `voltage`, `current`, `energy`                         |
| **Distance**     | `distance`, `duration`                                          |
| **Battery**      | `battery`, `battery_charging`                                   |
| **Connectivity** | `signal_strength`                                               |

### Script/Function Prefixes

| Prefix      | Purpose                                                        |
| ----------- | -------------------------------------------------------------- |
| `function_` | Core functionality bundles (presence simulation, HVAC control) |
| `area_`     | Area-specific scripts (occupancy simulation per area)          |
| `energy_`   | Energy management scripts (disable/enable heavy consumption)   |
| `location_` | Presence/location state scripts (home, away)                   |
| `vacation_` | Vacation mode scripts                                          |
| `wakeup_`   | Device wakeup scripts (Apple TV, etc.)                         |

### Integration Prefixes

| Integration    | Key File                                |
| -------------- | --------------------------------------- |
| **Ecobee**     | `packages/integrations/ecobee.yaml`     |
| **Envisalink** | `packages/integrations/envisalink.yaml` |
| **InfluxDB**   | `packages/integrations/influxdb.yaml`   |
| **HomeKit**    | `packages/integrations/homekit.yaml`    |
| **Awtrix**     | `packages/integrations/awtrix.yaml`     |
| **Torque**     | `packages/integrations/torque.yaml`     |

## Rules

1. Entity IDs are lowercase with underscores — no spaces, no camelCase
2. Area names match `area.yaml` canonical names exactly
3. Package filenames use snake_case with prefix (e.g., `routine_morning`, `function_presence`)
4. Script IDs use `script.` prefix in YAML references
5. Automation IDs use `automation.` prefix in YAML references
6. Input helper IDs use `input_boolean.`, `input_number.`, `input_select.` prefixes
