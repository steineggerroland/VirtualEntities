class RegisterOfPersons:
    def __init__(self):
        self._persons = []

    def enlist(self, person):
        matching_persons = list(filter(lambda p: p.name == person.name, self._persons))
        if matching_persons:
            self._persons.remove(matching_persons[0])
        self._persons.append(person)
        return True
