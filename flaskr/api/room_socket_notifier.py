import logging

from flask_socketio import SocketIO
from python_event_bus import EventBus

from iot.infrastructure.room_events import RoomEvents, RoomEvent, RoomClimateEvent


class RoomSocketNotifier:
    def __init__(self, socket: SocketIO):
        self.socket: SocketIO = socket
        self.logger = logging.getLogger(self.__class__.__qualname__)

        @socket.on('connect', namespace='/rooms')
        def handle_celebrate():
            self.logger.debug('client connected')

        specific_events = [RoomEvents.CHANGED_CONFIG_NAME, RoomEvents.UPDATED_ROOM_CLIMATE]
        for event in filter(lambda e: e not in specific_events, RoomEvents):
            EventBus.subscribe(event, lambda e: self._room_updated(e))
        EventBus.subscribe(RoomEvents.UPDATED_ROOM_CLIMATE, self._room_climate_updated)

    def _room_updated(self, event: RoomEvent, event_type='updated'):
        self.socket.emit(f'{event.room.name}/{event_type}',
                         {
                             'entity_name': event.room.name,
                             'entity': event.room.to_dict(),
                             'event_type': event_type,
                         },
                         namespace='/rooms')

    def _room_climate_updated(self, event: RoomClimateEvent):
        self.socket.emit(f'{event.room.name}/indoor-climate/updated',
                         {
                             'entity_name': event.room.name,
                             'entity': event.room.to_dict(),
                             'event_type': 'indoor_climate_updated',
                             'measure': event.measurement.to_dict()
                         },
                         namespace='/rooms')
