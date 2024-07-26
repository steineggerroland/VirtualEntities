import json
import logging
import time
from datetime import datetime
from threading import Thread
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

    def start(self):
        for thread in self.scheduled_update_threads:
            if not thread.is_alive():
                thread.start()

    def shutdown(self, timeout=2):
        for thread in self.scheduled_update_threads:
            if not thread.is_alive():
                thread.join(timeout)

    def handle_destinations(self, planned_notifications: List[PlannedNotification], get_dict_callback):
        for planned_notification in planned_notifications:
            thread = Thread(target=self._scheduled_updates, args=[planned_notification, get_dict_callback])
            thread.daemon = True
            self.scheduled_update_threads.append(thread)

    def _scheduled_updates(self, planned_notification: PlannedNotification, get_dict_callback):
        now = datetime.now(tzlocal())
        cron = croniter(planned_notification.cron_expression, now)
        while True:
            delta = cron.get_next(datetime) - datetime.now(tzlocal())
            time.sleep(max(0, delta.total_seconds()))
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
