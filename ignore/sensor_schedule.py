# import os
# import glob
# import time
# import sys
import datetime
import sens_help
from apscheduler.schedulers.background import BlockingScheduler

the_ds18x20 = sens_help.TheDS18x20()
the_garage_door = sens_help.MagDoorSwitch(pin=27, pull_up=None, active_state=False, bounce_time=0.5)


def get_temp():

    try:
        print(the_ds18x20.read_temp_f(), datetime.datetime.now())
    except Exception as error:
        print("Exception error reading temperature.")
        raise error

def get_door_state():
    try:
        print(the_garage_door.state(), datetime.datetime.now())
    except Exception as error:
        print("Exception error reading door state.")
        raise error
def startup_reads():
    get_temp()
    get_door_state()

sched = BlockingScheduler()
sched.add_job(get_temp, 'interval', seconds=30)
sched.add_job(get_door_state, 'interval', seconds=8)

startup_reads()
sched.start()


# while True:
#     try:
#         print(ds18x20.read_temp_f())
#         print(the_garage_door.state())
#         time.sleep(1)
#     except KeyboardInterrupt:
#         sys.exit(130)
#
