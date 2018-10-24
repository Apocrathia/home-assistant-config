# Apocrathia's Home Assistant Configuration Files 
[![Build Status](https://travis-ci.org/Apocrathia/home-assistant-config.svg?branch=master)](https://travis-ci.org/Apocrathia/home-assistant-config)
[![Black Duck Security Risk](https://copilot.blackducksoftware.com/github/repos/Apocrathia/home-assistant-config/branches/master/badge-risk.svg)](https://copilot.blackducksoftware.com/github/repos/Apocrathia/home-assistant-config/branches/master)

This is something that I've been meaning to get setup for a while now.
I am referencing 
[shortbloke](https://github.com/shortbloke/home_assistant_config)'s 
repository for a lot of this, as I really appcreciate the organization that 
he has come up with for all of this.

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
