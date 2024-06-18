from flask import render_template, redirect, url_for, flash
from flask.views import View
from flask_babel import gettext

from iot.infrastructure.room_catalog import RoomCatalog


class Details(View):
    def __init__(self, room_catalog: RoomCatalog):
        self.room_catalog = room_catalog

    def dispatch_request(self, name: str):
        room = self.room_catalog.find_room(name)
        if room is not None:
            return render_template("room.html", room=room)
        else:
            flash(gettext("No room found with name '%(name)s'", name=name), category="danger")
            return redirect(url_for("ve_list"))


class Configuration(View):
    def __init__(self, room_catalog: RoomCatalog):
        self.room_catalog = room_catalog

    def dispatch_request(self, name: str):
        room = self.room_catalog.find_room(name)
        if room is not None:
            return render_template("room_configuration.html", room=room)
        else:
            flash(gettext("No room found with name '%(name)s'", name=name), category="danger")
            return redirect(url_for("ve_list"))
