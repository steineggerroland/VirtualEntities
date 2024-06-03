import json
import logging
import sys
import threading
from time import sleep

import paho.mqtt.client as paho_mqtt

from iot.core.configuration import load_configuration

CONFIG_FILE_NAME = sys.argv[1] if len(sys.argv) > 1 else 'config.yaml'

logging.basicConfig(encoding='utf-8',
                    level=logging.DEBUG,
                    format='%(asctime)s - %(name)s(%(lineno)s) - %(levelname)s - %(message)s')

config = load_configuration(CONFIG_FILE_NAME)


def on_connect(client, userdata, flags, rc):
    logging.debug("Connected with result code %s", str(rc))


client = paho_mqtt.Client(client_id=config.mqtt.client_id)
if config.mqtt.has_credentials:
    client.username_pw_set(config.mqtt.username, config.mqtt.password)
client.on_connect = on_connect
client.connect(config.mqtt.url, config.mqtt.port)

room = {"type": "room", "temperature": 22.1, "humidity": 66.6, "topic": "kitchen/sensor/temperature"}
room2 = {"type": "room", "temperature": 22.2, "humidity": 65.43, "topic": "bath/sensor/temperature"}
thing = {"type": "appliance", "consumption": 1201.12, "topic": "consumption/topic", "unloading": "unloading/topic",
         "loading": "loading/topic"}
things = [room, room2, thing]


def notify_repeatedly():
    for t in things:
        client.publish(t['topic'], payload=json.dumps(t))
    logging.debug('sent notifications')
    logging.debug(client.is_connected())
    sleep(5)
    notify_repeatedly()


client.loop()
t = threading.Thread(target=notify_repeatedly)
t.start()
