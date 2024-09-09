from http import HTTPStatus

from flask import Blueprint
from flask_socketio import SocketIO

from flaskr.api.appliance import ApplianceConverter
from iot.core.time_series_storage import TimeSeriesStorage
from iot.infrastructure.appliance.appliance_depot import ApplianceDepot
from iot.infrastructure.appliance.appliance_service import ApplianceService


def appliance_depot_api(appliance_service: ApplianceService, appliance_depot: ApplianceDepot,
                        time_series_storage: TimeSeriesStorage, socketio: SocketIO, app):
    api = Blueprint('appliance-depot_api', __name__)
    converter = ApplianceConverter(app)

    @api.get('/appliances')
    def inventory():
        return list(map(converter.convert_appliance_for_frontend, appliance_depot.inventory()))

    @api.get('/appliances/<name>')
    def details(name: str):
        return converter.convert_appliance_for_frontend(appliance_depot.retrieve(name))

    @socketio.on('appliances/request', namespace='/appliances')
    def socket_details(request: dict):
        if 'name' not in request or 'nonce' not in request:
            return
        name = request['name']
        nonce = request['nonce']
        socketio.emit(f'appliances/{name}/response/{nonce}',
                      converter.convert_appliance_for_frontend(appliance_depot.retrieve(name)),
                      namespace='/appliances')

    @api.get('/appliances/<name>/run-complete-strategy')
    def run_complete_strategy(name: str):
        return appliance_service.managed_appliances.find(name).run_complete_strategy.to_dict()

    @api.get('/appliances/<name>/power-consumptions')
    def power_consumptions(name: str):
        measures = time_series_storage.get_power_consumptions_for_last_seconds(60 * 60 * 4, name)
        return list(map(lambda c: c.to_dict(), measures))

    @api.post('/appliances/<name>/unload')
    def unload(name: str):
        appliance_service.unloaded(name)
        return '', HTTPStatus.OK

    @api.post('/appliances/<name>/load')
    def load(name: str):
        appliance_service.loaded(name, True)
        return '', HTTPStatus.OK

    @api.post('/appliances/<name>/clean')
    def clean(name: str):
        appliance_service.clean(name)
        return '', HTTPStatus.OK

    @api.post('/appliances/<name>/notice-dirt')
    def notice_dirt(name: str):
        appliance_service.notice_dirt(name)
        return '', HTTPStatus.OK

    return api
