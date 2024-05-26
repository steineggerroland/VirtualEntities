from flask import render_template, current_app
from flask.views import View

from iot.infrastructure.machine.appliance_depot import ApplianceDepot
from iot.infrastructure.register_of_persons import RegisterOfPersons
from iot.infrastructure.room_catalog import RoomCatalog


class ListView(View):
    def dispatch_request(self):
        appliance_depot: ApplianceDepot = current_app.appliance_depot
        room_catalog: RoomCatalog = current_app.room_catalog
        register_of_persons: RegisterOfPersons = current_app.register_of_persons
        things = appliance_depot.inventory()
        rooms = room_catalog.list_all_rooms()
        persons = register_of_persons.catalog_all()
        return render_template("virtual_entities.html", entities={'things': things, 'rooms': rooms, 'persons': persons})
