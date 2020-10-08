#!/bin/bash

# To be run from the root of the config folder
echo "Working out of $PWD"

# Make custom_components folder
mkdir -v custom_components

# Enter custom_components folder
echo "Entering custom_components directory."
cd custom_components

# Install custom components

# alexa_media
git clone https://github.com/custom-components/alexa_media_player
mv alexa_media_player/custom_components/alexa_media alexa_media
rm -rfv alexa_media_player

# auto_backup
git clone https://github.com/jcwillox/hass-auto-backup
mv hass-auto-backup/custom_components/auto_backup auto_backup
rm -rfv hass-auto-backup

# remote_homeassistant
git clone https://github.com/lukas-hetzenecker/home-assistant-remote
mv home-assistant-remote/custom_components/remote_homeassistant remote_homeassistant
rm -rfv home-assistant-remote
