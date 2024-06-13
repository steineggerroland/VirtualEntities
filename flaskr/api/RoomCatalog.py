from flask import Blueprint

from iot.core.time_series_storage import TimeSeriesStorage
from iot.infrastructure.room_catalog import RoomCatalog


def room_catalog_api(room_catalog: RoomCatalog, time_series_storage: TimeSeriesStorage):
    api = Blueprint('room-catalog_api', __name__)

    @api.get('/rooms')
    def all():
        return list(map(lambda a: a.to_dict(), room_catalog.list_all_rooms()))

    @api.get('/rooms/<name>')
    def single(name: str):
        return room_catalog.find_room(name).to_dict()

    @api.get('/rooms/<name>/temperature')
    def temperature_time_line(name: str):
        return list(map(lambda c: c.to_dict(), time_series_storage.get_room_climate_for_last_seconds(60 * 60 * 4, name)))

    @api.get('/rooms/<name>/humidity')
    def humidity_time_line(name: str):
        return list(map(lambda c: c.to_dict(), time_series_storage.get_room_climate_for_last_seconds(60 * 60 * 4, name)))

    return api
