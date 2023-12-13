from iot.core.configuration import IotThingConfig
from iot.infrastructure.room_service import RoomService
from iot.infrastructure.units import Temperature
from iot.mqtt.mqtt_client import MqttClient
from iot.mqtt.mqtt_mediator import MqttMediator


class MqttRoomMediator(MqttMediator):
    def __init__(self, mqtt_client: MqttClient, room_service: RoomService, thing_config: IotThingConfig):
        super().__init__(mqtt_client)
        self.room_service = room_service
        for source in thing_config.sources.list:
            if source.type == 'temperature':
                mqtt_client.subscribe(source.topic, lambda msg: self.temperature_update(msg, source.path))

    def temperature_update(self, msg, json_path=None):
        raw_temperature = self._read_value_from_message(msg, json_path)
        if raw_temperature:
            self.room_service.update_temperature(Temperature(raw_temperature))
