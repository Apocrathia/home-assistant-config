# Packages

In order to keep my configuration organized and easy to work with, I have opted 
to use Home Assistant's 
[Packages](https://www.home-assistant.io/docs/configuration/packages/) 
functionality. This allows me to keep all of my code pretaining to something
together.

## Naming Convention

Although the ```package: !include_dir_named``` statement will now recursively
search a direcctory, there is no indication withing HASS as to what folder it
actually came from. To make my files organized, I have have prefixed them with a
function idenfier. That way they are grouped together in a logical manner.

Prefix | Description | Example
--- | --- | ---
component | Configurations specific to Home Assistant core functions | component_light
platform | Everything to set up and configure a specific platform. | platform_nest
routine | A collection of configurations to perform tasks which happen on a daily basis | routine_morning
function | Specific functions that can be bundled together | function_presence
system | Things that work specifically with  the management of Home Assistant | system_backup
toy | Things that have no real use, but are just for fun. | toy_annoyaimee

As I move through this, I am sure I will come up with more prefixes.