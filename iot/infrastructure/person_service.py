from typing import List
from threading import RLock

from python_event_bus import EventBus

from iot.core.configuration import VirtualEntityConfig, CaldavConfig
from iot.infrastructure.person import Person
from iot.infrastructure.register_of_persons import RegisterOfPersons
from iot.infrastructure.time.calendar import Calendar


class PersonService:
    def __init__(self, register_of_persons: RegisterOfPersons, config: VirtualEntityConfig):
        self._lock = RLock()
        self._source_errors = set()
        self.register_of_persons = register_of_persons
        calendar_sources = filter(lambda source: isinstance(source, CaldavConfig) and
                                                 source.application == "calendar", config.sources.list)
        self.person_name = config.name
        person = Person(self.person_name,
                        list(map(lambda calendar_conf: Calendar(calendar_conf.name, calendar_conf.url,
                                                                calendar_conf.color_hex),
                                 calendar_sources)))
        self.register_of_persons.enlist(person)
        EventBus.subscribe("person/changed_config_name", self.change_name, priority=0)

    def update_calendars(self, calendars: List[Calendar]):
        if not calendars:
            return
        with self._lock:
            person = self.register_of_persons.locate(self.person_name)
            replacements = {calendar.name: calendar for calendar in calendars}
            merged = [replacements.pop(old.name, old) for old in person.calendars]
            merged.extend(replacements.values())
            self.register_of_persons.enlist(person.set_calendars(merged))
            self._source_errors.difference_update(calendar.name for calendar in calendars)

    def mark_calendar_failed(self, name: str):
        with self._lock:
            self._source_errors.add(name)

    def calendar_snapshot(self):
        """Return one consistent set of immutable-by-convention source objects."""
        with self._lock:
            person = self.register_of_persons.locate(self.person_name)
            return tuple(person.calendars), frozenset(self._source_errors)

    def change_name(self, name: str, old_name: str):
        with self._lock:
            if self.person_name == old_name:
                person = self.register_of_persons.locate(old_name).change_name(name)
                self.register_of_persons.dismiss(old_name)
                self.register_of_persons.enlist(person)
                self.person_name = name

    def get_person(self):
        with self._lock:
            return self.register_of_persons.locate(self.person_name)

def supports_entity_type(entity_type) -> bool:
    return entity_type in ['person']
