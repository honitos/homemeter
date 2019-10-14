#!/usr/bin/python
# -*- coding: utf-8 -*-

import paho.mqtt.client as mqtt
import time

def on_connect(client, userdata, flags, rc):
    """ Connection errors rc
    0: Connection successful
    1: Connection refused – incorrect protocol version
    2: Connection refused – invalid client identifier
    3: Connection refused – server unavailable
    4: Connection refused – bad username or password
    5: Connection refused – not authorised
    6-255: Currently unused.
    """
    if rc == 0:
        client.connected_flag = True
        print("mqtt connection ok")
    else:
        print("there was an error while connecting: ", rc)

mqtt.Client.connected_flag = False
broker_address = "captain-rex"

mc = mqtt.Client(client_id="homemeter")
mc.username_pw_set("homeassistant","mqttHA")
mc.on_connect = on_connect

mc.loop_start()
print("connecting to broker...")

mc.connect(broker_address)
while not mc.connected_flag:
    print("waiting...")
    time.sleep(1)

print("starting mainloop")
mc.loop_stop()

while True:
    print(mc.publish("/test",time.time()))
    time.sleep(1)
mc.disconnect()
