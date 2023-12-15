from datetime import datetime

from iot.infrastructure.thing import Thing, _datetime_from_dict_key
from iot.infrastructure.units import Temperature, from_dict as temperature_from_dict


class Room(Thing):
    def __init__(self, name: str, temperature: None | Temperature = None, humidity: None | float = None,
                 last_updated_at: datetime = datetime.now(), last_seen_at: None | datetime = None):
        super().__init__(name, last_updated_at, last_seen_at, 60 * 10)
        self.temperature = temperature
        self.humidity = humidity

    def update_temperature(self, new_temperature: Temperature):
        self.temperature = new_temperature
        self.last_updated_at = self.last_seen_at = datetime.now()

    def update_humidity(self, humidity):
        self.humidity = humidity
        self.last_updated_at = self.last_seen_at = datetime.now()

    def to_dict(self):
        return {"name": self.name,
                "temperature": self.temperature.to_dict() if self.temperature else None,
                "humidity": self.humidity,
                "online_status": self.online_status(),
                "last_updated_at": self.last_updated_at.isoformat() if self.last_updated_at is not None else None,
                "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at is not None else None}


def from_dict(dictionary: dict):
    return Room(dictionary['name'],
                temperature=temperature_from_dict(dictionary['temperature']) if 'temperature' in dictionary else None,
                humidity=dictionary['humidity'] if 'humidity' in dictionary else None,
                last_updated_at=_datetime_from_dict_key(dictionary, 'last_updated_at'),
                last_seen_at=_datetime_from_dict_key(dictionary, 'last_seen_at'))
