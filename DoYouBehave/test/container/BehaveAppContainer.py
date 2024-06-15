import logging
import os
import shutil
import urllib.error
import urllib.parse
import urllib.request
from threading import Thread

from testcontainers.core.container import DockerContainer
from testcontainers.core.container import wait_container_is_ready
from testcontainers.core.waiting_utils import wait_for_logs

file_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


class BehaveAppContainer(DockerContainer):
    def __init__(self, app_path: str, port: int = 8080, **kwargs) -> None:
        super().__init__('python:3.11', **kwargs)
        self.port = port
        self.with_bind_ports(8080, self.port)
        self.with_command('/bin/sh /behave/test-data/start.sh')
        self.with_volume_mapping(app_path, '/behave', 'rw')
        shutil.copy(os.path.join(file_dir, 'container', 'app', 'config', '.default_config.yaml'),
                    os.path.join(file_dir, 'container', 'app', 'config', 'config.yaml'))
        self.with_volume_mapping(os.path.join(file_dir, 'container', 'app', 'config'), '/behave/test-config', 'rw')
        self.with_volume_mapping(os.path.join(file_dir, 'container', 'app', 'data'), '/behave/test-data', 'rw')

        self.logger_thread = Thread(target=self._poll_log, daemon=True)
        self.logger_thread.start()

    def start(self) -> 'BehaveAppContainer':
        super().start()

        wait_for_logs(self, '.*Serving Flask app.*')
        self._connect(self.get_container_host_ip(), self.port)

        return self

    def _poll_log(self):
        while True:
            if self.get_wrapped_container() is not None:
                for line in self.get_wrapped_container().logs(stream=True):
                    logging.getLogger('BehaveAppContainer').debug(line)

    @wait_container_is_ready(urllib.error.URLError)
    def _connect(self, host: str, port: int) -> None:
        url = urllib.parse.urlunsplit(('http', f'{host}:{port}', '', '', ''))
        urllib.request.urlopen(url, timeout=1)

    def get_behave_url(self):
        return f'http://{self.get_container_host_ip()}:{self.port}'

    def configure_mqtt(self, mqtt_host):
        self._replace_placeholder('$MQTT_HOST$', mqtt_host)

    def configure_influxdb(self, influxdb_host):
        self._replace_placeholder('$INFLUXDB_HOST$', influxdb_host)

    @staticmethod
    def _replace_placeholder(placeholder, mqtt_host):
        config_file_path = os.path.join(file_dir, 'container', 'app', 'config', 'config.yaml')
        with open(config_file_path, 'r') as file:
            file_contents = file.read()
        file_contents = file_contents.replace(placeholder, mqtt_host)
        with open(config_file_path, 'w') as file:
            file.write(file_contents)
