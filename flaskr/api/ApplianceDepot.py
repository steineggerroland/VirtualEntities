from http import HTTPStatus

from flask import Blueprint, Response, make_response

from iot.core.configuration_manager import ConfigurationManager
from iot.core.time_series_storage import TimeSeriesStorage
from iot.infrastructure.machine.appliance_depot import ApplianceDepot
from iot.infrastructure.machine.machine_service import MachineService


def appliance_depot_api(appliance_service: MachineService, appliance_depot: ApplianceDepot,
                        time_series_storage: TimeSeriesStorage):
    api = Blueprint('appliance-depot_api', __name__)

    @api.get('/appliances')
    def inventory():
        return list(map(lambda a: a.to_dict(), appliance_depot.inventory()))

    @api.get('/appliances/<name>')
    def details(name: str):
        return appliance_depot.retrieve(name).to_dict()

    @api.get('/appliances/<name>/power-consumptions')
    def power_consumptions(name: str):
        return list(
            map(lambda c: c.to_dict(), time_series_storage.get_power_consumptions_for_last_seconds(60 * 60 * 4, name)))

    @api.post('/appliances/<name>/unload')
    def unload(name: str):
        appliance_service.unloaded(name)
        return '', HTTPStatus.OK

    @api.post('/appliances/<name>/load')
    def load(name: str):
        appliance_service.loaded(name, True)
        return '', HTTPStatus.OK

    return api
