from datetime import datetime, timedelta

import pytz
from dateutil.utils import today
from flask import render_template, redirect, url_for, flash
from flask.views import View
from flask_babel import gettext

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
