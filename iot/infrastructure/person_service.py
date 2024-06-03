from typing import List

from iot.core.configuration import IotThingConfig, CaldavConfig
from iot.infrastructure.person import Person
from iot.infrastructure.register_of_persons import RegisterOfPersons
from iot.infrastructure.time.calendar import Calendar


class PersonService:
    def __init__(self, register_of_persons: RegisterOfPersons, config: IotThingConfig):
        self.register_of_persons = register_of_persons
        calendar_sources = filter(lambda source: type(source) is CaldavConfig and
                                                 source.application == "calendar", config.sources.list)
        self.person_name = config.name
        person = Person(self.person_name,
                        list(map(lambda calendar_conf: Calendar(calendar_conf.name, calendar_conf.url,
                                                                calendar_conf.color_hex),
                                 calendar_sources)))
        self.register_of_persons.enlist(person)

    def update_calendars(self, calendars: List[Calendar]):
        person = self.register_of_persons.locate(self.person_name)
        if not calendars:
            return
        unchanged_calendars = list(
            filter(lambda old_cal: old_cal.name not in map(lambda new_cal: new_cal.name, calendars),
                   person.calendars))
        person = person.set_calendars(calendars + unchanged_calendars)
        self.register_of_persons.enlist(person)

    def get_person(self):
        return self.register_of_persons.locate(self.person_name)


def supports_thing_type(thing_type) -> bool:
    return thing_type in ['person']
