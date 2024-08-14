import json
import logging
import sys
import threading
from random import random, choice
from time import sleep

import paho.mqtt.client as paho_mqtt

from iot.core.configuration import MqttMeasureSource
from iot.core.configuration_manager import ConfigurationManager
from iot.infrastructure.appliance.appliance_builder import ApplianceBuilder

CONFIG_FILE_NAME = sys.argv[1] if len(sys.argv) > 1 else 'config.yaml'
continuous: bool = sys.argv.count('--continuous') > 0

logging.basicConfig(encoding='utf-8',
                    level=logging.INFO,
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
    count = 0
    for entity in config.entities:
        if ApplianceBuilder.can_build(entity.type):
            if entity.sources:
                for source in entity.sources.list:
                    if type(source) is MqttMeasureSource and any(m.type == 'consumption' for m in source.measures):
                        source: MqttMeasureSource = source
                        rand = choice(['off', 'idle', 'running'])
                        if rand == 'off':
                            payload = 0
                        elif rand == 'idle':
                            payload = round(random() * 10, 2)
                        else:
                            payload = round(10 + random() * 2390, 2)
                        logging.debug('Sending to %s consumption %s', source.mqtt_topic, payload)
                        client.publish(source.mqtt_topic, payload)
                        count += 1
                        sleep(2)
        elif entity.type == "room":
            if entity.sources:
                for source in entity.sources.list:
                    if type(source) is MqttMeasureSource:
                        source: MqttMeasureSource = source
                        payload = json.dumps(
                            {"temperature": 15 + round(random() * 20, 2), "humidity": round(random() * 100, 2)})
                        logging.debug('Sending to %s indoor climate %s', source.mqtt_topic, payload)
                        client.publish(source.mqtt_topic, payload)
                        count += 1
                        sleep(2)
    logging.info('Sent %s notifications', count)


if continuous:
    client.loop()
    t = threading.Thread(target=notify_repeatedly)
    t.start()
else:
    send_random_data_for_entities()
