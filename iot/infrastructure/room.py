from datetime import datetime

from iot.infrastructure.thing import Thing, _datetime_from_dict_key
from iot.infrastructure.units import Temperature, from_dict as temperature_from_dict, TemperatureThresholds, \
    HumidityThresholds, TemperatureRating, HumidityRating, temperature_thresholds_from_dict, \
    humidity_thresholds_from_dict


class Room(Thing):
    def __init__(self, name: str, temperature: None | Temperature = None, humidity: None | float = None,
                 temperature_thresholds: TemperatureThresholds = None, humidity_thresholds: HumidityThresholds = None,
                 last_updated_at: datetime = datetime.now(), last_seen_at: None | datetime = None):
        super().__init__(name, 'room', last_updated_at, last_seen_at, 60 * 10)
        self.temperature = temperature
        self.humidity = humidity
        self.temperature_thresholds = temperature_thresholds
        self.humidity_thresholds = humidity_thresholds

    def update_temperature(self, new_temperature: Temperature):
        self.temperature = new_temperature
        self.last_updated_at = self.last_seen_at = datetime.now()

    def update_humidity(self, humidity):
        self.humidity = humidity
        self.last_updated_at = self.last_seen_at = datetime.now()

    def rate_temperature(self) -> TemperatureRating:
        if not self.temperature or not self.temperature_thresholds:
            return TemperatureRating.UNKNOWN
        if self.temperature.value < self.temperature_thresholds.frostiness_threshold:
            return TemperatureRating.CRITICAL_COLD
        if self.temperature.value < self.temperature_thresholds.optimal.lower_value:
            return TemperatureRating.COLD
        if self.temperature.value <= self.temperature_thresholds.optimal.upper_value:
            return TemperatureRating.OPTIMAL
        if self.temperature.value < self.temperature_thresholds.heat_threshold:
            return TemperatureRating.HOT
        return TemperatureRating.CRITICAL_HOT

    def rate_humidity(self) -> HumidityRating:
        if not self.humidity or not self.humidity_thresholds:
            return HumidityRating.UNKNOWN
        if self.humidity < self.humidity_thresholds.drought_threshold:
            return HumidityRating.CRITICAL_DRY
        if self.humidity < self.humidity_thresholds.optimal.lower_value:
            return HumidityRating.DRY
        if self.humidity <= self.humidity_thresholds.optimal.upper_value:
            return HumidityRating.OPTIMAL
        if self.humidity <= self.humidity_thresholds.wetness_threshold:
            return HumidityRating.WET
        return HumidityRating.CRITICAL_WET

    def to_dict(self):
        return {"name": self.name,
                "type": self.thing_type,
                "temperature": self.temperature.to_dict() if self.temperature else None,
                "humidity": self.humidity,
                "temperature_thresholds": self.temperature_thresholds.to_dict() if self.temperature_thresholds else None,
                "humidity_thresholds": self.humidity_thresholds.to_dict() if self.humidity_thresholds else None,
                "temperature_rating": self.rate_temperature(),
                "humidity_rating": self.rate_humidity(),
                "online_status": self.online_status(),
                "last_updated_at": self.last_updated_at.isoformat() if self.last_updated_at is not None else None,
                "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at is not None else None}


def from_dict(dictionary: dict):
    return Room(dictionary['name'],
                temperature=temperature_from_dict(dictionary['temperature']) if 'temperature' in dictionary else None,
                humidity=dictionary['humidity'] if 'humidity' in dictionary else None,
                temperature_thresholds=temperature_thresholds_from_dict(
                    dictionary['temperature_thresholds']) if "temperature_thresholds" in dictionary else None,
                humidity_thresholds=humidity_thresholds_from_dict(
                    dictionary['humidity_thresholds']) if "humidity_thresholds" in dictionary else None,
                last_updated_at=_datetime_from_dict_key(dictionary, 'last_updated_at'),
                last_seen_at=_datetime_from_dict_key(dictionary, 'last_seen_at'))
