from typing import List

from iot.infrastructure.person import Person


class RegisterOfPersons:
    def __init__(self):
        self._persons: List[Person] = []

    def enlist(self, person: Person) -> bool:
        matching_persons = list(filter(lambda p: p.name == person.name, self._persons))
        if matching_persons:
            self._persons.remove(matching_persons[0])
        self._persons.append(person)
        return True

    def dismiss(self, name: str) -> bool:
        matching_persons = list(filter(lambda p: p.name == name, self._persons))
        if matching_persons:
            self._persons.remove(matching_persons[0])
            return True
        return False

    def locate(self, name: str) -> Person | None:
        matching_persons = list(filter(lambda p: p.name == name, self._persons))
        return matching_persons[0] if matching_persons else None

    def catalog_all(self):
        pass
