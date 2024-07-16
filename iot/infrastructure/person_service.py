from typing import List

from python_event_bus import EventBus

from iot.core.configuration import VirtualEntityConfig, CaldavConfig
from iot.infrastructure.person import Person
from iot.infrastructure.register_of_persons import RegisterOfPersons
from iot.infrastructure.time.calendar import Calendar


class PersonService:
    def __init__(self, register_of_persons: RegisterOfPersons, config: VirtualEntityConfig):
        self.register_of_persons = register_of_persons
        calendar_sources = filter(lambda source: type(source) is CaldavConfig and
                                                 source.application == "calendar", config.sources.list)
        self.person_name = config.name
        person = Person(self.person_name,
                        list(map(lambda calendar_conf: Calendar(calendar_conf.name, calendar_conf.url,
                                                                calendar_conf.color_hex),
                                 calendar_sources)))
        self.register_of_persons.enlist(person)
        EventBus.subscribe("person/changed_config_name", self.change_name, priority=0)

    def update_calendars(self, calendars: List[Calendar]):
        person = self.register_of_persons.locate(self.person_name)
        if not calendars:
            return
        unchanged_calendars = list(
            filter(lambda old_cal: old_cal.name not in map(lambda new_cal: new_cal.name, calendars),
                   person.calendars))
        person = person.set_calendars(calendars + unchanged_calendars)
        self.register_of_persons.enlist(person)

    def change_name(self, name: str, old_name: str):
        if self.person_name == old_name:
            person: Person = self.register_of_persons.locate(old_name)
            person = person.change_name(name)
            self.register_of_persons.dismiss(old_name)
            self.register_of_persons.enlist(person)
            self.person_name = name

    def get_person(self):
        return self.register_of_persons.locate(self.person_name)

def supports_entity_type(entity_type) -> bool:
    return entity_type in ['person']
