from datetime import datetime

from iot.infrastructure.Thing import Thing
from iot.infrastructure.Units import Temperature


class Room(Thing):
    def __init__(self, name: str, temperature: None | Temperature = None, last_updated_at: datetime = datetime.now(),
                 last_seen_at: None | datetime = None):
        super().__init__(name, last_updated_at, last_seen_at)
        self.temperature = temperature

    def update_temperature(self, new_temperature: Temperature):
        self.temperature = new_temperature
        self.last_updated_at = self.last_seen_at = datetime.now()

    def to_dict(self):
        return {"name": self.name,
                "last_updated_at": self.last_updated_at.isoformat() if self.last_updated_at is not None else None,
                "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at is not None else None}
