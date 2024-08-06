from abc import ABCMeta
from typing import List

from python_event_bus import EventBus

from iot.core.configuration import TimeSeriesConfig
from iot.core.timeseries_storage_in_memory import InMemoryTimeSeriesStorageStrategy
from iot.core.timeseries_storage_influxdb import InfluxDbTimeSeriesStorageStrategy
from iot.core.timeseries_types import ConsumptionMeasurement, TemperatureHumidityMeasurement
from iot.infrastructure.appliance.appliance_events import ApplianceEvents
from iot.infrastructure.room_events import RoomEvents
from iot.infrastructure.units import Temperature


class TimeSeriesStorage(metaclass=ABCMeta):
    def __init__(self, time_series_config: TimeSeriesConfig = None):
        if time_series_config:
            self.time_series_storage_strategy = InfluxDbTimeSeriesStorageStrategy(time_series_config)
        else:
            self.time_series_storage_strategy = InMemoryTimeSeriesStorageStrategy()
        EventBus.subscribe(ApplianceEvents.CHANGED_CONFIG_NAME, self.rename)
        EventBus.subscribe(RoomEvents.CHANGED_CONFIG_NAME, self.rename)

    def start(self):
        self.time_series_storage_strategy.start()

    def shutdown(self):
        self.time_series_storage_strategy.shutdown()

    def append_power_consumption(self, measure: ConsumptionMeasurement, entity_name: str):
        return self.time_series_storage_strategy.append_power_consumption(measure, entity_name)

    def get_power_consumptions_for_last_seconds(self, seconds: int, entity_name: str) -> [ConsumptionMeasurement]:
        return self.time_series_storage_strategy.get_power_consumptions_for_last_seconds(seconds, entity_name)

    def append_room_climate(self, measure: TemperatureHumidityMeasurement, entity_name):
        return self.time_series_storage_strategy.append_room_climate(measure, entity_name)

    def get_room_climate_for_last_seconds(self, seconds: int, name: str) -> List[TemperatureHumidityMeasurement]:
        return self.time_series_storage_strategy.get_room_climate_for_last_seconds(seconds, name)

    def rename(self, name: str, old_name: str):
        self.time_series_storage_strategy.rename(old_name, name)
