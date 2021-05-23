#!/usr/bin/python3
"""Impulse Clock Master Daemon."""
import datetime
import getopt
import signal
import sys
import time
import gpiozero

AR2_MOVEMENT = True
AR2A_MOVEMENT = True
AR3_MOVEMENT = True
CLOCK_HOURS = 12
MINUTES_PER_HOUR = 60
CLOCK_MINUTES_MAX = (MINUTES_PER_HOUR * CLOCK_HOURS)

MINUTE_PULSE_PIN = gpiozero.OutputDevice('GPIO26', active_high=False, initial_value=False)   # CH1
HOUR_PULSE_PIN_AR2 = gpiozero.OutputDevice('GPIO20', active_high=False, initial_value=False) # CH2
HOUR_PULSE_PIN_AR3 = gpiozero.OutputDevice('GPIO21', active_high=False, initial_value=False) # CH3

class ClockState():
    """
    This class represents the state of the impulse clock.

    It also provides methods to persist the impulse clock state to a file, and to retrieve
    this state from a file.

    """

    def __init__(self):
        """Initialize impulse clock state."""
        self.persist_filename = "impulse_clock_time.txt"
        self.clock_minutes = 0

    def set_filename(self, filename):
        """Set filename to persist clock state."""
        self.persist_filename = filename

    def save(self):
        """Persist the current clock time to a file."""
        outstream = open(self.persist_filename, "w")
        outstream.seek(0, 0)
        outstream.write(str(self.clock_minutes))
        outstream.close()

    def restore(self):
        """Retrieve persisted clock time from a file."""
        try:
            instream = open(self.persist_filename, "r")
        except OSError:
            print("Persisted clock state file not found: " + self.persist_filename +
                  ", please specify -m, -h to set the clock.")
            sys.exit(2)

        instream.seek(0, 0)
        line = instream.read()
        instream.close()
        self.clock_minutes = int(line)

    def increment_minutes(self, minutes):
        """Increment clock minutes by the specified amount."""
        self.clock_minutes = (self.clock_minutes + minutes) % CLOCK_MINUTES_MAX

    def get_clock_minutes(self):
        """Return the current clock minutes."""
        return self.clock_minutes

    def set_clock_minutes(self, minutes):
        """Set the current clock minutes."""
        self.clock_minutes = minutes

PERSISTOBJECT = ClockState()

def signal_handler(sig, _):
    """Handle control-C and persit clock state."""
    now = datetime.datetime.now()

    # Persist clock_minutes to file.
    print(now.strftime("%Y-%m-%d %H:%M:%S") + " Caught signal " + str(sig) + " at clock time: " +
          str(PERSISTOBJECT.get_clock_minutes()) + ", persisting state.")

    PERSISTOBJECT.save()

    # Turn relays off.
    MINUTE_PULSE_PIN.off()
    HOUR_PULSE_PIN_AR2.off()
    HOUR_PULSE_PIN_AR3.off()

    sys.exit(0)

# Hook SIGINT and SIGTERM, unfortunately we can't hook SIGKILL
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def minute_send_pulse(duration):
    """Pulse the minute relay for duration seconds."""
    MINUTE_PULSE_PIN.on()
    time.sleep(duration)
    MINUTE_PULSE_PIN.off()

def hour_send_pulse(duration):
    """Pulse the hour relay for duration seconds."""
    HOUR_PULSE_PIN_AR2.on()
    HOUR_PULSE_PIN_AR3.on()
    minute_send_pulse(duration)
    HOUR_PULSE_PIN_AR2.off()
    HOUR_PULSE_PIN_AR3.off()

def advance_minutes(minutes):
    """Advance the clock the specified number of minutes."""
    for _ in range(minutes):
        time.sleep(0.5)
        minute_send_pulse(0.5)
        PERSISTOBJECT.increment_minutes(1)

    return minutes

def advance_hours(hours):
    """Advance the clock the specified number of hours."""
    while hours > 0:
        if (AR2_MOVEMENT is True or AR3_MOVEMENT is True):
            if (PERSISTOBJECT.get_clock_minutes() % MINUTES_PER_HOUR) < 35:
                minutes_to_get_to_thirty_five = 35 - (PERSISTOBJECT.get_clock_minutes()
                                                      % MINUTES_PER_HOUR)
                advance_minutes(minutes_to_get_to_thirty_five)
            hour_send_pulse(2)
            if AR2A_MOVEMENT is False:
                time.sleep(1)
                minute_send_pulse(0.5)
                time.sleep(5)
            PERSISTOBJECT.increment_minutes(25)
        else:
            if (PERSISTOBJECT.get_clock_minutes() % MINUTES_PER_HOUR) != 0:
                # Advance to the next hour :00
                advance_minutes(MINUTES_PER_HOUR - (PERSISTOBJECT.get_clock_minutes() %
                                                    MINUTES_PER_HOUR))
            else:
                advance_minutes(MINUTES_PER_HOUR)
        hours = hours - 1

def calculate_adjustment():
    """Given the current clock time, in minutes, calculate how many minutes are required to \
       advance the clock to the correct time."""
    now = datetime.datetime.now()
    now_minutes = ((now.hour * MINUTES_PER_HOUR) + now.minute) % CLOCK_MINUTES_MAX

    adjust_minutes = now_minutes - PERSISTOBJECT.get_clock_minutes()

    if adjust_minutes < 0:
        adjust_minutes += CLOCK_MINUTES_MAX

    return adjust_minutes

# Given the current clock time in minutes, and the number of minutes to adjust,
# advance the clock to the correct time.
#
# This happens in three stages:
# 1. Adjust hours by advancing to 35 minutes past the hour, and then using the hourly
#    adjustment to get to :00.
# 2. Recalculate the adjustment, then advance the minutes, by sending the minute pulse
#    to the clock at 1Hz.  The recalculation is necessary because moving the hour hand
#    by one hour can take ~37 seconds.
# 3. Recalculate the adjustment, and if the clock is still not at the correct time,
#    advance it.  This issue can happen if the previous adjustment happened around 58s
#    after the minute.
#
def adjust_clock(adjust_minutes):
    """Adjust the clock to the correct time."""
    if adjust_minutes > 0:
        # Adjust clock to the correct hour.
        adjust_hours = adjust_minutes // MINUTES_PER_HOUR

        # Adjust hour hand to the correct hour
        if adjust_hours > 0:
            print("Advancing clock ", adjust_hours, "hours.")
            advance_hours(adjust_hours)
            adjust_minutes = adjust_minutes - (adjust_hours * MINUTES_PER_HOUR)

        # Since the hourly adjustment takes a while, recalculate the minute adjustment.
        adjust_minutes = calculate_adjustment()
        if adjust_minutes > 0:
            print("Advancing clock ", adjust_minutes, "minutes.")
            advance_minutes(adjust_minutes)

            # Even the minute adjustment can take long enough to be off by one minute.
            adjust_minutes = calculate_adjustment()
            if adjust_minutes > 0:
                print("Advancing clock ", adjust_minutes, "minutes.")
                advance_minutes(adjust_minutes)


def daemon_loop():
    """Main loop of the impulse clock daemon."""
    while True:
        # Sleep until the beginning of the next second.
        microsecond = datetime.datetime.now().microsecond
        sleeptime = float((1000000 - microsecond) / 1000000.0)
        time.sleep(sleeptime)

        # Current time
        now = datetime.datetime.now()

        # Every minute, after 58s, pulse the minute pin for 1s.
        if now.second == 50:
            if ((now.minute == 59 and AR2A_MOVEMENT is True) or
                    (now.minute == 58 and AR2A_MOVEMENT is False)):
                now = datetime.datetime.now()
                print(now.strftime("%Y-%m-%d %H:%M:%S") +
                      " Clock minutes: ", PERSISTOBJECT.get_clock_minutes(), "Hourly adjust")
                hour_send_pulse(12)   # Perform hourly correction.
        elif now.second == 59:
            minute_send_pulse(1)

            PERSISTOBJECT.increment_minutes(1)
            now = datetime.datetime.now()
            print(now.strftime("%Y-%m-%d %H:%M:%S") + " Clock minutes: ",
                  PERSISTOBJECT.get_clock_minutes())

def main(argv):
    """Main entry point for clock daemon."""
    clock_hour = 0
    clock_minute = 0
    set_clock_time = False

    print("Impulse Clock Timing Daemon v0.6, (c) 2021")
    print("https://github.com/hharte/master-clock\n")
    try:
        opts, _ = getopt.getopt(argv, "p:h:m:", ["help"])
    except getopt.GetoptError:
        print('impulse_clock_daemon.py -p <filename> -h <hours> -m <minutes>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == "--help":
            print('impulse_clock_daemon.py --help -p <filename> -h <hours> -m <minutes>')
            sys.exit()
        elif opt in "-p":
            PERSISTOBJECT.set_filename(arg)
        elif opt in "-h":
            clock_hour = int(arg)
            set_clock_time = True
        elif opt in "-m":
            clock_minute = int(arg)
            set_clock_time = True

    if set_clock_time is True:
        PERSISTOBJECT.set_clock_minutes(((clock_hour * MINUTES_PER_HOUR) + clock_minute)
                                        % CLOCK_MINUTES_MAX)
    else:
        PERSISTOBJECT.restore()

    adjust_minutes = calculate_adjustment()

    if adjust_minutes > 0:
        start_adjustment_now = datetime.datetime.now()
        print("current time (minutes):",
              ((start_adjustment_now.hour * MINUTES_PER_HOUR) +
               start_adjustment_now.minute) % CLOCK_MINUTES_MAX)
        print("clock time   (minutes):", PERSISTOBJECT.get_clock_minutes())
        if adjust_minutes > 0:
            print(start_adjustment_now.strftime("%Y-%m-%d %H:%M:%S") + " Adjustment of",
                  adjust_minutes, "minutes started.")
            adjust_clock(adjust_minutes)
            end_adjustment_now = datetime.datetime.now()
            print(end_adjustment_now.strftime("%Y-%m-%d %H:%M:%S") + " Adjustment of",
                  adjust_minutes, "minutes completed.")

    daemon_loop()

if __name__ == "__main__":
    main(sys.argv[1:])
