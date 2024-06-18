from flask import render_template, redirect, url_for, flash
from flask.views import View
from flask_babel import gettext
from python_event_bus import EventBus

from flaskr.forms.ApplianceForm import ApplianceForm
from iot.core.configuration import ConfigurationManager
from iot.infrastructure.machine.appliance_depot import ApplianceDepot
from iot.infrastructure.machine.machine_service import MachineService


class Details(View):
    def __init__(self, appliance_depot: ApplianceDepot):
        self.appliance_depot = appliance_depot

    def dispatch_request(self, name: str):
        appliance = self.appliance_depot.retrieve(name)
        if appliance is not None:
            return render_template("appliance.html", appliance=appliance)
        else:
            flash(gettext("No appliance found with that name"), category="danger")
            return redirect(url_for("ve_list"))


class Configuration(View):
    methods = ['GET', 'POST']

    def __init__(self, appliance_service: MachineService, configuration_manager: ConfigurationManager):
        self.appliance_service = appliance_service
        self.configuration_manager = configuration_manager

    def dispatch_request(self, name: str):
        appliance = self.appliance_service.get_machine(name)
        if appliance is None:
            flash(gettext("No appliance found with that name"), category="danger")
            return redirect(url_for("ve_list"))
        appliance_form = ApplianceForm()
        if appliance_form.validate_on_submit():
            if name != appliance_form.name.data:
                self.configuration_manager.rename_appliance(old_name=name, new_name=appliance_form.name.data)
            flash(gettext("Appliance successfully updated"), category="success")
        else:
            flash(gettext("Failed to change appliance, see errors in the form"), category="danger")
        appliance_form.name.default = appliance.name
        appliance_form.process()
        return render_template("appliance_configuration.html", appliance=appliance, form=appliance_form)
