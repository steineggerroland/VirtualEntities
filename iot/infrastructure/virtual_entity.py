from abc import ABCMeta, abstractmethod
from datetime import datetime, timedelta
from enum import Enum

from dateutil.tz import tzlocal


class OnlineStatus(str, Enum):
    UNKNOWN = 'unknown'
    OFFLINE = 'offline'
    ONLINE = 'online'


class BaseVirtualEntity(metaclass=ABCMeta):
    name: str
    entity_type: str
    last_updated_at: datetime
    last_seen_at: datetime

    @abstractmethod
    def online_status(self) -> OnlineStatus:
        pass

    @abstractmethod
    def last_seen_time_delta(self) -> timedelta | None:
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        pass


class VirtualEntity(BaseVirtualEntity):
    def __init__(self, name: str, entity_type: str, last_updated_at: datetime | None = None,
                 last_seen_at: None | datetime = None,
                 online_delta_in_seconds=300):
        self.name = name
        self.entity_type = entity_type
        self.last_updated_at = last_updated_at.astimezone(tzlocal()) if last_updated_at else None
        self.last_seen_at = last_seen_at.astimezone(tzlocal()) if last_seen_at else None
        self._online_delta_in_seconds = online_delta_in_seconds if online_delta_in_seconds else 300

    def online_status(self) -> OnlineStatus:
        if self.last_seen_at is None:
            return OnlineStatus.UNKNOWN
        if (datetime.now(tzlocal()) - self.last_seen_at).total_seconds() <= self._online_delta_in_seconds:
            return OnlineStatus.ONLINE
        return OnlineStatus.OFFLINE

    def last_seen_time_delta(self) -> timedelta | None:
        return self.last_seen_at - datetime.now(tzlocal()) if self.last_seen_at is not None else None

    @abstractmethod
    def to_dict(self):
        pass


def _datetime_from_dict_key(dictionary: dict, key: str):
    return datetime.fromisoformat(dictionary[key]) if key in dictionary and dictionary[key] is not None else None
