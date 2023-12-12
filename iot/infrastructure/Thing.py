from abc import ABCMeta, abstractmethod
from datetime import datetime


class Thing(metaclass=ABCMeta):
    def __init__(self, name: str, last_updated_at: datetime | None = None, last_seen_at: None | datetime = None):
        self.last_seen_at = last_seen_at
        self.name = name
        self.last_updated_at = last_updated_at

    @abstractmethod
    def to_dict(self):
        pass
