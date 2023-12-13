import json
import logging
from abc import abstractmethod

from jsonpath import JSONPath


class MqttMediator:
    def __init__(self, mqtt_client):
        self.mqtt_client = mqtt_client
        self.logger = logging.getLogger(self.__class__.__qualname__)

    @abstractmethod
    def start(self):
        pass

    def _read_value_from_message(self, msg, json_path=None):
        payload = msg.payload
        if not json_path:
            return float(payload)
        try:
            matching_json_values = JSONPath(json_path).parse(json.loads(payload))
        except TypeError:
            self.logger.error('Unsupported non-json message, msg %s' % payload)
            return
        if matching_json_values:
            return matching_json_values[0]
        else:
            self.logger.debug('Received message not matching json path, msg %s, path %s' % (payload, json_path))
            return
