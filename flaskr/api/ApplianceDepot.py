from flask import Blueprint

from iot.core.time_series_storage import TimeSeriesStorage
from iot.infrastructure.machine.appliance_depot import ApplianceDepot


def appliance_depot_api(appliance_depot: ApplianceDepot, time_series_storage: TimeSeriesStorage):
    api = Blueprint('appliance-depot_api', __name__)

    @api.get('/appliances')
    def all():
        return list(map(lambda a: a.to_dict(), appliance_depot.inventory()))

    @api.get('/appliances/<name>')
    def single(name: str):
        return appliance_depot.retrieve(name).to_dict()

    @api.get('/appliances/<name>/power-consumptions')
    def single_power_consumptions(name: str):
        return list(
            map(lambda c: c.to_dict(), time_series_storage.get_power_consumptions_for_last_seconds(60 * 60 * 4, name)))

    return api
