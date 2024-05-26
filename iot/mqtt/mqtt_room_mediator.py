from iot.core.configuration import IotThingConfig, Measure
from iot.infrastructure.exceptions import DatabaseException
from iot.infrastructure.room_service import RoomService
from iot.infrastructure.units import Temperature
from iot.mqtt.mqtt_client import MqttClient
from iot.mqtt.mqtt_mediator import MqttMediator


class MqttRoomMediator(MqttMediator):
    def __init__(self, mqtt_client: MqttClient, room_service: RoomService, thing_config: IotThingConfig):
        super().__init__(mqtt_client)
        self.room_service = room_service
        for source in thing_config.sources.list if thing_config.sources else []:
            mqtt_client.subscribe(source.topic, lambda msg: self._handle_message(msg, source.measures))

        self.handle_destinations(thing_config.destinations.planned_notifications if thing_config.destinations else [],
                                 lambda: self.room_service.get_room().to_dict())

    def temperature_update(self, msg, json_path=None):
        try:
            raw_temperature = self._read_value_from_message(msg, json_path, float)
            if raw_temperature:
                self.room_service.update_temperature(Temperature(raw_temperature))
        except DatabaseException as e:
            self.logger.error("Failed to save room's '%s' temperature because of database error '%s'",
                              self.room_service.get_room().name, e, exc_info=True)

    def humidity_update(self, msg, json_path=None):
        try:
            raw_humidity = self._read_value_from_message(msg, json_path, float)
            if raw_humidity:
                self.room_service.update_humidity(raw_humidity)
        except DatabaseException as e:
            self.logger.error("Failed to save room's '%s' humidity because of database error '%s'",
                              self.room_service.get_room().name, e, exc_info=True)

    def update_room_climate(self, msg, temperature_json_path=None, humidity_json_path=None):
        try:
            self.room_service.update_room_climate(
                Temperature(self._read_value_from_message(msg, temperature_json_path, float)),
                self._read_value_from_message(msg, humidity_json_path, float))
        except DatabaseException as e:
            self.logger.error("Failed to save room's '%s' climate because of database error '%s'",
                              self.room_service.get_room().name, e, exc_info=True)

    def _handle_message(self, msg, measures: [Measure]):
        unhandled_measures = list(measures)
        if any(measure.type == 'temperature' for measure in measures) and any(
                measure.type == 'humidity' for measure in measures):
            temperature_measure = next(
                (temp_measure for temp_measure in measures if temp_measure.type == 'temperature'), None)
            humidity_measure = next(
                (humidity_measure for humidity_measure in measures if humidity_measure.type == 'humidity'), None)
            self.update_room_climate(msg, temperature_measure.path, humidity_measure.path)
            unhandled_measures.remove(temperature_measure)
            unhandled_measures.remove(humidity_measure)

        for measure in unhandled_measures:
            if measure.type == 'temperature':
                self.temperature_update(msg, measure.path)
                unhandled_measures.remove(measure)
            elif measure.type == 'humidity':
                self.humidity_update(msg, measure.path)
                unhandled_measures.remove(measure)

        if unhandled_measures:
            self.logger.warn('There are unknown measures: %s' % [measure.type for measure in unhandled_measures])
