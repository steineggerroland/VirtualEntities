import json
import logging
import time
from datetime import datetime
from threading import Thread

import paho.mqtt.client as paho_mqtt
from icron import croniter

from iot.core.configuration import MqttConfiguration, Sources, Destinations, PlannedNotification
from iot.machine.MachineService import MachineService


class MqttClient:
    def __init__(self, machine_service: MachineService, mqtt_config: MqttConfiguration, mqtt_sources: Sources,
                 destinations: Destinations):
        self.machine_service = machine_service
        self.mqtt_config = mqtt_config
        self.mqtt_sources = mqtt_sources

        self.mqtt_client = paho_mqtt.Client(client_id=self.mqtt_config.client_id)
        if self.mqtt_config.has_credentials:
            self.mqtt_client.username_pw_set(self.mqtt_config.username, self.mqtt_config.password)
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.connect(self.mqtt_config.url, self.mqtt_config.port)

        self.scheduled_update_threads = list()
        for planned_notification in destinations.planned_notifications:
            thread = Thread(target=self._scheduled_updates, args=[planned_notification])
            thread.daemon = True
            self.scheduled_update_threads.append(thread)
        self.loop_thread: Thread = Thread(target=self._loop_forever)
        self.loop_thread.daemon = True

        self.logger = logging.getLogger(self.__class__.__qualname__)

    def start(self):
        if not self.loop_thread.is_alive():
            self.loop_thread.start()
        for thread in self.scheduled_update_threads:
            if not thread.is_alive():
                thread.start()

    def _scheduled_updates(self, planned_notification: PlannedNotification):
        cron = croniter(planned_notification.cron_expression, datetime.now())
        while True:
            delta = cron.get_next(datetime) - datetime.now()
            time.sleep(delta.seconds)
            try:
                self.mqtt_client.publish(planned_notification.mqtt_topic,
                                         json.dumps(self.machine_service.thing.to_dict()))
            finally:
                self.logger.info(f"Sent notification to '{planned_notification.mqtt_topic}'")

    def _loop_forever(self):
        try:
            self.mqtt_client.loop_forever()
        finally:
            self.mqtt_client.disconnect()

    def on_connect(self, client, userdata, flags, rc):
        self.logger.debug(f"Connected with result code {str(rc)}")
        client.subscribe(self.mqtt_sources.consumption_topic)

    def on_message(self, client, userdata, msg):
        if msg.topic == self.mqtt_sources.consumption_topic:
            self.machine_service.update_power_consumption(float(msg.payload))
            self.logger.debug(f"Received power consumption {float(msg.payload)}")

    def stop(self):
        self.loop_thread.join(5)
