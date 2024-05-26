from datetime import datetime, timedelta

from iot.core.time_series_storage_strategy import TimeSeriesStorageStrategy
from iot.core.timeseries_types import ConsumptionMeasurement
from iot.infrastructure.units import Temperature


class InMemoryTimeSeriesStorageStrategy(TimeSeriesStorageStrategy):
    def __init__(self):
        self.power_consumption_values = {}

    def append_power_consumption(self, watt: float, thing_name: str):
        power_consumption_values = self.power_consumption_values[thing_name] \
            if thing_name in self.power_consumption_values else []
        power_consumption_values.append({"watt": watt, "created_at": datetime.now().isoformat()})
        if len(power_consumption_values) > 10:
            power_consumption_values.pop()
        self.power_consumption_values[thing_name] = power_consumption_values

    def get_power_consumptions_for_last_seconds(self, seconds: int, thing_name: str) -> [ConsumptionMeasurement]:
        power_consumption_values = self.power_consumption_values[thing_name] \
            if thing_name in self.power_consumption_values else []
        time_boundary = datetime.now() - timedelta(seconds=seconds)
        return [ConsumptionMeasurement(datetime.fromisoformat(power_consumption["created_at"]),
                                       power_consumption["watt"]) for power_consumption in power_consumption_values if
                datetime.fromisoformat(power_consumption["created_at"]) > time_boundary]

    def append_room_climate(self, temperature: Temperature, humidity: float, thing_name):
        # saving in memory not necessary because they are never read
        pass

    def start(self):
        pass

    def shutdown(self):
        pass
