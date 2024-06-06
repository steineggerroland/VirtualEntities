from flask import render_template
from flask.views import View

from iot.infrastructure.machine.appliance_depot import ApplianceDepot


class ApplianceDetails(View):
    def __init__(self, appliance_depot: ApplianceDepot):
        self.appliance_depot = appliance_depot

    def dispatch_request(self, name: str):
        appliance = self.appliance_depot.retrieve(name)
        return render_template("appliance_details.html", appliance=appliance)
