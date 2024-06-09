import os

import yamlenv
from flask import Flask, request
from flask_babel import Babel
from flask_bootstrap import Bootstrap5

from flaskr.api.ApplianceDepot import appliance_depot_api
from flaskr.views import VirtualEntities
from flaskr.views.ApplianceDetails import ApplianceDetails
from flaskr.views.Homepage import Homepage
from iot.core.time_series_storage import TimeSeriesStorage
from iot.infrastructure.machine.appliance_depot import ApplianceDepot
from iot.infrastructure.register_of_persons import RegisterOfPersons
from iot.infrastructure.room_catalog import RoomCatalog
from project import project


def create_app(default_config_file_name: str, appliance_depot: ApplianceDepot, time_series_storage: TimeSeriesStorage,
               room_catalog: RoomCatalog, register_of_persons: RegisterOfPersons, config: dict = None):
    app = Flask(__name__)

    app.config.from_file(default_config_file_name, load=yamlenv.load)
    app.config.from_mapping(config)

    app.appliance_depot = appliance_depot
    app.room_catalog = room_catalog
    app.register_of_persons = register_of_persons

    app.add_url_rule(
        "/",
        view_func=Homepage.as_view("home")
    )

    app.add_url_rule(
        "/virtual-entities/",
        view_func=VirtualEntities.ListView.as_view("ve_list")
    )

    app.add_url_rule(
        "/appliance/<name>/",
        view_func=ApplianceDetails.as_view('appliance', appliance_depot)
    )

    def locale_selector():
        return request.accept_languages.best_match(app.config['LANGUAGES'].keys())

    @app.context_processor
    def utility_processor():
        return dict(lang=locale_selector(), debug=request.args.get('debug'), project_url=project['url'])

    babel = Babel(app, default_translation_directories="../translations",
                  locale_selector=locale_selector)

    app.config['BOOTSTRAP_SERVE_LOCAL'] = True
    app.config['BOOTSTRAP_BOOTSWATCH_THEME'] = 'sketchy'
    bootstrap = Bootstrap5(app)

    app.register_blueprint(appliance_depot_api(appliance_depot, time_series_storage), url_prefix='/api/')

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    return app
