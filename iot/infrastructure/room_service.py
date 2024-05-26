from iot.core.configuration import IotThingConfig
from iot.core.storage import Storage
from iot.infrastructure.exceptions import DatabaseException
from iot.infrastructure.room import Room
from iot.infrastructure.units import TemperatureThresholds, Range, HumidityThresholds, Temperature


class RoomService:
    def __init__(self, storage: Storage, room_config: IotThingConfig):
        self.storage = storage
        self.room_name = room_config.name
        room: Room = storage.load_room(room_config.name)
        if room_config.temperature_thresholds:
            room.temperature_thresholds = TemperatureThresholds(
                Range(room_config.temperature_thresholds.optimal.lower,
                      room_config.temperature_thresholds.optimal.upper),
                room_config.temperature_thresholds.critical_lower, room_config.temperature_thresholds.critical_upper)
        if room_config.humidity_thresholds:
            room.humidity_thresholds = HumidityThresholds(
                Range(room_config.humidity_thresholds.optimal.lower, room_config.humidity_thresholds.optimal.upper),
                room_config.humidity_thresholds.critical_lower, room_config.humidity_thresholds.critical_upper)
        self.storage.update_thing(room)

    def update_temperature(self, new_temperature: Temperature):
        try:
            room: Room = self.storage.load_room(self.room_name)
            room.update_temperature(new_temperature)
            self.storage.update_thing(room)
        except ValueError as e:
            raise DatabaseException('Failed to save updated temperature.', e) from e

    def update_humidity(self, humidity: float):
        try:
            room: Room = self.storage.load_room(self.room_name)
            room.update_humidity(humidity)
            self.storage.update_thing(room)
        except ValueError as e:
            raise DatabaseException('Failed to save updated humidity.', e) from e

    def update_room_climate(self, temperature: Temperature, humidity: float):
        try:
            room: Room = self.storage.load_room(self.room_name)
            room.update_temperature(temperature)
            room.update_humidity(humidity)
            self.storage.update_thing(room)
            self.storage.append_room_climate(temperature, humidity, self.room_name)
        except ValueError as e:
            raise DatabaseException('Failed to save room climate.', e) from e


def supports_thing_type(thing_type) -> bool:
    return thing_type in ['room']
