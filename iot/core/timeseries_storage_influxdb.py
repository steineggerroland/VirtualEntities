import logging
from datetime import datetime

from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError

from iot.core.configuration import TimeSeriesConfig
from iot.core.time_series_storage_strategy import TimeSeriesStorageStrategy
from iot.core.timeseries_types import ConsumptionMeasurement
from iot.infrastructure.exceptions import DatabaseException
from iot.infrastructure.units import Temperature

CONSUMPTION_FIELD = "consumption"
THING_NAME_TAG = "thing"
POWER_CONSUMPTION_SERIES = "power_consumption"

TEMPERATURE_FIELD = "temperature"
HUMIDITY_FIELD = "humidity"
INDOOR_CLIMATE_SERIES = "indoor_climate"


class InfluxDbTimeSeriesStorageStrategy(TimeSeriesStorageStrategy):
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
                 "fields": {CONSUMPTION_FIELD: float(watt)}}
        try:
            self.influxdb.write_points([point])
        except InfluxDBClientError as e:
            self.logger.debug("Failed to write power consumption (%sW) for thing (%s) to influx db: %s",
                              watt, thing_name, e, exc_info=True)
            raise DatabaseException("Failed to write power consumption (%sW) for thing (%s) to influx db: %s" %
                                    (watt, thing_name, e), e) from e

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
                 "fields": {TEMPERATURE_FIELD: float(temperature.value), HUMIDITY_FIELD: float(humidity)}}
        try:
            self.influxdb.write_points([point])
        except InfluxDBClientError as e:
            self.logger.debug("Failed to write room climate (%s, %s%) for thing (%s) to influx db: %s",
                              temperature, humidity, thing_name, e, exc_info=True)
            raise DatabaseException("Failed to write room climate (%s, %d%%) for thing '%s' to influx db: %s" %
                                    (temperature, humidity, thing_name, e), e) from e

    def _change_thing_name_of_point(self, point: dict, new_name: str)-> dict:
        point['tags'][THING_NAME_TAG] = new_name
        return point

    def rename(self, old_name: str, new_name: str):
        rs = self.influxdb.query(f"SELECT * FROM {POWER_CONSUMPTION_SERIES}")
        points = rs.get_points(measurement=POWER_CONSUMPTION_SERIES, tags={THING_NAME_TAG: old_name})
        reassigned_points = map(lambda p: self._change_thing_name_of_point(p, new_name), points)
        self.influxdb.write_points(points)
        self.influxdb.delete_series(measurement=POWER_CONSUMPTION_SERIES, tags={THING_NAME_TAG: old_name})
