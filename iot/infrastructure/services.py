from iot.core.configuration import IotThingConfig


class DatabaseException(Exception):
    def __init__(self, msg: str, cause: Exception | None = None):
        self.msg = msg
        self.cause = cause


class InvalidThingType(Exception):
    def __init__(self, thing_config: IotThingConfig):
        self.msg = f"thing type '{thing_config.type}' is unknown"
