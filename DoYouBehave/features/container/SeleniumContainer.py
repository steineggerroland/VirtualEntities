import logging
from threading import Thread
from time import sleep

import urllib3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_container_is_ready

IMAGES = {
    "firefox": "selenium/standalone-firefox:latest",
    "edge": "selenium/standalone-edge:latest",
    "chrome": "selenium/standalone-chrome:latest"
}


def get_image_name(browser):
    return IMAGES[browser]


def get_options(browser) -> ChromeOptions | EdgeOptions | FirefoxOptions:
    if browser == 'firefox':
        return webdriver.FirefoxOptions()
    elif browser == 'chrome':
        return webdriver.ChromeOptions()
    elif browser == 'edge':
        return webdriver.EdgeOptions()
    else:
        raise TypeError()


class SeleniumContainer(DockerContainer):
    def __init__(self, browser, log_container_logs=False, image=None, **kwargs):
        self.image = image or get_image_name(browser)
        self.options = get_options(browser)

        self.port_to_expose = 4444
        self.vnc_port_to_expose = 4444
        super(SeleniumContainer, self).__init__(image=self.image, shm_size="2g",**kwargs)
        self.with_bind_ports(self.port_to_expose, self.vnc_port_to_expose)
        self.with_bind_ports(7900, 7900)
        if log_container_logs:
            self.logger_thread = Thread(target=self._poll_log, daemon=True)
            self.logger_thread.start()

    @wait_container_is_ready(urllib3.exceptions.HTTPError)
    def _connect(self) -> webdriver.Remote:
        return webdriver.Remote(
            command_executor=self.get_connection_url(),
            options=self.options)

    def get_driver(self) -> webdriver.Remote:
        return self._connect()

    def get_connection_url(self) -> str:
        ip = self.get_container_host_ip()
        port = self.get_exposed_port(self.port_to_expose)
        return f'http://{ip}:{port}'

    def _poll_log(self):
        while True:
            if self.get_wrapped_container() is not None:
                for line in self.get_wrapped_container().logs(stream=True):
                    print(line)
            sleep(3)
