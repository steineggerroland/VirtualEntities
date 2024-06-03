from typing import List

from iot.core.storage import Storage
from iot.infrastructure.room import Room


class RoomCatalog:
    def __init__(self, storage: Storage):
        self.storage = storage

    def catalog(self, room) -> bool:
        """Add or update a room's details."""
        return self.storage.update(room)

    def decommission(self, name) -> bool:
        """Remove a room by name."""
        return self.storage.remove(name)

    def find_room(self, name) -> Room:
        """Retrieve a room's details by name."""
        return self.storage.load_room(name)

    def list_all_rooms(self) -> List[Room]:
        """List all rooms."""
        return self.storage.load_all_rooms()
