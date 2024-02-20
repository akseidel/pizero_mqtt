import RPi.GPIO as GPIO

# to use Raspberry Pi board pin numbers
GPIO.setmode(GPIO.BOARD)

# set up the GPIO channels - one input and one output
GPIO.setup(11, GPIO.IN)
GPIO.setup(12, GPIO.OUT)

# input from pin 11
input_value = GPIO.input(11)

# output to pin 12
GPIO.output(12, GPIO.HIGH)

# the same script as above but using BCM GPIO 00..nn numbers
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN)
GPIO.setup(18, GPIO.OUT)
input_value = GPIO.input(17)
GPIO.output(18, GPIO.HIGH)

# also


# In this example below we use GPIO7 (pin 26) and GPIO8 (pin 24).
# Python scripts that use the GPIO library must be run using sudo. i.e.
# sudo python yourscript.py


import RPi.GPIO as GPIO

# Use GPIO numbers not pin numbers
GPIO.setmode(GPIO.BCM)

# set up the GPIO channels - one input and one output
GPIO.setup(7, GPIO.IN)
GPIO.setup(8, GPIO.OUT)

# input from GPIO7
input_value = GPIO.input(7)

# output to GPIO8
GPIO.output(8, True)

# another example where a pin is an output
# Again, this must be run sudo
import RPi.GPIO as GPIO
import time

# Use physical pin numbers
GPIO.setmode(GPIO.BOARD)
# Set up header pin 11 (GPIO17) as an output
print("Setup Pin 11")
GPIO.setup(11, GPIO.OUT)

var = 1
print
"Start loop"
while var == 1:
    print("Set Output False")
    GPIO.output(11, False)
    time.sleep(1)
    print("Set Output True")
    GPIO.output(11, True)
    time.sleep(1)