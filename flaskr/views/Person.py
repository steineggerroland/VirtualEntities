import logging
from datetime import date, datetime, timedelta

import pytz
from flask import render_template, redirect, url_for, flash
from flask.views import View, MethodView
from flask_babel import gettext

from flaskr.forms.PersonForm import PersonNameForm
from iot.core.configuration_manager import ConfigurationManager
from iot.infrastructure.person import Person
from iot.infrastructure.register_of_persons import RegisterOfPersons


def preview_days(person: Person, first_day: date, timezone: pytz.BaseTzInfo):
    """Build the seven local calendar days shown on a person's detail page."""
    days = []
    for offset in range(7):
        day = first_day + timedelta(days=offset)
        start = timezone.localize(datetime.combine(day, datetime.min.time()))
        end = timezone.localize(datetime.combine(day + timedelta(days=1), datetime.min.time()))
        days.append((day, person.get_appointments_for(start, timedelta(days=1)), start, end))
    return days


class Details(View):
    def __init__(self, register_of_persons: RegisterOfPersons):
        self.register_of_persons = register_of_persons

    def dispatch_request(self, name: str):
        person: Person = self.register_of_persons.locate(name)
        if person is not None:
            timezone = pytz.timezone("Europe/Berlin")
            days_to_appointments = preview_days(person, datetime.now(timezone).date(), timezone)
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
