import json
import logging
from threading import Thread
from typing import Callable

import paho.mqtt.client as paho_mqtt
from paho.mqtt.enums import CallbackAPIVersion

from iot.core.configuration import MqttConfiguration
from iot.infrastructure.machine.machine_service import DatabaseException


class Subscription:
    def __init__(self, name: str, topic: str, callback: Callable):
        self.name = name
        self.topic = topic
        self.callback = callback


class Subscriptions:
    def __init__(self):
        self.subscriptions = []

    def add(self, subscription: Subscription):
        self.subscriptions.append(subscription)

    def get_and_remove_all_of(self, name: str):
        removed_subscriptions = list(filter(lambda s: s.name == name, self.subscriptions))
        for subscription in removed_subscriptions:
            self.subscriptions.remove(subscription)
        return removed_subscriptions

    def get_topics(self):
        return set(map(lambda subscription: subscription.topic, self.subscriptions))

    def get_callbacks_for(self, topic: str):
        return list(map(lambda subscription: subscription.callback,
                        filter(lambda subscription: subscription.topic == topic, self.subscriptions)))


class MqttClient:
    def __init__(self, mqtt_config: MqttConfiguration):
        self.logger = logging.getLogger(self.__class__.__qualname__)
        self.mqtt_config = mqtt_config

        self.mqtt_client = paho_mqtt.Client(CallbackAPIVersion.VERSION1, client_id=self.mqtt_config.client_id)
        if self.mqtt_config.has_credentials:
            self.mqtt_client.username_pw_set(self.mqtt_config.username, self.mqtt_config.password)
            self.logger.debug(
                'Connecting to mqtt server "%s:pwlen%s@%s:%s"' % (
                    mqtt_config.username, len(mqtt_config.password), mqtt_config.url, mqtt_config.port))
        else:
            self.logger.debug(
                'Connecting to mqtt server "%s:%s"' % (mqtt_config.url, mqtt_config.port))
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

        self.loop_thread: Thread = Thread(target=self._loop_forever, daemon=True)
        self.subscriptions = Subscriptions()
        self.mqtt_client.connect(self.mqtt_config.url, self.mqtt_config.port)

    def start(self):
        if not self.loop_thread.is_alive():
            self.loop_thread.start()

    def _loop_forever(self):
        try:
            self.mqtt_client.loop_forever()
        finally:
            self.mqtt_client.disconnect()

    def on_connect(self, client, userdata, flags, reason_code):
        self.logger.debug("Connected with result code %s", str(reason_code))
        for subscribed_topic in self.subscriptions.get_topics():
            client.subscribe(subscribed_topic)

    def on_message(self, client, userdata, msg):
        self.logger.debug("Received message topic '%s' payload '%s'", msg.topic, msg.payload)
        callbacks = self.subscriptions.get_callbacks_for(msg.topic)
        for callback in callbacks:
            try:
                callback(msg)
            except DatabaseException as e:
                self.logger.error("Failed to handle message '%s' by one subscriber because of database error: %s",
                                  msg.topic, e, exc_info=True)
            except Exception as e:
                self.logger.error("Failed to handle message '%s' by one subscriber with error: %s",
                                  msg.topic, e, exc_info=True)

    def subscribe(self, name: str, topic: str, callback):
        self.subscriptions.add(Subscription(name, topic, callback))
        self.mqtt_client.subscribe(topic)

    def unsubscribe(self, name: str):
        removed_subscriptions = self.subscriptions.get_and_remove_all_of(name)
        all_topics = self.subscriptions.get_topics()
        for sub in set(filter(lambda s: s.topic not in all_topics, removed_subscriptions)):
            self.mqtt_client.unsubscribe(sub.topic)

    def publish(self, topic: str, payload: str | dict = None):
        msg = json.dumps(payload) if isinstance(payload, dict) else payload
        self.mqtt_client.publish(topic, payload=msg)

    def stop(self, timeout=5):
        self.loop_thread.join(timeout)
