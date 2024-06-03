from abc import ABCMeta, abstractmethod

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
    def get_power_consumptions_for_last_seconds(self, seconds: int, thing_name: str) -> [ConsumptionMeasurement]:
        pass

    @abstractmethod
    def append_room_climate(self, temperature: Temperature, humidity: float, thing_name: str):
        pass
