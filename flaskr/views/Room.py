import logging

from flask import render_template, redirect, url_for, flash
from flask.views import View, MethodView
from flask_babel import gettext

from flaskr.forms.RoomForm import RoomForm
from iot.core.configuration import ConfigurationManager
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


class Configuration(MethodView):
    init_every_request = False
    methods = ['GET', 'POST']

    def __init__(self, room_catalog: RoomCatalog, configuration_manager: ConfigurationManager):
        self.room_catalog = room_catalog
        self.configuration_manager = configuration_manager
        self.logger = logging.getLogger('Room.Configuration')

    def get(self, name: str):
        room = self.room_catalog.find_room(name)
        if room is None:
            flash(gettext("No room found with that name"), category="danger")
            return redirect(url_for("ve_list"))

        room_form = RoomForm()
        room_form.name.default = room.name
        room_form.process()
        return render_template("room_configuration.html", room=room, form=room_form)

    def post(self, name: str):
        room = self.room_catalog.find_room(name)
        if room is None:
            flash(gettext("No room found with that name"), category="danger")
            return redirect(url_for("ve_list"))

        room_form = RoomForm()
        if name != room_form.name.data and room_form.validate():
            try:
                self.configuration_manager.rename_room(old_name=name, new_name=room_form.name.data)
                flash(gettext("Room successfully updated"), category="success")
                return redirect(url_for("room_configuration", name=room_form.name.data))
            except Exception as e:
                self.logger.exception(e)
                flash(gettext("Something went wrong"), category="danger")
                return render_template("room_configuration.html", room=room, form=room_form)
        else:
            flash(gettext("Failed to change room, see errors in the form"), category="danger")
            return render_template("room_configuration.html", room=room, form=room_form)
