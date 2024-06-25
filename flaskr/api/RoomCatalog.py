import logging

from flask import Blueprint

from iot.core.time_series_storage import TimeSeriesStorage
from iot.infrastructure.room_catalog import RoomCatalog


def room_catalog_api(room_catalog: RoomCatalog, time_series_storage: TimeSeriesStorage):
    api = Blueprint('room-catalog_api', __name__)
    logger = logging.getLogger('room_catalog_api')

    @api.get('/rooms')
    def all():
        return list(map(lambda a: a.to_dict(), room_catalog.list_all_rooms()))

    @api.get('/rooms/<name>')
    def single(name: str):
        return room_catalog.find_room(name).to_dict()

    @api.get('/rooms/<name>/temperature')
    def temperature_time_line(name: str):
        temperature_time_series = list(map(lambda c: c.to_dict(), time_series_storage.get_room_climate_for_last_seconds(60 * 60 * 4, name)))
        logger.debug(f'{name}s` temperature: {temperature_time_series}')
        return temperature_time_series

    @api.get('/rooms/<name>/humidity')
    def humidity_time_line(name: str):
        humidity_time_series = list(map(lambda c: c.to_dict(), time_series_storage.get_room_climate_for_last_seconds(60 * 60 * 4, name)))
        logger.debug(f'{name}s` humidity: {humidity_time_series}')
        return humidity_time_series
    return api
