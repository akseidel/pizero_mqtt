import paho.mqtt.client as mqtt
import json
import random
import datetime
import time


# The callback for when the mqttc receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    thisDevice = "$SYS/#"
    client.subscribe(thisDevice)
    print("Subscribed as " + thisDevice)


# We do not care about incomming messages about these.
# The callback for when a PUBLISH message is received from the server.
# def on_message_from_doorstate(mqttc, userdata, message):
#     print("Received message '" + str(message.payload) + "' on topic '"
#           + message.topic + "' with QoS " + str(message.qos))

# def on_message_from_temperature(mqttc, userdata, message):
#     print("Received message '" + str(message.payload) + "' on topic '"
#           + message.topic + "' with QoS " + str(message.qos))


# Create MQTT mqttc
client = mqtt.Client()

# Call on_connect function to ensure broker accepted mqttc connection
client.on_connect = on_connect

# Connect to sandbox MQTT Broker
client.connect("192.168.1.110", 1883, 60)

# Establish network connection loop using loop_start() method
client.loop_start()

# Establish a client_id for the edge device (usually a hostname)
client_id = ('raspberrypi-z01')

# Establish a topic for pressure specific tags
topic_doorstate = 'homeassistant/garage/OverheadDoor'

# Establish a topic for temperature specific tags
topic_temp = 'homeassistant/garage/Temperature'

# Continuously scan input states as long as the
# scanning flag ia True.
scanning = True
scan = 1
while scanning:
    # Create dummy tags
    reading_doorstate = random.uniform(2.3, 50.5)  # psi
    reading_temp = random.uniform(120.4, 240.6)  # fahrenheit

    # Create payload for doorstate tags
    doorstate_payload = {
        "Timestamp": datetime.datetime.now().timestamp(),
        "client_id": client_id,
        "overheaddoor": reading_doorstate,
    }
    # Serialize paylaod to JSON
    payload_doorstate = json.dumps(doorstate_payload)

    # Create payload for temperature tags
    temp_payload = {
        "Timestamp": datetime.datetime.now().timestamp(),
        "client_id": client_id,
        "temp": reading_temp
    }
    # Serialize paylaod to JSON
    payload_temp = json.dumps(temp_payload)

    # # Same mqttc will subscribe to broker, but will only subscribe to pressure topic
    # mqttc.subscribe(topic_door_state, qos=1)
    # mqttc.message_callback_add(topic_door_state, on_message_from_doorstate)

    # Publish payload to Broker on defined topic
    client.publish(topic=topic_doorstate, payload=payload_doorstate, qos=0)
    client.publish(topic=topic_temp, payload=payload_temp, qos=0)

    # Create counter and add a delay to establish scan rate
    print(f'Device Scan Number: {scan}')
    scan += 1
    time.sleep(5)  # seconds
