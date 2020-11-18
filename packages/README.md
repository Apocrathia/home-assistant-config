# Packages

In order to keep my configuration organized and easy to work with, I have opted 
to use Home Assistant's 
[Packages](https://www.home-assistant.io/docs/configuration/packages/) 
functionality. This allows me to keep all of my code pretaining to something
together.

## Naming Convention

Although the ```package: !include_dir_named``` statement will recursively
search a directory, there is no indication withing HASS as to what folder it
actually came from. To make my files organized, I have prefixed them with a
function idenfier. That way they are grouped together in a logical manner. Most
of this follows the nomenclature outlined in the [Home Assistant Glossary](https://www.home-assistant.io/docs/glossary/).

Prefix | Description | Example
--- | --- | ---
area | Configurations related to an area of the home | area_back_yard
integration | Configurations specific to core functionality of Home Assistant | integration_ecobee
routine | Configurations to perform tasks which happen on a routine basis | routine_morning
function | Configurations that can be bundled together to perform a specific function | function_presence
system | Things that work specifically with the management of Home Assistant | system_backup
toy | Things that have no real use, but are just for fun. | toy_annoyaimee