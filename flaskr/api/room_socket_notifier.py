from flask_socketio import SocketIO
from python_event_bus import EventBus

from iot.infrastructure.room_events import RoomEvents, RoomEvent, RoomClimateEvent


class RoomSocketNotifier:
    def __init__(self, socket: SocketIO):
        self.socket = socket

        specific_events = [RoomEvents.CHANGED_CONFIG_NAME, RoomEvents.UPDATED_ROOM_CLIMATE]
        for event in filter(lambda e: e not in specific_events , RoomEvents):
            EventBus.subscribe(event, self._room_updated)
        EventBus.subscribe(RoomEvents.UPDATED_ROOM_CLIMATE, self._room_climate_updated)

    def _room_updated(self, event: RoomEvent):
        self.socket.emit(f'rooms/{event.room.name}/updated', {'room': event.room.to_dict()})

    def _room_climate_updated(self, event: RoomClimateEvent):
        self.socket.emit(f'rooms/{event.room.name}/indor-climate/updated',
                         {'room': event.room.to_dict(), 'measure': event.measurement.to_dict()})
