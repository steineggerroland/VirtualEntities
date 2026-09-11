import json
import logging
from datetime import datetime
from threading import Thread, Event
from typing import List

from croniter import croniter
from dateutil.tz import tzlocal
from jsonpath import JSONPath

from iot.core.configuration import PlannedNotification
from iot.mqtt.mqtt_client import MqttClient


class MqttMediator:
    def __init__(self, mqtt_client):
        self.mqtt_client: MqttClient = mqtt_client
        self.logger = logging.getLogger(self.__class__.__qualname__)
        self.scheduled_update_threads: List[Thread] = []
        self._stop = Event()

    def start(self):
        for thread in self.scheduled_update_threads:
            if not thread.is_alive():
                thread.start()

    def shutdown(self, timeout=2):
        self._stop.set()
        for thread in self.scheduled_update_threads:
            if thread.is_alive():
                thread.join(timeout)

    def handle_destinations(self, planned_notifications: List[PlannedNotification], get_dict_callback):
        for planned_notification in planned_notifications:
            thread = Thread(target=self._scheduled_updates, args=[planned_notification, get_dict_callback])
            thread.daemon = True
            self.scheduled_update_threads.append(thread)

    def _scheduled_updates(self, planned_notification: PlannedNotification, get_dict_callback):
        now = datetime.now(tzlocal())
        cron = croniter(planned_notification.cron_expression, now)
        while not self._stop.is_set():
            delta = cron.get_next(datetime) - datetime.now(tzlocal())
            if self._stop.wait(max(0, delta.total_seconds())):
                return
            try:
                self.mqtt_client.publish(planned_notification.mqtt_topic, get_dict_callback())
                self.logger.debug("Sent update to '%s'", planned_notification.mqtt_topic)
            except Exception as e:
                self.logger.error("Failed to send update to '%s'", planned_notification.mqtt_topic, exc_info=e)

    def _read_value_from_message(self, msg, json_path=None, value_type=float):
        payload = msg.payload
        if not json_path:
            return value_type(payload)
        try:
            matching_json_values = JSONPath(json_path).parse(json.loads(payload))
        except TypeError:
            self.logger.error('Unsupported non-json message, msg %s' % payload)
            return
        if matching_json_values:
            return value_type(matching_json_values[0])
        else:
            self.logger.debug('Received message not matching json path, msg %s, path %s' % (payload, json_path))
            return
