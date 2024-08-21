import logging
from socket import SocketIO


class PersonSocketNotifier:
    def __init__(self, socket: SocketIO):
        self.logger = logging.getLogger(self.__class__.__qualname__)

        @socket.on('connect', namespace='/persons')
        def handle_celebrate():
            self.logger.debug('client connected')
