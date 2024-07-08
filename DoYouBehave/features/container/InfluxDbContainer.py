import logging
import os
from threading import Thread
from time import sleep
from typing import Optional

from influxdb import InfluxDBClient
from testcontainers.core.waiting_utils import wait_container_is_ready
from testcontainers_python_influxdb.influxdb2 import InfluxDb2Container


class InfluxDbContainerWrapper(InfluxDb2Container):
    def __init__(self, test_dir: str, log_container_logs=False, image: str = "influxdb:latest",
                 container_port: int = 8086, host_port: Optional[int] = None,
                 init_mode: Optional[str] = None,
                 admin_token: Optional[str] = None, username: Optional[str] = None, password: Optional[str] = None,
                 org_name: Optional[str] = None, bucket: Optional[str] = None, retention: Optional[str] = None,
                 **docker_client_kw):
        super().__init__(image, container_port, host_port, init_mode, admin_token, username, password, org_name, bucket,
                         retention, **docker_client_kw)
        path = os.path.join(test_dir, 'scripts')
        self.with_volume_mapping(path, '/docker-entrypoint-initdb.d', 'rw')
        self.log_container_logs = log_container_logs
        self.log_thread = Thread(target=self._poll_log, daemon=True)
        self.client = InfluxDBClient(host='localhost', port=host_port,
                                     username=username, password=password,
                                     database=bucket)
        self.bucket = bucket

    def start(self) -> "InfluxDb2Container":
        if self.log_container_logs:
            self.log_thread.start()
        super().start()
        self._verify_run()
        return self

    def _poll_log(self):
        while True:
            if self.get_wrapped_container() is not None:
                for line in self.get_wrapped_container().logs(stream=True):
                    print(line)
            sleep(3)

    @wait_container_is_ready(AssertionError)
    def _verify_run(self) -> None:
        self.client.create_database(self.bucket)
        databases = self.client.get_list_database()
        assert len(databases) > 1
