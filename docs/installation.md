### NOTE: This document is now deprecated

# Installation

Since I run my hass.io install on an Ubuntu host, the installation process is pretty standard. For the most part, all of the heavy lifting is done by the [hass.io install script](https://github.com/home-assistant/hassio-build/tree/master/install#install-hassio).

## Host Configuration

In order to properly run the hass.io installation script, the following packages are required:

```
apparmor-utils
apt-transport-https
avahi-daemon
ca-certificates
curl
dbus
docker.io
jq
network-manager
socat
software-properties-common
```

Once these packages are installed, we're ready to install hass.io!

## Hass.io Installation

_Hats off to [Pascal Vizeli](https://github.com/pvizeli) for his work on the [hass.io build script](https://github.com/home-assistant/hassio-build/blob/master/install/hassio_install). It really makes this easy as hell._

Now just run this as root:

```
curl -sL https://raw.githubusercontent.com/home-assistant/hassio-build/master/install/hassio_install | bash -s
```

## Hass.io Configuration

If you're following this, and you're not me, here's where we part ways.

I keep all of my configurations backed up using the snapshot feature of hass.io and then it's synced to Dropbox. I will simply download my last snapshot and upload it to hass.io.

The entire purpose of making this configuration public is to share the knowledge and lessons that I have learned. Please feel free to use as much of the code here as you see fit to your own home, but don't expect it to work.

![I Have no idea what I am doing](images/ihavenoideawhatiamdoing.jpg)
