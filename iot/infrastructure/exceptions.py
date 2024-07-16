class DatabaseException(Exception):
    def __init__(self, msg: str | None = None, cause: Exception | None = None):
        self.msg = msg
        self.cause = cause


class InvalidEntityType(Exception):
    def __init__(self, entity_type: str = None):
        self.msg = f"Entity type '{entity_type}' is unknown"
