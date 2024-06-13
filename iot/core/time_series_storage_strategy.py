from abc import ABCMeta, abstractmethod
from typing import List

from iot.core.timeseries_types import ConsumptionMeasurement
from iot.infrastructure.units import Temperature


class TimeSeriesStorageStrategy(metaclass=ABCMeta):
    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def shutdown(self):
        pass

    @abstractmethod
    def append_power_consumption(self, watt: float, thing_name: str):
        pass

    @abstractmethod
    def get_power_consumptions_for_last_seconds(self, seconds: int, thing_name: str) -> List[ConsumptionMeasurement]:
        pass

    @abstractmethod
    def append_room_climate(self, temperature: Temperature, humidity: float, thing_name: str):
        pass

    @abstractmethod
    def rename(self, old_name: str, new_name: str):
        pass
