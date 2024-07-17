from abc import ABCMeta, abstractmethod
from typing import List

from iot.core.timeseries_types import ConsumptionMeasurement, TemperatureHumidityMeasurement
from iot.infrastructure.units import Temperature


class TimeSeriesStorageStrategy(metaclass=ABCMeta):
    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def shutdown(self):
        pass

    @abstractmethod
    def append_power_consumption(self, measure: ConsumptionMeasurement, entity_name: str):
        pass

    @abstractmethod
    def get_power_consumptions_for_last_seconds(self, seconds: int, entity_name: str) -> List[ConsumptionMeasurement]:
        pass

    @abstractmethod
    def append_room_climate(self, measure: TemperatureHumidityMeasurement, entity_name: str):
        pass

    @abstractmethod
    def get_room_climate_for_last_seconds(self, seconds: int, name: str) -> List[TemperatureHumidityMeasurement]:
        pass

    @abstractmethod
    def rename(self, old_name: str, new_name: str):
        pass
