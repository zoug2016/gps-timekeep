# Info

These are instructions on how to make a Raspberry Pi into a time server, with the help of a [GPS addon board](ava.upuaut.net/store/index.php?route=product/product&path=59_60&product_id=95).

The result should be that the Pi will continuously get current time from the GPS unit, which will be then served outside via a NTP daemon. The NTP deamon will *not* run if the GPS unit does not have a signal (so as not to announce wrong time). A simple web interface is provided, to monitor the status of the GPS, NTP daemon, and some other server status data.

Note that this setup is **not** secure, so don't let the net see your Pi! (I.e. use it behind a firewall or something.)

# Installation

#### ... from a freshly installed raspbian:

### Finish configuring the raspberry

SSH daemon should be running by default. The first run should be either with a keyboard and a monitor, or plugged into a router (so that we can ssh into it, a DHCP client is waiting on the ethernet port).

	sudo raspi-config

### Install some stuff

We want a gps daemon, some clients, and some misc utils that I can't do without.

	sudo apt-get install git htop gpsd gpsd-clients supervisor lighttpd

### Adjust network config

Edit `/etc/network/interfaces`. I wanted two static configs on the ethernet port, so changed `iface eth0 inet dhcp` to

	auto eth0
	iface eth0 inet static
	  address 192.168.3.14
	  netmask 255.255.255.0
	  gateway 192.168.3.1

	auto eth0:0
	iface eth0:0 inet static
	  address 192.168.0.1
	  netmask 255.255.255.0

### To get the GPS add-on board communicating with gpsd

We need to change the default configuration (getty on the serial port), so that linux doesn't try to communicate/access the serial port, which now has a GPS unit attached to. So:

 - remove console on `ttyAMA0` from `/boot/config.txt`
 - comment out getty on `ttyAMA0` from `/etc/inittab` (probably last line)

### Make sure gpsd does not start automatically

Make it does *not* start on boot (will be managed by `supervisord`).

	sudo dpkg-reconfigure gpsd

### Make sure NTP daemon does not start automatically

Also make sure it doesn't start automatically. Also will be managed by `supervisord`:

	sudo update-rc.d ntp disable

### Make sure lighttpd does not start automatically

	sudo update-rc.d lighttpd disable

## Get the files!

Get the files and put them into `/opt/gps-timekeep` (this path is hardcoded into things -- I'm lazy).

	sudo mkdir /opt/gps-timekeep
	sudo chown pi:pi /opt/gps-timekeep
	cd /opt
	git clone https://github.com/flabbergast/gps-timekeep.git

Alternatively, download a zip by clicking on "Download ZIP" in the right column, unpack it, and copy the contents of `gps-timekeep-master` into `/opt/timekeep`.

This will get you configurations files for the daemons (will be used by [supervisor](http://supervisord.org/)), `gps-watcher` and `time-from-gps` python scripts and a python cgi script which displays system info and lets you edit some config files. What remains to be done is:

	sudo cp /opt/gps-timekeep/configs/daemons.conf /etc/supervisor/conf.d

to configure `supervisord`, and restart it

	sudo /etc/init.d/supervisor stop
	sudo /etc/init.d/supervisor start

Now you should have access to a basic info web page (on port `80`) and to `supervisord` web interface (on port `9001`).

The "Further info and configuration" webpage, as well as access to `supervisord`, is password protected (don't feel protected by this, it's not really secure). The name:pass is `admin:muflon`. If you want to change this, you need to edit two places: `/etc/supervisor/conf.d/daemons.conf` and `/opt/gps-timekeep/auth`. They need to match!

If you want to remove the password protection:

 + Edit `/etc/supervisor/conf.d/daemons.conf` and remove the two lines (`username` and `password`).
 + Remove `/opt/gps-timekeep/auth`.
 + Edit `/opt/gps-timekeep/configs/lighttpd.conf` and comment out the `auth.require` block.

## Optional extras

Some actions from the web interface require privilege escalation (I couldn't convince `lighttpd` to run as root), so:

If you want to be able to edit the system configuration from the web interface, you'll need to change the permissions of the corresponding files so that they are writable by the user/group as which the `lighttpd` web server runs. For instance:

	sudo chgrp www-data /etc/network/interfaces
	sudo chown g+w /etc/network/interfaces

This changes the group of `/etc/network/interfaces` to `www-data` and makes it group-writable.

Similarly, if you want to be able to reboot from the web interface, you need to make it possible for the `www-data` user to execute `/sbin/reboot`. The easiest (and most unsafe) way is to make `/sbin/halt` (to which `/sbin/reboot` is a symbolic link) setuid root:

	sudo chmod +s /sbin/halt

(Archlinux users need to edit `configs/lighttpd.conf` and change the user and group to `http`.)


# Some info on how it's all set up

#### Hardware side:

 + A GPS unit talks to the Pi via the serial port `/dev/ttyAMA0`, and produces PPS pulse on GPIO pin 18 (every second).
 
#### Software side:

 + Official dependencies: `supervisor`, `lighttpd`, `gpsd`, `ntpd`, `python 2.7` (and `gps` python module, the debian package is `python-gps`).
 + All the daemons and programs related to this stuff are run through [supervisor](http://supervisord.org/) daemon. So the expectation is that the used software is installed, but not automatically run by the system.
 + **Beware:** things are hardcoded to run from `/opt/gps-timekeep`! Also some assumptions that a debian-based system is used are in place (e.g. `/etc/network/interfaces`, `/sbin/reboot -> /sbin/halt`, `www-data` for `lighttpd` user/group)
 + `lighttpd` runs to provide a "web interface". Its main function is to provide info about the status of things.
 + The communication with the GPS hardware is done via `gpsd` daemon. This one is supposed to be running all the time, and all the other programs get GPS info through it. Among other things, it writes the current time received from GPS ("coarse time") to a "shared memory" segment, where it can be read by `ntpd`.
 + The time service to the "outside" is provided by `ntpd` daemon. It reads the shared memory segment to get GPS time. However, there are a couple of quirks/issues:
   + Because pi's kernel does not have the right configuration, `ntpd` can't use the PPS signal from the GPS unit directly. So a workaround daemon, `rpi_gpio_ntp`, needs to be running to receive the PPS pulses and write the precise time to the shared memory segment to be read by `ntpd`. The thing is that `rpi_gpio_ntp` needs to start only *after* GPS has a fix and the system time is approximately correct (I'm not sure how it works and why, this observation comes from my experience).
   + Sometimes, after boot, `ntpd` refuses to read time from the shared memory segment for some reason, and restarting things doesn't help me. A "fix", which seems to work for me is to set the system time to an approximately correct time *before* starting any daemons.
 + So to deal with the things above, there are two extra python programs:
   + `time-from-gps.py`: this is a "startup" script. It waits until GPS reports a fix and a time, and subsequently sets the system time (to an approximately correct one) and starts the other daemon:
   + `gps-watcher.py`: monitors the GPS for signal. If there's no signal, it stopd `ntpd` and `rpi_gpio_ntp`. If there is signal, it starts them up. Also, it regenerates the basic static html page (every 2-3 seconds).
 + Other web interface elements:
   + `supervisord` runs its own web interface on port 9001.
   + One python CGI script is provided (`serverconfig.py`), which gives more system info, and lets you edit `/etc/network/interfaces` and reboot the Pi (see "Optional Extras" for what's needed to make this work).

#### Other notes (about configuration, etc...)

+ `gpsd` parameters should contain `-n`. This is so that gpsd starts listening to the GPS device even before a client (like cgps or such) asks for it. we need this so that the timekeeping starts right away on boot.
+ To test if `rpi_gpio_ntp` receives the pulses, run (the `18` is the GPIO pin on which the PPS pulse is sent):

		sudo rpi_gpio_ntp -g 18 -d

  It should print one line every second (when the pulse comes).
+ `ntpd` configuration: The `time1` parameter for `fudge` of `SHM` source is an observed value to make the offset of this source smallish (<5ms). It's more-less the time which is takes the GPS unit to transmit info over serial and then gpsd to process and enter into the shared memory. It's likely to be larger (cca 0.350) for GPS units attached over USB.
+ Current status of the NTP daemon can be observed by running `ntpq -p` or `ntpq -pn` (`-n` for not reverse resolving IP addresses). Most important things about the output:

   - the very first column indicates status of a source: `*` means currently used/selected, `x` means not used
   - the `reach` column should have `377` for the `UPPS` source (means ntpd "sees" the source). It changes for a while after ntpd restart, then it should stabilize on `377`.
   - the `offset` is in milliseconds. Shouldn't be too big; less than 1 for the `UPPS` source, or at least single digits.
+ `lighttpd` is set up to use `/run/www` as the main document root, since the status page is updated every 2-3 seconds and so we want to use a `tmpfs` filesystem. In other words, stuff from there lives only in the memory and disappears on every reboot!

# Sources / Credits

 - [GPS addon board](ava.upuaut.net/store/index.php?route=product/product&path=59_60&product_id=95) This is the one I used. Communicates through the serial port and generates PPS on GPIO 18 (pin 12).
 - [A very comprehensive guide with pretty much everything in it.](http://www.satsignal.eu/ntp/Raspberry-Pi-NTP.html) Maybe too detailed, so slightly hard to navigate through. Also explains the other possibility to get PPS: patch and recompile the kernel.
 - [rpi_gpio_ntp source code](http://vanheusden.com/time/rpi_gpio_ntp/)

