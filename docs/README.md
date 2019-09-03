# **Frozen**
I am currently in the process of moving and my home assistant instance is offline. This configuration was last valid with v0.95. This repository will be updated within the next couple of months once I am in my new home.

## Update
I am planning on doing a bit of a different setup in my next home, and I will be updating this repository over the next couple of months to reflect this. My current idea is to continue running Home Assistant in my VMware environment, with a Raspberry Pi running as a slave node that has the Z-Wave stick attached to it. This will enable me to be a little less worried about where my HASS VM is physically resided in my VMware cluster, and provide an always-on device that can sit more centrally in the house to keep all of the Z-Wave devices connected. In addition, I am going to look into integrating a ZigBee radio as well. However, these are all preliminary plans. Right now, I want to make sure I keep my documentation updated enough so anyone reading this knows where I currently am. I know my username puts me towards the top of the example list.

# Apocrathia's Home Assistant Configuration Files 
[![Build Status](https://travis-ci.org/Apocrathia/home-assistant-config.svg?branch=master)](https://travis-ci.org/Apocrathia/home-assistant-config)
[![Black Duck Security Risk](https://copilot.blackducksoftware.com/github/repos/Apocrathia/home-assistant-config/branches/master/badge-risk.svg)](https://copilot.blackducksoftware.com/github/repos/Apocrathia/home-assistant-config/branches/master)
[![Coverage Status](https://coveralls.io/repos/github/Apocrathia/home-assistant-config/badge.svg?branch=master)](https://coveralls.io/github/Apocrathia/home-assistant-config?branch=master)

### Configuration File Status 
Each commit triggers a build check by TravisCI. If this is successful, 
my local HASS instance will automagically pull down the new configuration 
and restart itself.

![My Home Assistant Default View](images/default_view.png)

## Hardware
I am running Home Assistant within Hass.io on an Ubuntu virtual machine 
which is running within VMware ESXi on an Intel NUC. For the most part, 
I have attempted to abstract as much hardware from the equation as possible.

## General Information
This configuration controls a couple of significant features in my smart home.
* Alarm Clock using my bedroom lights and TV
* Turning the outside lights on at night
* Arming the alarm system when nobody is home
* Security lighting when motion is detected at my front door

**Note: Private information is stored in secrets.yaml (not uploaded)**
