from abc import ABCMeta

from iot.core.configuration import TimeSeriesConfig
from iot.core.timeseries_storage_in_memory import InMemoryTimeSeriesStorageStrategy
from iot.core.timeseries_storage_influxdb import InfluxDbTimeSeriesStorageStrategy
from iot.core.timeseries_types import ConsumptionMeasurement
from iot.infrastructure.units import Temperature


class TimeSeriesStorage(metaclass=ABCMeta):
    def __init__(self, time_series_config: TimeSeriesConfig = None):
        if time_series_config:
            self.time_series_storage_strategy = InfluxDbTimeSeriesStorageStrategy(time_series_config)
        else:
            self.time_series_storage_strategy = InMemoryTimeSeriesStorageStrategy()

    def start(self):
        self.time_series_storage_strategy.start()

    def shutdown(self):
        self.time_series_storage_strategy.shutdown()

    def append_power_consumption(self, watt: float, thing_name: str):
        self.time_series_storage_strategy.append_power_consumption(watt, thing_name)

    def get_power_consumptions_for_last_seconds(self, seconds: int, thing_name: str) -> [ConsumptionMeasurement]:
        return self.time_series_storage_strategy.get_power_consumptions_for_last_seconds(seconds, thing_name)

    def append_room_climate(self, temperature: Temperature, humidity: float, thing_name):
        self.time_series_storage_strategy.append_room_climate(temperature, humidity, thing_name)
