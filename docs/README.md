# Apocrathia's Home Assistant Configuration Files 

![Project Maintenance][maintenance-shield]
[![License][license-shield]](LICENSE.md)

[![GitHub Activity][commits-shield]][commits]
[![GitHub Last Commit][last-commit-shield]][commits]

[![GitHub Actions][actions-shield]][actions]
[![Black Duck Security Risk][black-duck-shield]][black-duck]

![GitHub Stars][stars-shield]
![GitHub Watchers][watchers-shield]
![GitHub Forks][forks-shield]

[![Discord][discord-shield]][discord]
[![Community Forum][forum-shield]][forum]

---

![My Home Assistant Default View](images/default_view.png)

## Architecture

The production instance of Home Assistant is running via the 
[Home Assistant Operating System](https://github.com/home-assistant/operating-system)
on a virtual machine (VM) in a VMware vSphere cluster, with a remote instance 
running on a Raspberry Pi 4 which has multiple USB radios connected 
(Currently [Zigbee](https://www.home-assistant.io/integrations/zha/), 
[Z-Wave](https://www.home-assistant.io/integrations/zwave/), and an 
RTL-SDR dongle for [433mhz devices](https://github.com/merbanan/rtl_433)). 

This is done for multiple reasons:

- Allow HA to communicate directly with wireless devices without the need for an external hub.
- Prevent having to pass USB devices through to virtual michines.
- Enable VMware to migrate the main HA VM across hosts within the cluster based upon load.
- Place radios in a more central location with better reception. 

![My Home Assistant Architecture](images/conceptual_architecture.png)

Instances are linked together using 
[Lukas Hetzenecker's home-assistant-remote custom_component](https://github.com/lukas-hetzenecker/home-assistant-remote),
which allows for all configuration to be completed within Home Assistant,
without the need to worry about using USB/IP or socat to push the devices over the network.
I've looked into using MQTT discovery, but the issue is advertisement intervals.
Devices show up instantly with the homeassistant-remote component, even after restarts.

## General Information
This configuration controls a couple of significant features in my smart home.
- Alarm Clock using my bedroom lights and TV
- Turning on/off lights at sunset/sunrise
- Arming the alarm system when nobody is home
- Security lighting when motion is detected at my front door

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
[travis-shield]: https://travis-ci.org/Apocrathia/home-assistant-config.svg?branch=master
[travis]: https://travis-ci.org/Apocrathia/home-assistant-config
[home-assistant]: https://home-assistant.io
[issue]: https://github.com/Apocrathia/home-assistant-config/issues
[license-shield]: https://img.shields.io/github/license/Apocrathia/home-assistant-config.svg
[maintenance-shield]: https://img.shields.io/maintenance/yes/2020.svg
[last-commit-shield]: https://img.shields.io/github/last-commit/Apocrathia/home-assistant-config.svg
[stars-shield]: https://img.shields.io/github/stars/Apocrathia/home-assistant-config.svg?style=social&label=Stars
[forks-shield]: https://img.shields.io/github/forks/Apocrathia/home-assistant-config.svg?style=social&label=Forks
[watchers-shield]: https://img.shields.io/github/watchers/Apocrathia/home-assistant-config.svg?style=social&label=Watchers
[black-duck-shield]: https://copilot.blackducksoftware.com/github/repos/Apocrathia/home-assistant-config/branches/master/badge-risk.svg
[black-duck]: https://copilot.blackducksoftware.com/github/repos/Apocrathia/home-assistant-config/branches/master/
