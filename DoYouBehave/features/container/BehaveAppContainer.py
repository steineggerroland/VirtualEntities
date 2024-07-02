import logging
import os
import shutil
import urllib.error
import urllib.parse
import urllib.request
from threading import Thread
from time import sleep

from testcontainers.core.container import DockerContainer
from testcontainers.core.container import wait_container_is_ready
from testcontainers.core.docker_client import DockerClient


class BehaveAppContainer(DockerContainer):
    def __init__(self, app_path: str, test_dir: str, app_logging=False, port: int = 8080, **kwargs) -> None:
        super().__init__('python:3.11', **kwargs)
        self.port = port
        self.test_dir = test_dir
        self.with_bind_ports(8080, self.port)
        self.with_command('/bin/sh /behave_runtime/test-data/start.sh')
        self.with_volume_mapping(app_path, '/behave', 'ro')
        shutil.copy(os.path.join(test_dir, 'config', '.default_config.yaml'),
                    os.path.join(test_dir, 'config', 'config.yaml'))
        self.with_volume_mapping(os.path.join(test_dir, 'config'),
                                 '/behave_runtime/test-config', 'rw')
        self.with_volume_mapping(os.path.join(test_dir, 'data'),
                                 '/behave_runtime/test-data', 'rw')
        self.logger_thread = Thread(target=self._poll_log, daemon=True)
        self.app_logging = app_logging

    def start(self) -> 'BehaveAppContainer':
        if self.app_logging:
            self.logger_thread.start()
        super().start()
        self._connect(self.get_container_host_ip(), self.port)
        return self

    def _poll_log(self):
        while True:
            if self.get_wrapped_container() is not None:
                for line in self.get_wrapped_container().logs(stream=True):
                    logging.getLogger('BehaveAppContainer').debug(line)
            sleep(3)

    @wait_container_is_ready(urllib.error.URLError)
    def _connect(self, host: str, port: int) -> None:
        url = urllib.parse.urlunsplit(('http', f'{host}:{port}', '', '', ''))
        urllib.request.urlopen(url, timeout=1)

    def get_behave_url(self):
        client = DockerClient()
        ip = self.get_container_host_ip()
        ip = client.gateway_ip(self.get_wrapped_container().id)
        port = self.port
        return f'http://{ip}:{port}'

    def configure_mqtt(self, mqtt_host):
        self._replace_placeholder(self.test_dir, '$MQTT_HOST$', mqtt_host)

    def configure_influxdb(self, influxdb_host):
        self._replace_placeholder(self.test_dir, '$INFLUXDB_HOST$', influxdb_host)

    def configure_caldav(self, host):
        self._replace_placeholder(self.test_dir, '$CALDAV_HOST$', host)

    @staticmethod
    def _replace_placeholder(test_dir, placeholder, mqtt_host):
        config_file_path = os.path.join(test_dir, 'config', 'config.yaml')
        with open(config_file_path, 'r') as file:
            file_contents = file.read()
        file_contents = file_contents.replace(placeholder, mqtt_host)
        with open(config_file_path, 'w') as file:
            file.write(file_contents)
