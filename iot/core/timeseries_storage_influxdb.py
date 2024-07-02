import logging
from datetime import datetime
from typing import List

from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError

from iot.core.configuration import TimeSeriesConfig
from iot.core.time_series_storage_strategy import TimeSeriesStorageStrategy
from iot.core.timeseries_types import ConsumptionMeasurement, TemperatureHumidityMeasurement
from iot.infrastructure.exceptions import DatabaseException
from iot.infrastructure.units import Temperature

MAX_COUNT_TO_UPDATE = 100

CONSUMPTION_FIELD = "consumption"
THING_NAME_TAG = "thing"
POWER_CONSUMPTION_SERIES = "power_consumption"

TEMPERATURE_FIELD = "temperature"
HUMIDITY_FIELD = "humidity"
INDOOR_CLIMATE_SERIES = "indoor_climate"


class InfluxDbTimeSeriesStorageStrategy(TimeSeriesStorageStrategy):
    def __init__(self, time_series_config: TimeSeriesConfig):
        self.influxdb = InfluxDBClient(host=time_series_config.url, port=time_series_config.port,
                                       username=time_series_config.username, password=time_series_config.password,
                                       database=time_series_config.bucket_name)
        self.bucket_name = time_series_config.bucket_name
        self.logger = logging.getLogger(self.__class__.__qualname__)

    def start(self):
        assert self.bucket_name in self.influxdb.get_list_database()

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

    def get_power_consumptions_for_last_seconds(self, seconds: int, thing_name) -> List[ConsumptionMeasurement]:
        rs = self.influxdb.query(f"SELECT * FROM {POWER_CONSUMPTION_SERIES} WHERE time >= now() - {seconds}s")
        points = rs.get_points(measurement=POWER_CONSUMPTION_SERIES, tags={THING_NAME_TAG: thing_name})
        measurements = []
        self.logger.debug(points)
        for point in points:
            measurements.append(ConsumptionMeasurement(datetime.fromisoformat(point['time']), point[CONSUMPTION_FIELD]))
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

    def get_room_climate_for_last_seconds(self, seconds: int, room_name: str) -> List[TemperatureHumidityMeasurement]:
        rs = self.influxdb.query(f"SELECT * FROM {INDOOR_CLIMATE_SERIES} WHERE time >= now() - {seconds}s")
        points = rs.get_points(measurement=INDOOR_CLIMATE_SERIES, tags={THING_NAME_TAG: room_name})
        measurements = []
        for point in points:
            measurements.append(
                TemperatureHumidityMeasurement(datetime.fromisoformat(point['time']), point[TEMPERATURE_FIELD],
                                               point[HUMIDITY_FIELD]))
        return measurements

    def rename(self, old_name: str, new_name: str):
        self._rename_thing_in_time_series(INDOOR_CLIMATE_SERIES, old_name, new_name)
        self._rename_thing_in_time_series(POWER_CONSUMPTION_SERIES, old_name, new_name)

    def _rename_thing_in_time_series(self, time_series_name: str, old_name: str, new_name: str):
        try:
            rs = self.influxdb.query(f"SELECT * FROM {time_series_name}")
            old_points = list(rs.get_points(measurement=time_series_name, tags={THING_NAME_TAG: old_name}))
            if old_points:
                chunks = [old_points[i:i + MAX_COUNT_TO_UPDATE] for i in range(0, len(old_points), MAX_COUNT_TO_UPDATE)]
                for chunk in chunks:
                    reassigned_points = list(map(lambda p: self._change_thing_name_of_point(p, new_name), chunk))
                    self.influxdb.write_points(reassigned_points)
                self.influxdb.delete_series(measurement=time_series_name, tags={THING_NAME_TAG: old_name})
        except InfluxDBClientError:  # Exception is raised on query when no data exists (404 by db)
            self.logger.debug(f'No climate data to rename for entity {old_name}')

    def _change_thing_name_of_point(self, point: dict, new_name: str) -> dict:
        try:
            point['tags'][THING_NAME_TAG] = new_name
        except KeyError as e:
            self.logger.error("Could not set entity name to point: (%s)", point)
            raise DatabaseException("Failed to change entity name.", e) from e
        return point
