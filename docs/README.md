# Apocrathia's Home Assistant Configuration Files

![Project Maintenance][maintenance-shield]
[![License][license-shield]](LICENSE.md)

[![GitHub Activity][commits-shield]][commits]
[![GitHub Last Commit][last-commit-shield]][commits]

[![GitHub Actions][actions-shield]][actions]

![GitHub Stars][stars-shield]
![GitHub Watchers][watchers-shield]
![GitHub Forks][forks-shield]

[![Discord][discord-shield]][discord]
[![Community Forum][forum-shield]][forum]

<a href="https://www.buymeacoffee.com/apocrathia" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/arial-violet.png" alt="Buy Me A Coffee" style="height: 30px !important;width: 117px !important;" ></a>

---

![My Home Assistant Default View](images/default_view.png)

## Documentation

- [Package Structure](packages.md) - Organization and structure of Home Assistant packages
- [Special Projects](projects.md) - Documentation for mycology, aquaponics, and other special integrations
- [Contributing Guidelines](CONTRIBUTING.md) - How to contribute to this project
- [License Information](LICENSE.md) - Project license details

## Architecture

The Home Assistant setup consists of several integrated components:

### Core System

- Main Home Assistant instance runs on Proxmox virtualization
- Backed by Synology NAS for storage and data persistence
- Uses MariaDB for the database backend

### Device Integration

- Raspberry Pi nodes for distributed radio connectivity:
  - Z-Wave network management
  - Zigbee device control (via Zigbee2MQTT)
  - LoRa connectivity for long-range sensors

### Smart Home Integration

- HomeKit integration for Apple device compatibility
- Support for various smart speakers and mobile devices
- Integration with security systems (Envisalink)

### System Management

- Weekly maintenance routines for system health
- Automated certificate renewal via Let's Encrypt
- Comprehensive backup strategy
- GitHub Actions for configuration testing

![My Home Assistant Architecture](images/conceptual_architecture.png)

## General Information

This configuration controls several key features in my smart home:

- Alarm Clock using bedroom lights and TV
- Automated lighting based on sun events
- Security system integration and automation
- Motion-activated security lighting
- Special project monitoring (mycology, aquaponics)
- Automated blind control

**Note: Private information is stored in secrets.yaml (not uploaded)**

[commits-shield]: https://img.shields.io/github/commit-activity/y/Apocrathia/home-assistant-config.svg
[commits]: https://github.com/Apocrathia/home-assistant-config/commits/master
[actions-shield]: https://github.com/Apocrathia/home-assistant-config/workflows/Home%20Assistant%20CI/badge.svg
[actions]: https://github.com/Apocrathia/home-assistant-config/actions
[contributors]: https://github.com/Apocrathia/home-assistant-config/graphs/contributors
[discord-shield]: https://img.shields.io/discord/330944238910963714.svg
[discord]: https://discord.gg/c5DvZ4e
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg
[forum]: https://community.home-assistant.io/?u=Apocrathia
[apocrathia]: https://github.com/Apocrathia
[home-assistant]: https://home-assistant.io
[issue]: https://github.com/Apocrathia/home-assistant-config/issues
[license-shield]: https://img.shields.io/badge/license-apache-brightgreen.svg
[maintenance-shield]: https://img.shields.io/maintenance/yes/2023.svg
[last-commit-shield]: https://img.shields.io/github/last-commit/Apocrathia/home-assistant-config.svg
[stars-shield]: https://img.shields.io/github/stars/Apocrathia/home-assistant-config.svg?style=social&label=Stars
[forks-shield]: https://img.shields.io/github/forks/Apocrathia/home-assistant-config.svg?style=social&label=Forks
[watchers-shield]: https://img.shields.io/github/watchers/Apocrathia/home-assistant-config.svg?style=social&label=Watchers
