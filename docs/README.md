# Apocrathia's Home Assistant Configuration Files 
[![Build Status](https://travis-ci.org/Apocrathia/home-assistant-config.svg?branch=master)](https://travis-ci.org/Apocrathia/home-assistant-config)
[![Black Duck Security Risk](https://copilot.blackducksoftware.com/github/repos/Apocrathia/home-assistant-config/branches/master/badge-risk.svg)](https://copilot.blackducksoftware.com/github/repos/Apocrathia/home-assistant-config/branches/master)
[![Coverage Status](https://coveralls.io/repos/github/Apocrathia/home-assistant-config/badge.svg?branch=master)](https://coveralls.io/github/Apocrathia/home-assistant-config?branch=master)

### Configuration File Status 
TravisCI hasn't been sucessfully building the configuration in a while. Not sure what's going on there. I might have to switch to another CI system.

![My Home Assistant Default View](images/default_view.png)

## Architecture

I am running Home Assistant via HassOS within VMware ESXi. For the most part, I have attempted to abstract as much hardware from the equation as possible. However, I do have an [Aeotec Z-Stick](https://aeotec.com/z-wave-usb-stick/) passed through to the virtual machine for accessing the Z-Wave network.

Eventually, I would like to move this back over to an Ubuntu VM, and relocate the Z-Stick to a Raspberry Pi, where I can access it over [usbip](https://ubuntu.pkgs.org/16.04/ubuntu-universe-amd64/usbip_0.1.7-3_amd64.deb.html). Nothing against HassOS. It's a great lightweight implementation. It's just more suited for an embedded environment, rather than a virtual environment. I initially considered doing this with a second Home Assistant instance and use event/state streaming over MQTT, but it would have been a pain when I needed to update the Z-Wave network.

![My Home Assistant Architecture](images/conceptual_architecture.png)

## General Information
This configuration controls a couple of significant features in my smart home.
* Alarm Clock using my bedroom lights and TV
* Turning the outside lights on at night
* Arming the alarm system when nobody is home
* Security lighting when motion is detected at my front door

**Note: Private information is stored in secrets.yaml (not uploaded)**
