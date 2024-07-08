from flask import render_template, current_app
from flask.views import View

from iot.infrastructure.machine.appliance_depot import ApplianceDepot
from iot.infrastructure.register_of_persons import RegisterOfPersons
from iot.infrastructure.room_catalog import RoomCatalog


class ListView(View):
    def __init__(self, appliance_depot: ApplianceDepot, room_catalog: RoomCatalog,
                 register_of_persons: RegisterOfPersons):
        self.appliance_depot: ApplianceDepot = appliance_depot
        self.room_catalog: RoomCatalog = room_catalog
        self.register_of_persons: RegisterOfPersons = register_of_persons

    def dispatch_request(self):
        appliances = self.appliance_depot.inventory()
        rooms = self.room_catalog.list_all_rooms()
        persons = self.register_of_persons.catalog_all()
        return render_template("virtual_entities.html", entities={'appliance_depot': appliances, 'room_catalog': rooms,
                                                                  'register_of_persons': persons})


class Dashboard(View):
    def __init__(self, appliance_depot: ApplianceDepot, room_catalog: RoomCatalog):
        self.appliance_depot: ApplianceDepot = appliance_depot
        self.room_catalog: RoomCatalog = room_catalog

    def dispatch_request(self):
        appliances = self.appliance_depot.inventory()
        rooms = self.room_catalog.list_all_rooms()
        return render_template("dashboard.html", entities={'appliance_depot': appliances, 'room_catalog': rooms})
