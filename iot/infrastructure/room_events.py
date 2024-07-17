from enum import Enum

from iot.core.timeseries_types import TemperatureHumidityMeasurement
from iot.infrastructure.room import Room


class RoomEvents(str, Enum):
    ADDED = "room/added"
    CHANGED_CONFIG_NAME= "room/changed_config_name"
    UPDATED_ROOM = "room/updated"
    UPDATED_ROOM_CLIMATE = "room/indoor_climate/updated"


class RoomEvent:
    def __init__(self, room: Room):
        self.room = room


class RoomClimateEvent(RoomEvent):
    def __init__(self, room: Room, measure: TemperatureHumidityMeasurement):
        super().__init__(room)
        self.measurement = measure

