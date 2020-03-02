#!/bin/bash

# This script is to setup various custom components to allow 
# configuration checks to pass.

# Save current directory to variable
CWD=$(pwd)

# Output for Travis debugging
echo "Currently working in $CWD"

# Create custom_components directory
mkdir $CWD/custom_components

# Home Assistant Remote
git clone https://github.com/lukas-hetzenecker/home-assistant-remote /tmp/remote_homeassistant
mv /tmp/remote_homeassistant/custom_components/remote_homeassistant $CWD/custom_components/remote_homeassistant 

# Auto Backup
git clone https://github.com/jcwillox/hass-auto-backup /tmp/auto_backup
mv /tmp/auto_backup/custom_components/auto_backup $CWD/custom_components/auto_backup

# I might try to create this as a git submodule eventually
# However, I just want Travis to work for now...