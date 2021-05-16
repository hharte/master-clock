# Master-Clock Daemon
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/cee2a942ecf849fbbd3e340330043e4f)](https://www.codacy.com/gh/hharte/master-clock/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=hharte/master-clock&amp;utm_campaign=Badge_Grade)

# Introduction

This Python script controls the Standard Electric Time Company’s impulse clocks with an AR2A movement.  It runs on a Raspberry Pi and uses a [3-SPDT Relay Module](https://www.amazon.com/gp/product/B07PB9KK8Q) to control the clock. The AR2A movement uses a 24VDC pulse for two seconds every minute at 58 seconds after the minute to advance the clock.  The only exception is at 59 minutes after the hour, at 58 seconds after the hour, a 48VDC pulse is used to activate the hourly correction mechanism.  The hourly correction releases the minute hand, and using gravity, the minute hand is allowed to advance to :00.


# Installation


## Hardware

The relay module should be connected to 24VDC and 48VDC as follows:

![alt_text](https://raw.githubusercontent.com/hharte/master-clock/main/pictures/impulse_clock_wiring.png "image_tooltip")

If only a 24VDC power supply is available, the clock will run fine at 24VDC, but without the benefit of the hourly correction.  In this case, please edit master_clock_daemon.py and change the AR2_Movement and AR3_Movement to False:


```
AR2_MOVEMENT = False
AR3_MOVEMENT = False
```



## Software

Note: These instructions assume you are installing the software in /home/pi/master-clock.  If you are installing to a different location, please modify the paths in `impulse_clock_daemon.service` as appropriate.


### Download master-clock:

 \
<code>git clone [https://github.com/hharte/master-clock.git](https://github.com/hharte/master-clock.git)</code>


```
cd master-clock
```


Start the impulse clock daemon and set the clock to the correct time.  On the command line, specify the clock’s displayed hour with the -h parameter, and the clock’s displayed minute with the -m parameter.  Use the -p parameter to specify a file to persist the current clock time:

`./impulse_clock_daemon.py -h 5 -m 34 /home/pi/impulse_clock_time.txt` 

Impulse_clock_daemon will calculate the number of minutes of adjustment required, and begin advancing the clock.  When the clock reaches the current time, the operation is complete. complete.


```
Impulse Clock Timing Daemon v0.6, (c) 2021
https://github.com/hharte/master-clock

current time (minutes): 293
clock time   (minutes): 303
2021-05-02 16:53:45 Adjustment of 710 minutes started.
Advancing clock  11 hours.
Advancing clock  60 minutes.
Advancing clock  1 minutes.
2021-05-02 17:01:30 Adjustment of 710 minutes completed.
```


Press Control-C to terminate impulse_clock_daemon.  This will persist the clock’s displayed time to a file.


```
^C2021-05-02 17:01:37 Caught signal at clock time: 301, persisting state.
```



## Install the Service


```
sudo cp impulse_clock_daemon.service /etc/systemd/system/
```



### To start on boot:


```
sudo systemctl enable impulse_clock_daemon.service
```



### To start manually


```
sudo systemctl start impulse_clock_daemon.service
```



### To check status


```
systemctl status impulse_clock_daemon.service

