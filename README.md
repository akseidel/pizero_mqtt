# pizero_mqtt_monitor

## A Raspberry Pi Zero W Publishing Sensor Data as MQTT Messages for Home Assistant

* Intended to monitor sensors at set intervals and post results to mqtt broker for **Home Assistant** to subscribe.
* The general approach here uses two different methods to issue callbacks that publish data to the MQTT broker using the Python **paho-mqtt-client**. Attached sensors and Pi Zero states are read and monitored by **gpiozero** classes. **Gpiozero** sensor state change callbacks are used to publish data when the states change. Sensor data and running state data is also published at set time intervals using **apscheduler**.
* For example the **gpiozero** **LightSensor** monitoring an LDR publishes light detected and light not detected state changes when those events occur while **apscheduler** publishes the **gpiozero** **LightSensor** light intensity values at a set time interval. 
* **Apscheduler** is also used to publish Availability MQTT posts at set time intervals for **Home Assistant** to see.

### Parts In This Repository

* **pizero_mqtt_monitor.py** - The main python program. This program is set to be a **systemctl** service that starts when the **Pi Zero W** powers up.
* **sens_help.py** - A helper file used by **pizero_mqtt_monitor.py**.
* **mqtt_monitor.service** - The **systemctl** service file.
* **configuration.yaml** - The **Home Assistant** **configuration.yaml** file being used to show the **Home Assistant** MQTT configuration settings needed to coordinate with what **pizero_mqtt_monitor.py** publishes.
