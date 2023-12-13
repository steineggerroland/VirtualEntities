from iot.core.configuration import IotThingConfig
from iot.core.storage import Storage
from iot.infrastructure.room import Room
from iot.infrastructure.room import from_dict as r_from_dict
from iot.infrastructure.services import DatabaseException


class RoomService:
    def __init__(self, storage: Storage, room_config: IotThingConfig):
        self.storage = storage
        self.room: Room = r_from_dict(storage.load_thing(room_config.name))

    def update_temperature(self, new_temperature):
        try:
            self.room.update_temperature(new_temperature)
            self.storage.update_thing(self.room)
        except ValueError as e:
            raise DatabaseException('Failed to save updated temperature.', e) from e


def supports_thing_type(thing_type) -> bool:
    return thing_type in ['room']
