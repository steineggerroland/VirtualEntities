import os
import secrets

import yamlenv
from flask import Flask, request
from flask_babel import Babel, gettext
from flask_bootstrap import Bootstrap5
from flask_socketio import SocketIO

from flaskr.api.appliance_depot import appliance_depot_api
from flaskr.api.appliance_socket_notifier import ApplianceSocketNotifier
from flaskr.api.person_socket_notifier import PersonSocketNotifier
from flaskr.api.room_catalog import room_catalog_api
from flaskr.api.room_socket_notifier import RoomSocketNotifier
from flaskr.frontend_translations import frontend_translations
from flaskr.options_controller import options_blueprint
from flaskr.views import VirtualEntities, Room, Appliance, Person
from flaskr.views.Homepage import Homepage
from iot.core.configuration_manager import ConfigurationManager
from iot.core.time_series_storage import TimeSeriesStorage
from iot.infrastructure.appliance.appliance_depot import ApplianceDepot
from iot.infrastructure.appliance.appliance_service import ApplianceService
from iot.infrastructure.register_of_persons import RegisterOfPersons
from iot.infrastructure.room_catalog import RoomCatalog
from project import Project


def create_app(default_config_file_name: str, appliance_service: ApplianceService, appliance_depot: ApplianceDepot,
               time_series_storage: TimeSeriesStorage, room_catalog: RoomCatalog,
               register_of_persons: RegisterOfPersons, configuration_manager: ConfigurationManager,
               flask_config: dict = None):
    app = Flask(__name__)

    app.secret_key = secrets.token_urlsafe(16)
    app.config.from_file(default_config_file_name, load=yamlenv.load)
    app.config.from_mapping(flask_config)

    socketio = SocketIO(app)

    @socketio.on('celebrate')
    def handle_celebrate():
        socketio.emit('celebrate')

    app.add_url_rule(
        "/",
        view_func=Homepage.as_view("home")
    )
    app.add_url_rule(
        "/virtual-entities.html",
        view_func=VirtualEntities.ListView.as_view("ve_list", appliance_depot, room_catalog, register_of_persons)
    )
    app.add_url_rule(
        "/dashboard.html",
        view_func=VirtualEntities.Dashboard.as_view("ve_dashboard", appliance_depot, room_catalog)
    )

    app.add_url_rule(
        "/appliance/<name>.html",
        view_func=Appliance.Details.as_view('appliance', appliance_depot)
    )
    app.add_url_rule(
        "/appliance/<name>/configuration.html",
        view_func=Appliance.Configuration.as_view('appliance_configuration', appliance_service, configuration_manager)
    )
    app.register_blueprint(appliance_depot_api(appliance_service, appliance_depot, time_series_storage, socketio, app),
                           url_prefix='/api/')

    app.add_url_rule(
        "/room/<name>.html",
        view_func=Room.Details.as_view('room', room_catalog)
    )
    app.add_url_rule(
        "/room/<name>/configuration.html",
        view_func=Room.Configuration.as_view('room_configuration', room_catalog, configuration_manager)
    )
    app.register_blueprint(room_catalog_api(room_catalog, time_series_storage), url_prefix='/api/')

    app.add_url_rule(
        "/person/<name>.html",
        view_func=Person.Details.as_view('person', register_of_persons)
    )
    app.add_url_rule(
        "/person/<name>/configuration.html",
        view_func=Person.Configuration.as_view('person_configuration', register_of_persons, configuration_manager)
    )

    app.register_blueprint(options_blueprint(), url_prefix='/options/')

    def locale_selector():
        return request.accept_languages.best_match(app.config['LANGUAGES'].keys())

    def current_translations():
        return frontend_translations(gettext)

    @app.context_processor
    def utility_processor():
        return dict(lang=locale_selector(), debug=request.args.get('debug'), project_url=Project.url,
                    styx={'translations': current_translations()})

    babel = Babel(app, default_translation_directories="../translations",
                  locale_selector=locale_selector)

    app.config['BOOTSTRAP_SERVE_LOCAL'] = True
    app.config['BOOTSTRAP_BOOTSWATCH_THEME'] = 'united'
    bootstrap = Bootstrap5(app)

    appliance_socket_notifier = ApplianceSocketNotifier(socketio, appliance_service, app)
    room_socket_notifier = RoomSocketNotifier(socketio)
    person_socket_notifier = PersonSocketNotifier(socketio)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    return app
