import logging
from threading import Thread

import logging
from threading import Thread

import paho.mqtt.client as paho_mqtt

from iot.core.configuration import MqttConfiguration
from iot.machine.MachineService import DatabaseException


class MqttClient:
    def __init__(self, mqtt_config: MqttConfiguration):
        self.mqtt_config = mqtt_config

        self.mqtt_client = paho_mqtt.Client(client_id=self.mqtt_config.client_id)
        if self.mqtt_config.has_credentials:
            self.mqtt_client.username_pw_set(self.mqtt_config.username, self.mqtt_config.password)
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.connect(self.mqtt_config.url, self.mqtt_config.port)
        self.loop_thread: Thread = Thread(target=self._loop_forever, daemon=True)

        self.subscriptions = {}

        self.logger = logging.getLogger(self.__class__.__qualname__)

    def start(self):
        if not self.loop_thread.is_alive():
            self.loop_thread.start()

    def _loop_forever(self):
        try:
            self.mqtt_client.loop_forever()
        finally:
            self.mqtt_client.disconnect()

    def on_connect(self, client, userdata, flags, rc):
        self.logger.debug("Connected with result code %s", str(rc))
        for subscribed_topic in self.subscriptions.keys():
            client.subscribe(subscribed_topic)

    def on_message(self, client, userdata, msg):
        self.logger.debug("Received message topic '%s' payload '%s'", msg.topic, msg.payload)
        callbacks = self.subscriptions[msg.topic]
        for callback in callbacks:
            try:
                callback(msg)
            except DatabaseException as e:
                self.logger.error("Failed to handle message '%s' by one subscriber because of database error.",
                                  msg.topic, exc_info=e)

    def subscribe(self, topic: str, callback):
        self.subscriptions.setdefault(topic, [])
        self.subscriptions.get(topic).append(callback)
        self.mqtt_client.subscribe(topic)

    def publish(self, topic: str, msg=None):
        self.mqtt_client.publish(topic, payload=msg)

    def stop(self):
        self.loop_thread.join()
