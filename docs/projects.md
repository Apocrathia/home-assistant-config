# Special Projects Documentation

## Overview

Multi-device project integrations, each self-contained under `packages/projects/`.

## Current Projects

### Mycology Project

Location: `packages/projects/mycology.yaml`

A monitoring and control system for mycology cultivation:

- Environmental monitoring (temperature, humidity)
- Growth condition automation
- Alert system for condition deviations
- Data logging and analysis

### Aquaponics System

Location: `packages/projects/aquaponics.yaml`

Automated aquaponics system management:

- Water quality monitoring
- Feeding schedules
- Pump control
- Environmental parameters
- Alert system for critical conditions

### Automated Blinds

Location: `packages/projects/blinds.yaml`

Smart blind control system:

- Schedule-based operation
- Light level responsiveness
- Temperature optimization
- Manual override options
- Scene integration

## Project Structure

Each project package follows a consistent structure:

```yaml
# Project Configuration Template
sensor:
  # Project-specific sensors
automation:
  # Project-specific automations
binary_sensor:
  # Status sensors
script:
  # Reusable scripts
input_boolean:
  # Control switches
template:
  # Custom sensors and calculations
alert:
  # Warning systems
```

## Integration with Core System

- Projects can be enabled/disabled via input_boolean helpers
- Data is stored in InfluxDB for long-term analysis
- Notifications are sent through the central notification system
- Projects are integrated with the main dashboard

## Adding New Projects

1. Create a new file in `packages/projects/`
2. Follow the project structure template
3. Document dependencies and requirements
4. Include setup instructions
5. Add monitoring and alerting
6. Create project-specific dashboard views
