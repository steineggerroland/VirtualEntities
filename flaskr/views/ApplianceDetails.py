from flask import render_template
from flask.views import View

from iot.core.time_series_storage import TimeSeriesStorage
from iot.infrastructure.machine.appliance_depot import ApplianceDepot


class ApplianceDetails(View):
    def __init__(self, appliance_depot: ApplianceDepot, times_series_storage: TimeSeriesStorage):
        self.appliance_depot = appliance_depot
        self.time_series_storage = times_series_storage

    def dispatch_request(self, name: str):
        appliance = self.appliance_depot.retrieve(name)
        time_series = self.time_series_storage.get_power_consumptions_for_last_seconds(60 * 60 * 4, name)
        return render_template("appliance_details.html", appliance=appliance, time_series=time_series)
