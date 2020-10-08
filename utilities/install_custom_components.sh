#!/bin/bash

# To be run from the root of the config folder

# Make custom_components folder
mkdir custom_components

# Enter custom_components folder
cd custom_components

# Install custom components

# alexa_media
git clone https://github.com/custom-components/alexa_media_player
mv alexa_media_player/custom_components/alexa_media alexa_media
rmdir alexa_media_player

# auto_backup
git clone https://github.com/jcwillox/hass-auto-backup
mv hass-auto-backup/custom_components/auto_backup auto_backup
rmdir hass-auto-backup

# remote_homeassistant
git clone https://github.com/lukas-hetzenecker/home-assistant-remote
mv home-assistant-remote/custom_components/remote_homeassistant remote_homeassistant
rmdir home-assistant-remote
