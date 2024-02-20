from gpiozero import Button
import time

# No internal pull_up, an external one is provided.
# Data is pulled up in circuit. Activation, ie door closed
# pulls the data to ground. So active state is False.
door_sensor = Button(pin=27, pull_up=None, active_state=False, bounce_time=0.5)

while True:
    if door_sensor.is_pressed:
        print("Door is closed")
    else:
        print("Door is open")
    time.sleep(0.1)



