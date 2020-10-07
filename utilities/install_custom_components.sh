#!/bin/bash

# This script is meant to be run by GitHub Actions.
cd /github/workspace

# Make custom_components folder
mkdir custom_components

# Enter custom_components folder
cd custom_components

# Install custom components

# alexa_media
git clone https://github.com/custom-components/alexa_media_player
mv custom_components/alexa_media alexa_media
rmdir custom_components

# auto_backup
git clone https://github.com/jcwillox/hass-auto-backup
mv custom_components/auto_backup auto_backup
rmdir custom_components

# remote_homeassistant
git clone https://github.com/lukas-hetzenecker/home-assistant-remote
mv custom_components/remote_homeassistant remote_homeassistant
rmdir custom_components
