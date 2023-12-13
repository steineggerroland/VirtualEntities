import json
import logging

from jsonpath import JSONPath

from iot.core.configuration import IotThingConfig
from iot.infrastructure.room_service import RoomService
from iot.infrastructure.units import Temperature
from iot.mqtt.mqtt_client import MqttClient


class MqttRoomMediator:
    def __init__(self, mqtt_client: MqttClient, room_service: RoomService, thing_config: IotThingConfig):
        self.mqtt_client = mqtt_client
        self.room_service = room_service
        for source in thing_config.sources.list:
            mqtt_client.subscribe(source.topic, lambda msg: self.temperature_update(msg, source.temperature_path))

        self.logger = logging.getLogger(self.__class__.__qualname__)

    def temperature_update(self, msg, json_path):
        raw_temperature = self._read_value_from_message(msg, json_path)
        if raw_temperature:
            self.room_service.update_temperature(Temperature(raw_temperature))

    def _read_value_from_message(self, msg, json_path=None):
        if not json_path:
            return float(msg)
        try:
            matching_json_values = JSONPath(json_path).parse(json.loads(msg))
            if matching_json_values:
                return matching_json_values[0]
            else:
                self.logger.debug('Received message not matching json path, msg %s, path %s' % (msg, json_path))
                return
        except TypeError:
            self.logger.error('Unsupported non-json message, msg %s' % msg)
            return
