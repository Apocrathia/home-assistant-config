#!/bin/bash

# To be run from the root of the config folder
echo "Working out of $PWD"

# Make custom_components folder
mkdir -v custom_components

# Enter custom_components folder
echo "Entering custom_components directory."
cd custom_components

# Install custom components

# pirateweather
git clone https://github.com/Pirate-Weather/pirate-weather-ha
mv pirate-weather-ha/custom_components/pirateweather pirateweather
rm -rfv pirate-weather-ha

# battery notes
git clone https://github.com/andrew-codechimp/HA-Battery-Notes
mv HA-Battery-Notes/custom_components/battery_notes battery_notes
rm -rfv HA-Battery-Notes
