import gpiozero
import time
minute_pulse_pin = gpiozero.OutputDevice('GPIO17', active_high=True, initial_value=False)
hour_pulse_pin = gpiozero.OutputDevice('GPIO27', active_high=True, initial_value=False)

def send_pulse(pin, duration):
   pin.on()
   time.sleep(duration)
   pin.off()

while True:  # Daemon loop
   # Check time until we hit 58 seconds
   while True:
      if time.localtime().tm_sec == 58:
         break
   if  time.localtime().tm_min == 59:
      send_pulse(hour_pulse_pin, 2)

   else:
      send_pulse(minute_pulse_pin, 2)

