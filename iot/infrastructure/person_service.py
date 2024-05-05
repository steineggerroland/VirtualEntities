from iot.core.configuration import IotThingConfig, UrlConf
from iot.core.storage import Storage
from iot.infrastructure.person import Person
from iot.infrastructure.time.calendar import Calendar


class PersonService:
    def __init__(self, storage: Storage, config: IotThingConfig):
        self.storage = storage
        calendar_sources = filter(lambda source: type(source) is UrlConf and
                                                 source.application == "calendar", config.sources.list)
        self.person = Person(config.name,
                             list(map(lambda calendar_conf: Calendar(calendar_conf.url), calendar_sources)))


def supports_thing_type(thing_type) -> bool:
    return thing_type in ['person']
