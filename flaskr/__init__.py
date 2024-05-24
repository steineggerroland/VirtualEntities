import os

import yamlenv
from flask import Flask, request
from flask_babel import Babel

from flaskr.views import VirtualEntities


def create_app(default_config_file_name: str, config: dict = None):
    app = Flask(__name__)

    app.config.from_file(default_config_file_name, load=yamlenv.load)
    app.config.from_mapping(config)

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
