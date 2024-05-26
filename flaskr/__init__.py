import os

import yamlenv
from flask import Flask, request
from flask_babel import Babel

from flaskr.views import VirtualEntities
from iot.infrastructure.machine.appliance_depot import ApplianceDepot
from iot.infrastructure.register_of_persons import RegisterOfPersons
from iot.infrastructure.room_catalog import RoomCatalog


def create_app(default_config_file_name: str, appliance_depot: ApplianceDepot, room_catalog: RoomCatalog,
               register_of_persons: RegisterOfPersons, config: dict = None):
    app = Flask(__name__)

    app.config.from_file(default_config_file_name, load=yamlenv.load)
    app.config.from_mapping(config)

    app.appliance_depot = appliance_depot
    app.room_catalog = room_catalog
    app.register_of_persons = register_of_persons

    app.add_url_rule(
        "/virtual-entities/",
        view_func=VirtualEntities.ListView.as_view("ve_list")
    )

    babel = Babel(app, default_translation_directories="../translations",
                  locale_selector=lambda: request.accept_languages.best_match(app.config['LANGUAGES'].keys()))

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    return app
