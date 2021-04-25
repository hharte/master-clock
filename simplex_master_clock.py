#!/usr/bin/python3
import datetime
import gpiozero
import signal
import sys
import time

minute_pulse_pin = gpiozero.OutputDevice('GPIO17', active_high=True, initial_value=False)
hour_pulse_pin = gpiozero.OutputDevice('GPIO27', active_high=True, initial_value=False)

def signal_handler(signal, frame):
    print ("Caught signal, exiting.")
    
    # if the user presses ^C, turn relays off.
    minute_pulse_pin.off()
    hour_pulse_pin.off()
    sys.exit(0)

# Hook SIGINT and SIGTERM, unfortunately we can't hook SIGKILL
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def send_pulse(pin, duration):
    now = datetime.datetime.now()
    pin.on()
    print (now.strftime("%Y-%m-%d %H:%M:%S") + " Pulsing relay for " + str(duration) + "s...")
    time.sleep(duration)
    pin.off()

while True:
    # Sleep until the beginning of the next second.
    microsecond = datetime.datetime.now().microsecond
    sleeptime = float((1000000 - microsecond) / 1000000.0)
    time.sleep(sleeptime)

    # Current time
    now = datetime.datetime.now()

    # All adjustments happen at 57m, 54s past the hour.
    if now.minute == 57 and now.second == 54:
        if (now.hour == 5 or now.hour == 17):
            send_pulse(minute_pulse_pin, 14)
        else:
            send_pulse(minute_pulse_pin, 8)

