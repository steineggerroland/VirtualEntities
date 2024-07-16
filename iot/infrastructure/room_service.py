from python_event_bus import EventBus

from iot.core.configuration import VirtualEntityConfig
from iot.core.time_series_storage import TimeSeriesStorage
from iot.infrastructure.exceptions import DatabaseException
from iot.infrastructure.room import Room
from iot.infrastructure.room_catalog import RoomCatalog
from iot.infrastructure.units import TemperatureThresholds, Range, HumidityThresholds, Temperature


class RoomService:
    def __init__(self, room_catalog: RoomCatalog, time_series_storage: TimeSeriesStorage, room_config: VirtualEntityConfig):
        self.room_catalog = room_catalog
        self.time_series_storage = time_series_storage
        self.room_name = room_config.name
        room: Room = self.get_room()
        if room_config.temperature_thresholds:
            room.temperature_thresholds = TemperatureThresholds(
                Range(room_config.temperature_thresholds.optimal.lower,
                      room_config.temperature_thresholds.optimal.upper),
                room_config.temperature_thresholds.critical_lower, room_config.temperature_thresholds.critical_upper)
        if room_config.humidity_thresholds:
            room.humidity_thresholds = HumidityThresholds(
                Range(room_config.humidity_thresholds.optimal.lower, room_config.humidity_thresholds.optimal.upper),
                room_config.humidity_thresholds.critical_lower, room_config.humidity_thresholds.critical_upper)
        self.room_catalog.catalog(room)
        EventBus.subscribe("room/changed_config_name", self.change_name, priority=0)

    def update_temperature(self, new_temperature: Temperature):
        try:
            room: Room = self.room_catalog.find_room(self.room_name)
            room = room.update_temperature(new_temperature)
            self.room_catalog.catalog(room)
        except ValueError as e:
            raise DatabaseException('Failed to save updated temperature.', e) from e

    def update_humidity(self, humidity: float):
        try:
            room: Room = self.room_catalog.find_room(self.room_name)
            room = room.update_humidity(humidity)
            self.room_catalog.catalog(room)
        except ValueError as e:
            raise DatabaseException('Failed to save updated humidity.', e) from e

    def update_room_climate(self, temperature: Temperature, humidity: float):
        try:
            room: Room = self.room_catalog.find_room(self.room_name)
            room = room.update_temperature(temperature)
            room = room.update_humidity(humidity)
            self.room_catalog.catalog(room)
            self.time_series_storage.append_room_climate(temperature, humidity, self.room_name)
        except ValueError as e:
            raise DatabaseException('Failed to save room climate.', e) from e

    def change_name(self, name: str, old_name: str):
        if self.room_name == old_name:
            room: Room = self.room_catalog.find_room(old_name)
            room = room.change_name(name)
            self.room_catalog.decommission(old_name)
            self.room_catalog.catalog(room)
            self.room_name = name

    def get_room(self) -> Room:
        db_entry = self.room_catalog.find_room(self.room_name)
        return db_entry if db_entry is not None else Room(self.room_name)


def supports_entity_type(entity_type) -> bool:
    return entity_type in ['room']
