import logging
import os
from threading import Thread
from time import sleep

from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs


class MosquittoContainer(DockerContainer):
    def __init__(self, test_dir: str, log_container_logs=False, port: int = 1883, **kwargs) -> None:
        super().__init__('eclipse-mosquitto:2', **kwargs)
        self.port = port
        self.with_bind_ports(1883, self.port)
        self.with_volume_mapping(os.path.join(test_dir, 'config'), '/mosquitto/config', 'ro')
        self.with_volume_mapping(os.path.join(test_dir, 'data'), '/mosquitto/data', 'rw')
        self.with_volume_mapping(os.path.join(test_dir, 'log'), '/mosquitto/log', 'rw')
        self.log_container_logs = log_container_logs
        self.logger_thread = Thread(target=self._poll_log, daemon=True)

    def start(self) -> 'MosquittoContainer':
        if self.log_container_logs:
            self.logger_thread.start()
        super().start()
        wait_for_logs(self, predicate='.*running.*')
        self.exec("chmod -R o+rw /mosquitto") # change access rights to enable deletion after run
        return self

    def _poll_log(self):
        while True:
            if self.get_wrapped_container() is not None:
                for line in self.get_wrapped_container().logs(stream=True):
                    print(line)
            sleep(3)
