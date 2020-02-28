# Apocrathia's Home Assistant Configuration Files 
[![Build Status](https://travis-ci.org/Apocrathia/home-assistant-config.svg?branch=master)](https://travis-ci.org/Apocrathia/home-assistant-config)
[![Black Duck Security Risk](https://copilot.blackducksoftware.com/github/repos/Apocrathia/home-assistant-config/branches/master/badge-risk.svg)](https://copilot.blackducksoftware.com/github/repos/Apocrathia/home-assistant-config/branches/master)
[![Coverage Status](https://coveralls.io/repos/github/Apocrathia/home-assistant-config/badge.svg?branch=master)](https://coveralls.io/github/Apocrathia/home-assistant-config?branch=master)

### Configuration File Status 
TravisCI hasn't been sucessfully building the configuration in a while due to the usage of custom components.

![My Home Assistant Default View](images/default_view.png)

## Architecture

The production instance of Home Assistant is running via the 
[Home Assistant Operating System](https://github.com/home-assistant/operating-system)
 on a virtual machine (VM) in a VMware vSphere cluster, with a remote instance 
 running on a Raspberry Pi 4 which has multiple USB radios connected 
 (Currently [Zigbee](https://www.home-assistant.io/integrations/zha/), 
 [Z-Wave](https://www.home-assistant.io/integrations/zwave/), and an 
 RTL-SDR dongle for [433mhz](https://github.com/james-fry/hassio-addons/tree/master/rtl4332mqtt)). 
 This is done for multiple reasons.
- Allow HA to communicate directly with wireless devices without the need for an external hub.
- Prevent having to pass USB devices through to virtual michines.
- Enable VMware Distributed Resource Scheduler (DRS) to migrate HA VM across hosts within the cluster based upon load.
- Place radios in central location with far better reception. (The network rack is grounded and effectively acts as a faraday cage)

![My Home Assistant Architecture](images/conceptual_architecture.png)

Instances are linked together using 
[Lukas Hetzenecker's home-assistant-remote custom_component](https://github.com/lukas-hetzenecker/home-assistant-remote),
 which allows for all configuration to be completed within Home Assistant,
  without the need to worry about using USB/IP or socat to push the devices over the network.

## General Information
This configuration controls a couple of significant features in my smart home.
* Alarm Clock using my bedroom lights and TV
* Turning the outside lights on at night
* Arming the alarm system when nobody is home
* Security lighting when motion is detected at my front door

**Note: Private information is stored in secrets.yaml (not uploaded)**
