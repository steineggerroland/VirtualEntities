from flask import render_template, redirect, url_for
from flask.views import View

from flaskr.forms.ApplianceForm import ApplianceForm
from iot.infrastructure.machine.appliance_depot import ApplianceDepot


class ApplianceDetails(View):
    def __init__(self, appliance_depot: ApplianceDepot):
        self.appliance_depot = appliance_depot

    def dispatch_request(self, name: str):
        appliance = self.appliance_depot.retrieve(name)
        return render_template("appliance.html", appliance=appliance)


class UpdateAppliance(View):
    def __init__(self, appliance_depot: ApplianceDepot):
        self.appliance_depot = appliance_depot

    def dispatch_request(self, name: str):
        appliance = self.appliance_depot.retrieve(name)
        appliance_form = ApplianceForm()
        if appliance_form.validate_on_submit():
            if name != appliance_form.name.data:
                self.appliance_depot.change_name(old_name=name, new_name=appliance_form.name.data)
            return redirect(url_for('appliance', name=name))
        appliance_form.name.default = appliance.name
        appliance_form.process()
        return render_template("appliance_update.html", appliance=appliance, form=appliance_form)
