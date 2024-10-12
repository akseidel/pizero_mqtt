# pizero_mqtt_monitor.py aks 01/27/2024
# Intended to monitor sensors at set intervals and post results to mqtt broker for
# Home Assistant to subscribe.
#
# The general approach here uses two different methods to issue callbacks that publish data
# to the MQTT broker. Attached sensors and PiZero states are read and monitored by gpiozero. Gpiozero
# sensor state change callbacks are used to publish data when states change. Sensor data and running
# state data is also published at set time intervals using apscheduler. For example the gpiozero
# LightSensor monitoring an LDR publishes light detected and light not detected state change events
# while apscheduler publishes the LightSensor light intensity values at a set time interval.
# Apscheduler is also used to publish Availability MQTT posts at set time intervals for Homeassistant
# to see.
#
# NOTE - coding for paho version 2.x. The python IDE and online information is not
# currently up to date with the 2.x breaking changes. The same applies to some gpiozero classes.
#
import paho.mqtt.client as mqtt
import json
import datetime
from datetime import timedelta
import sens_help
# from gpiozero.pins.native import NativeFactory
from gpiozero.pins.pigpio import PiGPIOFactory
from gpiozero import Device
from gpiozero import MotionSensor
from gpiozero import Button
from gpiozero import LightSensor
from apscheduler.schedulers.background import BlockingScheduler
import time
import argparse
import subprocess

# setting the default pin_factory to be the enhanced pigpio
# note: the pigpiod daemon must be running as a service
# ie sudo systemctl enable pigpiod
# Device.pin_factory = NativeFactory()
Device.pin_factory = PiGPIOFactory()

monitor_schedule = BlockingScheduler()

# The PIR motion sensor takes about 60 sec. to stabilize. Just in case it has
# not warmed up during the Pizero boot time, st_t is used to wait at least 60
# seconds after st_t.
st_t = time.monotonic()

mqtt_broker_url = "192.168.1.110"
this_hostname = "raspberrypi-z01"
this_dev = "pizero-z01"
en_out = False  # enable output for debug purposes

# Establish a client_id
client_id = this_hostname

# set topics for each sensor
tp_this_dev = 'rpiz01/garage/'
tp_avail_st = tp_this_dev + 'LWT'
tp_dr_state = tp_this_dev + 'garage_dr'
tp_temp = tp_this_dev + 'temperature'
tp_lt = tp_this_dev + 'lightsensed'
tp_pir_motion = tp_this_dev + 'pir_motion'
tp_cpu_t_state = tp_this_dev + 'cpu_temperature'
tp_pir_a_activity = tp_this_dev + 'pir_a_activity'
tp_pir_b_activity = tp_this_dev + 'pir_b_activity'
tp_wifi = tp_this_dev + 'wifi'

# Default data gpio numbers.
# Note: The temp sensor is 1-wire. 1-wire data is set up outside the program.
dp_lt = 23  # LDR
dp_pir_a = 24  # PIR A
dp_pir_b = 11  # PIR B
dp_dr = 27  # Door (a reed switch seeing a strong magnet)

# Default pir_a settings
pir_a_queue_len = 1
pir_a_poll_rate = 10
pir_a_thresh = 0.5

# Default pir_b settings
pir_b_queue_len = 1
pir_b_poll_rate = 10
pir_b_thresh = 0.5

# Default poll rate seconds
df_ds18x20_poll_int: int = 60
df_garage_dr_poll_int: int = 60
df_ldr_poll_int: int = 66
df_pizero_cpu_poll_int: int = 30
df_pir_a_poll_int: int = 90
df_pir_b_poll_int: int = 90
df_still_alive_int: int = 62
df_iw_int: int = 60


def process_any_arguments() -> None:
    """
    Process any command line arguments
    """
    global en_out

    prsr = argparse.ArgumentParser(description='Process command line settings.')
    prsr.add_argument('-d', action='store_true', help='Intended for debug purposes.')

    args = prsr.parse_args()
    en_out = args.d
    if not en_out:
        print(f'\nNot reporting the MQTT message events to the console.')
        print(f'Use the -d argument to see reporting events to the console.')


def do_msg(msg):
    if en_out:
        print(msg)


# The version2 callback for when the mqttc receives a CONNACK response from the server.
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        # success connecting
        do_msg(f'\nMQTT Broker {mqtt_broker_url} connected with result code {str(reason_code)}')

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed. But this applies to what this client
        # subscribes to, not what the other clients, like homeassistant, subscribe to.
        # client.subscribe(this_dev)
        # Update mqttc availability
        rpt_online(client, tp_avail_st)
        do_msg(f'MQTT subscribed as {this_dev}\n')


def rpt_online(client, tp):
    client.publish(topic=tp, payload='online', qos=0)


# Create MQTT mqttc instance and connect it to Broker
mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)  # breaking change in paho version 2.0
# Set on_connect callback function to ensure broker accepted mqttc connection
mqttc.on_connect = on_connect
# Set last will and testament message (required before .connect)
mqttc.will_set(topic=tp_avail_st, payload='offline', qos=0)

do_msg(f'\nChecking for reachable mqtt broker at {mqtt_broker_url}')

while not sens_help.is_host_reachable(mqtt_broker_url):
    try:
        do_msg(f'... Checking again for reachable {mqtt_broker_url}')
    except KeyboardInterrupt:
        do_msg(f'Stopping due to [Ctrl + C]')

do_msg(f'Ok, {mqtt_broker_url} is reachable.')
do_msg(f'\nAttempting MQTT Broker connection to {mqtt_broker_url}')

# Now connect.
mqttc.connect(host=mqtt_broker_url, port=1883, keepalive=90)

# set the sensor objects
ds18x20 = sens_help.TheDS18x20()
ds18x20_poll_int = df_ds18x20_poll_int

# The apscheduler and gpiozero events will be used for the garage dr.
garage_dr_sens = Button(pin=dp_dr,
                        pull_up=None,
                        active_state=False,
                        bounce_time=0.25
                        )
garage_dr_poll_int = df_garage_dr_poll_int
# The apscheduler and gpiozero events will be used for the PIR motion detectors.
pir_a = MotionSensor(pin=dp_pir_a,
                     pull_up=None,
                     queue_len=pir_a_queue_len,
                     active_state=True,
                     sample_rate=pir_a_poll_rate,
                     threshold=pir_a_thresh,
                     partial=False
                     )
pir_a_poll_int = df_pir_a_poll_int

pir_b = MotionSensor(pin=dp_pir_b,
                     pull_up=None,
                     queue_len=pir_b_queue_len,
                     active_state=True,
                     sample_rate=pir_b_poll_rate,
                     threshold=pir_b_thresh,
                     partial=False
                     )
pir_b_poll_int = df_pir_b_poll_int

ldr = LightSensor(pin=dp_lt,
                  queue_len=5,
                  charge_time_limit=0.01,
                  threshold=0.1,
                  partial=False
                  )
ldr_poll_int = df_ldr_poll_int

pizero_cpu = sens_help.CPUTempState(threshold=80.0, event_delay=10.0)
pizero_cpu_poll_int = df_pizero_cpu_poll_int


def snd_still_alive():
    rpt_online(mqttc, tp_avail_st)
    if en_out:
        print(f'\nsnd_still_alive published {tp_avail_st} as online - {datetime.datetime.now()}\n')


def snd_pizero_cpu_state():
    try:
        pizero_cpu_state = pizero_cpu.cpu_temp_state()
        if en_out:
            print(f'Pizero CPU: {pizero_cpu_state} - {datetime.datetime.now()}')

        # payload
        pizero_cpu_pld = {
            "time": datetime.datetime.now(),
            "client_id": client_id,
            "cpu_temp_c": pizero_cpu_state[0],
            "cpu_hot": pizero_cpu_state[1]
        }
        # payload to JSON
        pld_pizero_cpu = json.dumps(pizero_cpu_pld, default=str)
        mqttc.publish(topic=tp_cpu_t_state, payload=pld_pizero_cpu, retain=True, qos=0)

    except Exception as error:
        do_msg("Exception error reading dr state.")
        raise error


def snd_temp():
    try:
        ds18x20_temp = ds18x20.read_temp_f()
        if en_out:
            print(f'Temperature: {ds18x20_temp} F - {datetime.datetime.now()}')

        # payload
        temp_pld = {
            "time": datetime.datetime.now(),
            "client_id": client_id,
            "temperature": ds18x20_temp,
            "temp_unit": "F"
        }
        # payload to JSON
        pld_temp = json.dumps(temp_pld, default=str)
        mqttc.publish(topic=tp_temp, payload=pld_temp, retain=True, qos=0)

    except Exception as error:
        do_msg("Exception error reading temperature.")
        raise error


def snd_dr_state():
    try:
        if garage_dr_sens.is_active:
            rd_dr_state = "closed"
        else:
            rd_dr_state = "open"
        if en_out:
            print(f'Garage dr: {rd_dr_state} - {datetime.datetime.now()}')

        # payload
        dr_state_pld = {
            "time": datetime.datetime.now(),
            "client_id": client_id,
            "garage_dr": rd_dr_state
        }
        # payload to JSON
        pld_dr_state = json.dumps(dr_state_pld, default=str)
        mqttc.publish(topic=tp_dr_state, payload=pld_dr_state, retain=True, qos=0)

    except Exception as error:
        do_msg("Exception error reading dr state.")
        raise error


def snd_lt_sense():
    try:
        rd_lt_sensed_s = ldr.light_detected
        rd_lt_sensed_v = ldr.value
        if en_out:
            print(f'Light Sensed: {rd_lt_sensed_s} - {datetime.datetime.now()}')

        # payload
        lt_sensed_pld = {
            "time": datetime.datetime.now(),
            "client_id": client_id,
            "light_sensed_state": rd_lt_sensed_s,
            "light_sensed_value": rd_lt_sensed_v
        }
        # payload to JSON
        pld_lt_sensed = json.dumps(lt_sensed_pld, default=str)
        mqttc.publish(topic=tp_lt, payload=pld_lt_sensed, retain=True, qos=0)

    except Exception as error:
        do_msg("Exception error reading light_sensed.")
        raise error


def snd_pir_a_state():
    try:
        if timedelta(seconds=time.monotonic() - st_t).total_seconds() > 60.0:
            if en_out:
                print(f'Garage PIR_A motion: {pir_a.is_active} - {datetime.datetime.now()}')

            # payload
            motion_pld = {
                "time": datetime.datetime.now(),
                "client_id": client_id,
                "motion": pir_a.value,
                "detected": pir_a.is_active
            }
            # payload to JSON
            pld_pir_activity = json.dumps(motion_pld, default=str)
            mqttc.publish(topic=tp_pir_a_activity, payload=pld_pir_activity, retain=True, qos=0)

    except Exception as error:
        do_msg("Exception error reading PIR state.")
        raise error


def snd_pir_b_state():
    try:
        if timedelta(seconds=time.monotonic() - st_t).total_seconds() > 60.0:
            if en_out:
                print(f'Garage PIR_B motion: {pir_b.is_active} - {datetime.datetime.now()}')

            # payload
            motion_pld = {
                "time": datetime.datetime.now(),
                "client_id": client_id,
                "motion": pir_b.value,
                "detected": pir_b.is_active
            }
            # payload to JSON
            pld_pir_activity = json.dumps(motion_pld, default=str)
            mqttc.publish(topic=tp_pir_b_activity, payload=pld_pir_activity, retain=True, qos=0)

    except Exception as error:
        do_msg("Exception error reading PIR state.")
        raise error


def snd_wifi_strength():
    try:
        # CalledProcessError
        # wifi signal dBm
        cmd = "iw dev wlan0 station dump | grep signal: | cut -d' ' -f3"
        iw_dbm = subprocess.check_output(cmd, shell=True).decode("utf-8").translate({ord(i): None for i in "\n\t"})
        # wifi connected time seconds
        cmd = "iw dev wlan0 station dump | grep 'connected time' | cut -d' ' -f2 | cut -d'\t' -f2"
        iw_ctm = subprocess.check_output(cmd, shell=True).decode("utf-8").translate({ord(i): None for i in "\n\t"})

        if en_out:
            print(f'WiFi signal strength: {iw_dbm} dBm')
            print(f'WiFi connected time: {iw_ctm} seconds')

        # payload
        iw_pld = {
            "time": datetime.datetime.now(),
            "client_id": client_id,
            "iw_dbm": iw_dbm,
            "iw_ctm": iw_ctm
        }
        # payload to JSON
        pld_wifi = json.dumps(iw_pld, default=str)
        mqttc.publish(topic=tp_wifi, payload=pld_wifi, retain=True, qos=0)

    except subprocess.CalledProcessError as error:
        do_msg("Exception error reading wifi state.")
        raise error


def startup_reads():
    snd_temp()
    snd_dr_state()
    snd_pizero_cpu_state()
    snd_lt_sense()
    snd_wifi_strength()


def device_setups():
    # Register the gpiozero state change callbacks.
    pir_a.when_activated = snd_pir_a_state
    pir_a.when_deactivated = snd_pir_a_state
    pir_b.when_activated = snd_pir_b_state
    pir_b.when_deactivated = snd_pir_b_state
    garage_dr_sens.when_activated = snd_dr_state
    garage_dr_sens.when_deactivated = snd_dr_state
    ldr.when_dark = snd_lt_sense
    ldr.when_light = snd_lt_sense

    # Setup polling schedule
    monitor_schedule.add_job(snd_temp, 'interval', seconds=ds18x20_poll_int)
    monitor_schedule.add_job(snd_dr_state, 'interval', seconds=garage_dr_poll_int)
    monitor_schedule.add_job(snd_pizero_cpu_state, 'interval', seconds=pizero_cpu_poll_int)
    monitor_schedule.add_job(snd_lt_sense, 'interval', seconds=ldr_poll_int)
    monitor_schedule.add_job(snd_pir_a_state, 'interval', seconds=pir_a_poll_int)
    monitor_schedule.add_job(snd_pir_b_state, 'interval', seconds=pir_b_poll_int)
    monitor_schedule.add_job(snd_wifi_strength, 'interval', seconds=df_iw_int)

    # A patch keeping the LWT 'online'. The mqtt broker marks the subscription offline when
    # the pizero takes too long to wifi reconnect after it happens to lose wifi service. There
    # might be other reasons why the broker marks the subscription offline.
    monitor_schedule.add_job(snd_still_alive, 'interval', seconds=df_still_alive_int)


def main():
    process_any_arguments()
    mqttc.loop_start()
    device_setups()
    startup_reads()
    monitor_schedule.start()


# Execute main() function
if __name__ == '__main__':
    main()
