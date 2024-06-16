import logging
import os
from threading import Thread
from time import sleep

from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

app_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


class MosquittoContainer(DockerContainer):
    def __init__(self, port: int = 1883, **kwargs) -> None:
        super().__init__('eclipse-mosquitto:2', **kwargs)
        self.port = port
        self.with_bind_ports(1883, self.port)
        self.with_volume_mapping(os.path.join(app_directory, 'container', 'mqtt', 'config'), '/mosquitto/config', 'rw')
        self.with_volume_mapping(os.path.join(app_directory, 'container', 'mqtt', 'data'), '/mosquitto/data', 'rw')
        self.with_volume_mapping(os.path.join(app_directory, 'container', 'mqtt', 'log'), '/mosquitto/log', 'rw')
        self.logger_thread = Thread(target=self._poll_log, daemon=True)
        self.logger_thread.start()

    def start(self) -> 'MosquittoContainer':
        super().start()
        wait_for_logs(self, predicate='.*running.*')
        return self

    def get_container_name(self):
        return self.get_wrapped_container().name

    def _poll_log(self):
        while True:
            if self.get_wrapped_container() is not None:
                for line in self.get_wrapped_container().logs(stream=True):
                    logging.getLogger('MosquittoContainer').debug(line)
            sleep(3)
