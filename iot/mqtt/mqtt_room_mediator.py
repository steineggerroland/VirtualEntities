from iot.core.configuration import IotThingConfig, Measure
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

        self.handle_destinations(thing_config.destinations, lambda: self.room_service.room.to_dict())

    def temperature_update(self, msg, json_path=None):
        raw_temperature = self._read_value_from_message(msg, json_path)
        if raw_temperature:
            self.room_service.update_temperature(Temperature(raw_temperature))

    def humidity_update(self, msg, json_path=None):
        raw_humidity = self._read_value_from_message(msg, json_path)
        if raw_humidity:
            self.room_service.update_humidity(raw_humidity)

    def _handle_message(self, msg, measures: [Measure]):
        for measure in measures:
            if measure.type == 'temperature':
                self.temperature_update(msg, measure.path)
            elif measure.type == 'humidity':
                self.humidity_update(msg, measure.path)
