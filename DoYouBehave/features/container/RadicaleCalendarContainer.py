import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from threading import Thread
from time import sleep

from testcontainers.core.container import DockerContainer
from testcontainers.core.container import wait_container_is_ready
from testcontainers.core.waiting_utils import wait_for_logs


class RadicaleCalendarContainer(DockerContainer):
    def __init__(self, test_dir: str, log_container_logs=False, port: int = 5232, **kwargs) -> None:
        super().__init__('python:3.11', **kwargs)
        self.port = port
        self.with_bind_ports(5232, self.port)
        self.with_command('/bin/sh /radicale-bin/start.sh')
        script_path = os.path.join(test_dir, 'scripts')
        self.with_volume_mapping(script_path, '/radicale-bin', 'ro')
        script_path = os.path.join(test_dir, 'config')
        self.with_volume_mapping(script_path, '/radicale-config', 'ro')
        self.logger_thread = Thread(target=self._poll_log, daemon=True)
        self.log_container_logs = log_container_logs

    def _poll_log(self):
        while True:
            if self.get_wrapped_container() is not None:
                for line in self.get_wrapped_container().logs(stream=True):
                    logging.getLogger('RadicaleContainer').debug(line)
            sleep(3)

    def start(self) -> 'RadicaleCalendarContainer':
        if self.log_container_logs:
            self.logger_thread.start()
        super().start()
        wait_for_logs(self, '.*Radicale server ready.*', 20)
        self._connect(self.get_container_host_ip(), self.port)
        return self

    @wait_container_is_ready(urllib.error.URLError)
    def _connect(self, host: str, port: int) -> None:
        url = urllib.parse.urlunsplit(('http', f'{host}:{port}', '', '', ''))
        urllib.request.urlopen(url, timeout=1)
