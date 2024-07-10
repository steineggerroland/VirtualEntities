from datetime import datetime, timedelta
from typing import List

from iot.core.time_series_storage_strategy import TimeSeriesStorageStrategy
from iot.core.timeseries_types import ConsumptionMeasurement, TemperatureHumidityMeasurement
from iot.infrastructure.units import Temperature


class InMemoryTimeSeriesStorageStrategy(TimeSeriesStorageStrategy):
    def __init__(self):
        self.power_consumption_values = {}
        self.climate_values = {}

    def append_power_consumption(self, watt: float, entity_name: str):
        power_consumption_values = self.power_consumption_values[entity_name] \
            if entity_name in self.power_consumption_values else []
        power_consumption_values.append({"watt": watt, "created_at": datetime.now().isoformat()})
        if len(power_consumption_values) > 10:
            power_consumption_values.reverse()
            power_consumption_values.pop()
            power_consumption_values.reverse()
        self.power_consumption_values[entity_name] = power_consumption_values

    def get_power_consumptions_for_last_seconds(self, seconds: int, entity_name: str) -> List[ConsumptionMeasurement]:
        power_consumption_values = self.power_consumption_values[entity_name] \
            if entity_name in self.power_consumption_values else []
        time_boundary = datetime.now() - timedelta(seconds=seconds)
        return [ConsumptionMeasurement(datetime.fromisoformat(power_consumption["created_at"]),
                                       power_consumption["watt"]) for power_consumption in power_consumption_values if
                datetime.fromisoformat(power_consumption["created_at"]) > time_boundary]

    def append_room_climate(self, temperature: Temperature, humidity: float, room_name):
        climate_values = self.climate_values[room_name] \
            if room_name in self.climate_values else []
        climate_values.append(
            {"humidity": humidity, "temperature": temperature.value, "created_at": datetime.now().isoformat()})
        if len(climate_values) > 10:
            climate_values.reverse()
            climate_values.pop()
            climate_values.reverse()
        self.climate_values[room_name] = climate_values

    def rename(self, old_name, new_name):
        if old_name in self.power_consumption_values:
            self.power_consumption_values[new_name] = self.power_consumption_values[old_name]
            del self.power_consumption_values[old_name]
        if old_name in self.climate_values:
            self.climate_values[new_name] = self.climate_values[old_name]
            del self.climate_values[old_name]

    def get_room_climate_for_last_seconds(self, seconds: int, name: str) -> List[TemperatureHumidityMeasurement]:
        if name in self.climate_values:
            return list(map(
                lambda measurement: TemperatureHumidityMeasurement(datetime.fromisoformat(measurement['created_at']),
                                                                   measurement['temperature'], measurement['humidity']),
                filter(
                    lambda measurement: datetime.now() - datetime.fromisoformat(measurement['created_at']) < timedelta(
                        seconds=seconds), self.climate_values[name])))
        else:
            return list()

    def start(self):
        pass

    def shutdown(self):
        pass
