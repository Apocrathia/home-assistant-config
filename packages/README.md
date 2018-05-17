# Packages

In order to keep my configuration organized and easy to work with, I have opted 
to use Home Assistant's 
[Packages](https://www.home-assistant.io/docs/configuration/packages/) 
functionality. This allows me to keep all of my code pretaining to something
together.

## Naming Convention

Because the ```package: !include_dir_named``` statement does not recursively
search a direcctory, all of the relegant configuration files must be within
that folder. To make my files organized, I have have prefixed them with a
function idenfier. That way they are grouped together in a logical manner.

Prefix | Description | Example
--- | --- | ---
platform | Everything to set up and configure a specific platform. | platform_nest
routine | A collection of configurations to perform tasks which happen on a daily basis | routine_morning
function | Specific functions that can be bundled together | function_alarmclock
management | Things that work specifically with  the management of Home Assistant | management_backup
toy | Things that have no real use, but are just for fun. | toy_annoyaimee

As I move through this, I am sure I will come up with more prefixes.