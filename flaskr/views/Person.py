import logging
from datetime import datetime, timedelta

import pytz
from dateutil.utils import today
from flask import render_template, redirect, url_for, flash
from flask.views import View, MethodView
from flask_babel import gettext

from flaskr.forms.PersonForm import PersonNameForm
from iot.core.configuration_manager import ConfigurationManager
from iot.infrastructure.person import Person
from iot.infrastructure.register_of_persons import RegisterOfPersons


class Details(View):
    def __init__(self, register_of_persons: RegisterOfPersons):
        self.register_of_persons = register_of_persons

    def dispatch_request(self, name: str):
        person: Person = self.register_of_persons.locate(name)
        if person is not None:
            days_to_appointments = list(map(lambda day: (
                day, person.get_appointments_for(day, timedelta(days=1)),
                datetime.combine(day, datetime.min.time(), pytz.timezone("Europe/Berlin")),
                datetime.combine(day, datetime.max.time(), pytz.timezone("Europe/Berlin"))),
                                            [today(pytz.timezone("Europe/Berlin")) + timedelta(days=offset) for offset
                                             in range(0, 7)]))
            return render_template("person.html", person=person,
                                   days_to_appointments=days_to_appointments)
        else:
            flash(gettext("No person found with name '%(name)s'", name=name), category="danger")
            return redirect(url_for("ve_list"))


class Configuration(MethodView):
    init_every_request = False
    methods = ['GET', 'POST']

    def __init__(self, register_of_persons: RegisterOfPersons, configuration_manager: ConfigurationManager):
        self.register_of_persons = register_of_persons
        self.configuration_manager = configuration_manager
        self.logger = logging.getLogger('Person.Configuration')

    def get(self, name: str):
        person = self.register_of_persons.locate(name)
        if person is None:
            flash(gettext("No person found with that name"), category="danger")
            return redirect(url_for("ve_list"))

        person_form = PersonNameForm()
        person_form.name.default = person.name
        person_form.process()
        return render_template("person_configuration.html", person=person, form=person_form)

    def post(self, name: str):
        person = self.register_of_persons.locate(name)
        if person is None:
            flash(gettext("No person found with that name"), category="danger")
            return redirect(url_for("ve_list"))

        person_form = PersonNameForm()
        if name != person_form.name.data and person_form.validate():
            try:
                self.configuration_manager.rename_person(old_name=name, new_name=person_form.name.data)
                flash(gettext("Person successfully updated"), category="success")
                return redirect(url_for("person_configuration", name=person_form.name.data))
            except Exception as e:
                self.logger.exception(e)
                flash(gettext("Something went wrong"), category="danger")
                return render_template("person_configuration.html", person=person, form=person_form)
        else:
            flash(gettext("Failed to change person, see errors in the form"), category="danger")
            return render_template("person_configuration.html", person=person, form=person_form)
