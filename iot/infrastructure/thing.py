from abc import ABCMeta, abstractmethod
from datetime import datetime
from enum import Enum


class OnlineStatus(str, Enum):
    UNKNOWN = 'unknown'
    OFFLINE = 'offline'
    ONLINE = 'online'


class Thing(metaclass=ABCMeta):
    def __init__(self, name: str, last_updated_at: datetime | None = None, last_seen_at: None | datetime = None,
                 online_delta_in_seconds=300):
        self.name = name
        self.last_updated_at = last_updated_at
        self.last_seen_at = last_seen_at
        self._online_delta_in_seconds = online_delta_in_seconds

    def online_status(self):
        if self.last_seen_at is None:
            return OnlineStatus.UNKNOWN
        if (datetime.now() - self.last_seen_at).total_seconds() <= self._online_delta_in_seconds:
            return OnlineStatus.ONLINE
        return OnlineStatus.OFFLINE

    @abstractmethod
    def to_dict(self):
        pass


def _datetime_from_dict_key(dictionary: dict, key: str):
    return datetime.fromisoformat(dictionary[key]) if key in dictionary and dictionary[key] is not None else None
