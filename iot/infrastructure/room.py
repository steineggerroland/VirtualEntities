from datetime import datetime

from iot.infrastructure.thing import Thing, _datetime_from_dict_key
from iot.infrastructure.units import Temperature


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


def from_dict(dictionary: dict):
    return Room(dictionary['name'], dictionary['temperature'] if 'temperature' in dictionary else None,
                last_updated_at=_datetime_from_dict_key(dictionary, 'last_updated_at'),
                last_seen_at=_datetime_from_dict_key(dictionary, 'last_seen_at'))
