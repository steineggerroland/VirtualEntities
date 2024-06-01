class DatabaseException(Exception):
    def __init__(self, msg: str | None = None, cause: Exception | None = None):
        self.msg = msg
        self.cause = cause


class InvalidThingType(Exception):
    def __init__(self, thing_type: str = None):
        self.msg = f"thing type '{thing_type}' is unknown"
