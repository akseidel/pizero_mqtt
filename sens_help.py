# sens_help.py    aks 01/27/24
import os
import glob
import time
from gpiozero import CPUTemperature
import subprocess
# from gpiozero.pins.native import NativeFactory
from gpiozero.pins.pigpio import PiGPIOFactory
from gpiozero import Device

# setting the default pin_factory to be the enhanced pigpio
# Device.pin_factory = NativeFactory()
Device.pin_factory = PiGPIOFactory()

def is_host_reachable(the_host):
    # Returns True if URL the_host is reachable, False otherwise.
    png_cmd = ['ping', '-c', '1', the_host]
    result = subprocess.run(png_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode == 0:
        return True
    else:
        return False


class TheDS18x20:
    # The DS18x20 sensor is a 1-wire device handled by system code when enabled. RASPI-CONFIG is one
    # way to enable it. All changes to the system require rebooting.
    # The default one-wire GPIO for the Raspberry Pi is GPIO 4. This can be changed via the RPI's
    # config.txt file. Edit the dtoverlay line in the RPI config.txt file in sudo mode.
    # Add the following line at the end of the file, in which x is the GPIO you want to use for one-wire:
    # dtoverlay=w1-gpio,gpiopin=x
    #
    # For example, to enable one-wire on GPIO17, it would be as follows:
    # dtoverlay=w1-gpio,gpiopin=17 # This is header pin (or 'board pin') 11.
    # save file and reboot

    def __init__(self):
        self.device_file = ""
        try:
            # Enable the 1-wire system handled by the OS
            os.system('modprobe w1-gpio')
            # Enable DS18x20 support on the 1-wire system
            os.system('modprobe w1-therm')
            # 1-wire devices show up as files at /sys/bus/w1/devices/
            self.base_dir = '/sys/bus/w1/devices/'
            # Each DS18x20 has its own folder named 28-xxxxxxxxxxxx, where xxxxxxxxxxxx is the unique
            # address of the DS18x20 sensor. Here, just one DS18B20 assumed, so the one 28* wildcard gets the folder.
            self.device_folder = glob.glob(self.base_dir + '28*')[0]
            # The w1_slave file contains the reading in Celsius x 1000.
            self.device_file = self.device_folder + '/w1_slave'
        except IndexError:
            print(f'\nDid not find 1-wire DS18x20 temperature device.')

    def read_temp_raw(self):
        if self.device_file:
            f = open(self.device_file, 'r')
            lines = f.readlines()
            f.close()
            return lines

    def read_temp_f(self):
        lines = self.read_temp_raw()
        if lines is not None:
            while lines[0].strip()[-3:] != 'YES':
                time.sleep(0.2)
                lines = self.read_temp_raw()
            equals_pos = lines[1].find('t=')
            if equals_pos != -1:
                temp_string = lines[1][equals_pos + 2:]
                temp_c = float(temp_string) / 1000.0
                temp_f = temp_c * 9.0 / 5.0 + 32.0
                temp_f = '{0:.1f}'.format(temp_f)
                return temp_f


class CPUTempState:

    def __init__(self,
                 sensor_file: str = '/sys/class/thermal/thermal_zone0/temp',
                 min_temp: float = 0.0,
                 max_temp: float = 100.0,
                 threshold: float = 80.0,
                 event_delay: float = 10.0
                 ) -> None:
        # read gpiozero LightSensor docs
        self.cpu_temp = CPUTemperature(sensor_file=sensor_file,
                                       min_temp=min_temp,
                                       max_temp=max_temp,
                                       threshold=threshold,
                                       event_delay=event_delay)

    def cpu_temp_state(self) -> tuple:
        t = self.cpu_temp.temperature
        if t > self.cpu_temp.threshold:
            return t, True
        else:
            return t, False
