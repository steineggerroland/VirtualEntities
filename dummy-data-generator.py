import json
import logging
import sys
import threading
from random import random
from time import sleep

import paho.mqtt.client as paho_mqtt

from iot.core.configuration import MqttMeasureSource
from iot.core.configuration_manager import ConfigurationManager

CONFIG_FILE_NAME = sys.argv[1] if len(sys.argv) > 1 else 'config.yaml'
continuous: bool = sys.argv.count('--continuous') > 0

logging.basicConfig(encoding='utf-8',
                    level=logging.DEBUG,
                    format='%(asctime)s - %(name)s(%(lineno)s) - %(levelname)s - %(message)s')

config = ConfigurationManager().load(CONFIG_FILE_NAME)


def on_connect(client, userdata, flags, rc):
    logging.debug("Connected with result code %s", str(rc))


client = paho_mqtt.Client(client_id=config.mqtt.client_id)
if config.mqtt.has_credentials:
    client.username_pw_set(config.mqtt.username, config.mqtt.password)
client.on_connect = on_connect
client.connect(config.mqtt.url, config.mqtt.port)


def notify_repeatedly():
    send_random_data_for_entities()
    sleep(42)
    notify_repeatedly()


def send_random_data_for_entities():
    for entity in config.entities:
        if entity.type == "appliance":
            if entity.sources:
                for source in entity.sources.list:
                    if type(source) is MqttMeasureSource:
                        source: MqttMeasureSource = source
                        client.publish(source.mqtt_topic, round(random() * 2400, 2))
                        sleep(2)
        elif entity.type == "room":
            if entity.sources:
                for source in entity.sources.list:
                    if type(source) is MqttMeasureSource:
                        source: MqttMeasureSource = source
                        client.publish(source.mqtt_topic, json.dumps(
                            {"temperature": 15 + round(random() * 20, 2), "humidity": round(random() * 100, 2)}))
                        sleep(2)
    logging.debug('sent notifications')


if continuous:
    client.loop()
    t = threading.Thread(target=notify_repeatedly)
    t.start()
else:
    send_random_data_for_entities()
