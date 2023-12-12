import json
import logging
import time
from datetime import datetime
from threading import Thread

from croniter import croniter

from iot.core.configuration import MqttConfiguration, Sources, Destinations, PlannedNotification
from iot.machine.MachineService import MachineService, DatabaseException
from iot.mqtt.MqttClient import MqttClient


class MqttMediator:
    def __init__(self, machine_service: MachineService, mqtt_config: MqttConfiguration, mqtt_sources: Sources,
                 destinations: Destinations, mqtt_client: MqttClient):
        self.machine_service = machine_service
        self.mqtt_config = mqtt_config
        self.mqtt_sources = mqtt_sources
        self.mqtt_client = mqtt_client

        self.scheduled_update_threads = []
        for planned_notification in destinations.planned_notifications:
            thread = Thread(target=self._scheduled_updates, args=[planned_notification])
            thread.daemon = True
            self.scheduled_update_threads.append(thread)

        self.logger = logging.getLogger(self.__class__.__qualname__)

    def start(self):
        for thread in self.scheduled_update_threads:
            if not thread.is_alive():
                thread.start()
        self.mqtt_client.subscribe(self.mqtt_sources.consumption_topic, self.power_consumption_update)
        if self.mqtt_sources.loading_topic:
            self.mqtt_client.subscribe(self.mqtt_sources.loading_topic, self.load_machine)
        if self.mqtt_sources.unloading_topic:
            self.mqtt_client.subscribe(self.mqtt_sources.unloading_topic, self.unload_machine)

    def _scheduled_updates(self, planned_notification: PlannedNotification):
        cron = croniter(planned_notification.cron_expression, datetime.now())
        while True:
            delta = cron.get_next(datetime) - datetime.now()
            time.sleep(max(0, delta.total_seconds()))
            try:
                self.mqtt_client.publish(planned_notification.mqtt_topic,
                                         json.dumps(self.machine_service.thing.to_dict()))
                self.logger.debug("Sent update to '%s'", planned_notification.mqtt_topic)
            except Exception as e:
                self.logger.error("Failed to send updte to '%s'", planned_notification.mqtt_topic, exc_info=e)

    def power_consumption_update(self, msg):
        try:
            self.machine_service.update_power_consumption(float(msg.payload))
            self.logger.debug("Updated power consumption '%s'", float(msg.payload))
        except DatabaseException as e:
            self.logger.error("Failed update power consumption '%s' because of database error.", msg.topic, exc_info=e)

    def load_machine(self, msg):
        try:
            self.machine_service.loaded()
            self.logger.debug("Set machine loaded.")
        except DatabaseException as e:
            self.logger.error("Failed set machine loaded because of database error.", msg.topic, exc_info=e)

    def unload_machine(self, msg):
        try:
            self.machine_service.unloaded()
            self.logger.debug("Set machine unloaded.")
        except DatabaseException as e:
            self.logger.error("Failed set machine unloaded because of database error.", msg.topic, exc_info=e)
