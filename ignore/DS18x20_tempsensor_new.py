# Complete Project Details: https://RandomNerdTutorials.com/raspberry-pi-ds18b20-python/

# Based on the Adafruit example: https://github.com/adafruit/Adafruit_Learning_System_\
# Guides/blob/main/Raspberry_Pi_DS18B20_Temperature_Sensing/code.py

import os
import glob
import time
import sys
import sens_help


the_ds18x20 = sens_help.TheDS18x20()
the_garage_door = sensor_helpers.MagDoorSwitch(pin=27, pull_up=None, active_state=False, bounce_time=0.5)

while True:
    try:
        print(the_ds18x20.read_temp_f())
        print(the_garage_door.state())
        time.sleep(1)
    except KeyboardInterrupt:
        sys.exit(130)

