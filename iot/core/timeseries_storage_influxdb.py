import logging
from datetime import datetime

from influxdb import InfluxDBClient

from iot.core.configuration import TimeSeriesConfig
from iot.core.time_series_storage import TimeSeriesStorage
from iot.core.timeseries_types import ConsumptionMeasurement
from iot.infrastructure.units import Temperature

CONSUMPTION_FIELD = "consumption"
THING_NAME_TAG = "thing"
POWER_CONSUMPTION_SERIES = "power_consumption"

TEMPERATURE_FIELD = "temperature"
HUMIDITY_FIELD = "humidity"
INDOOR_CLIMATE_SERIES = "indoor_climate"


class InfluxDbTimeSeriesStorage(TimeSeriesStorage):
    def __init__(self, time_series_config: TimeSeriesConfig):
        self.influxdb = InfluxDBClient(host=time_series_config.url, username=time_series_config.username,
                                       password=time_series_config.password)
        self.bucket_name = time_series_config.bucket_name
        self.influxdb.switch_database(self.bucket_name)
        self.logger = logging.getLogger(self.__class__.__qualname__)

    def start(self):
        self.influxdb.ping()

    def shutdown(self):
        self.influxdb.close()

    def append_power_consumption(self, watt: float, thing_name):
        point = {"measurement": POWER_CONSUMPTION_SERIES, "tags": {THING_NAME_TAG: thing_name},
                 "fields": {CONSUMPTION_FIELD: watt}}
        self.influxdb.write_points([point])

    def get_power_consumptions_for_last_seconds(self, seconds: int, thing_name) -> [ConsumptionMeasurement]:
        rs = self.influxdb.query(f"SELECT * FROM {POWER_CONSUMPTION_SERIES} WHERE time >= now() - {seconds}s")
        points = rs.get_points(measurement=POWER_CONSUMPTION_SERIES, tags={THING_NAME_TAG: thing_name})
        measurements = []
        self.logger.debug(points)
        for point in points:
            measurements.append(ConsumptionMeasurement(datetime.fromisoformat(point['time']), point['consumption']))
        return measurements

    def append_room_climate(self, temperature: Temperature, humidity: float, thing_name):
        point = {"measurement": INDOOR_CLIMATE_SERIES, "tags": {THING_NAME_TAG: thing_name},
                 "fields": {TEMPERATURE_FIELD: temperature.value, HUMIDITY_FIELD: humidity}}
        self.influxdb.write_points([point])
