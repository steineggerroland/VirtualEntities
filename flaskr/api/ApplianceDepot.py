from datetime import datetime, timedelta
from http import HTTPStatus

from flask import Blueprint, Response, make_response

from iot.core.configuration_manager import ConfigurationManager
from iot.core.time_series_storage import TimeSeriesStorage
from iot.core.timeseries_types import ConsumptionMeasurement
from iot.infrastructure.appliance.appliance_depot import ApplianceDepot
from iot.infrastructure.appliance.machine_service import MachineService


def appliance_depot_api(appliance_service: MachineService, appliance_depot: ApplianceDepot,
                        time_series_storage: TimeSeriesStorage):
    api = Blueprint('appliance-depot_api', __name__)

    @api.get('/appliances')
    def inventory():
        return list(map(lambda a: a.to_dict(), appliance_depot.inventory()))

    @api.get('/appliances/<name>')
    def details(name: str):
        return appliance_depot.retrieve(name).to_dict()

    @api.get('/appliances/<name>/run-complete-strategy')
    def run_complete_strategy(name: str):
        return appliance_service.managed_machines.find(name).run_complete_strategy.to_dict()

    @api.get('/appliances/<name>/power-consumptions')
    def power_consumptions(name: str):
        measures = time_series_storage.get_power_consumptions_for_last_seconds(60 * 60 * 4, name)
        appliance = appliance_depot.retrieve(name)
        if appliance.watt is not None:
            if len(measures) == 0:  # last update was before time interval
                measures.append(
                    ConsumptionMeasurement(max(datetime.now() - timedelta(seconds=60 * 60 * 4), appliance.last_seen_at),
                                           appliance.watt))
            measures.append(ConsumptionMeasurement(datetime.now(), appliance.watt))
        return list(
            map(lambda c: c.to_dict(), measures))

    @api.post('/appliances/<name>/unload')
    def unload(name: str):
        appliance_service.unloaded(name)
        return '', HTTPStatus.OK

    @api.post('/appliances/<name>/load')
    def load(name: str):
        appliance_service.loaded(name, True)
        return '', HTTPStatus.OK

    return api
