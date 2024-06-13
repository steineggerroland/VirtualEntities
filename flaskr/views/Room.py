from flask import render_template, redirect, url_for, flash
from flask.views import View
from flask_babel import gettext
from python_event_bus import EventBus

from flaskr.forms.ApplianceForm import ApplianceForm
from iot.core.configuration import ConfigurationManager
from iot.infrastructure.machine.appliance_depot import ApplianceDepot
from iot.infrastructure.machine.machine_service import MachineService
from iot.infrastructure.room_catalog import RoomCatalog


class Details(View):
    def __init__(self, room_catalog: RoomCatalog):
        self.room_catalog = room_catalog

    def dispatch_request(self, name: str):
        room = self.room_catalog.find_room(name)
        if room is not None:
            return render_template("room.html", room=room)
        else:
            flash(gettext("No room found with name '%(name)s'", name=name))
            return redirect(url_for("ve_list"))


class Configuration(View):
    def __init__(self, room_catalog: RoomCatalog):
        self.room_catalog = room_catalog

    def dispatch_request(self, name: str):
        room = self.room_catalog.find_room(name)
        if room is not None:
            return render_template("room_configuration.html", room=room)
        else:
            flash(gettext("No room found with name '%(name)s'", name=name))
            return redirect(url_for("ve_list"))
