import logging
import os.path
import re
import sys

import pytest
from selenium.webdriver.common.by import By
from selenium import webdriver
from testcontainers.core.docker_client import DockerClient
from testcontainers_python_influxdb.influxdb2 import InfluxDb2Container

from test.container.BehaveAppContainer import BehaveAppContainer
from test.container.MosquittoContainer import MosquittoContainer
from test.pages.virtual_entity_page import VirtualEntityPage


class TestWebsite:
    @pytest.fixture(autouse=True)
    def browser_setup_and_teardown(self):
        client = DockerClient()

        influxdb_container = InfluxDb2Container(host_port=8884, username="influx", password="influx",
                                                bucket="time_series")
        mqtt_container = MosquittoContainer(8883)
        app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        behave_app_container = BehaveAppContainer(app_dir, 8086)
        try:
            self.use_selenoid = False  # set to True to run tests with Selenoid

            stdout_handler = logging.StreamHandler(sys.stdout)
            stdout_handler.setLevel(logging.DEBUG)
            logging.basicConfig(encoding='utf-8',
                                level=logging.DEBUG,
                                format='%(asctime)s - %(name)s(%(lineno)s) - %(levelname)s - %(message)s',
                                handlers=[stdout_handler],
                                force=True)
            influxdb_container.start()
            behave_app_container.configure_influxdb(client.gateway_ip(influxdb_container.get_wrapped_container().id))
            mqtt_container.start()
            behave_app_container.configure_mqtt(client.gateway_ip(mqtt_container.get_wrapped_container().id))
            behave_app_container.start()

            self.browser = webdriver.Chrome()

            self.browser.maximize_window()
            self.browser.implicitly_wait(10)

            self.BASE_URL = behave_app_container.get_behave_url()
            self.browser.get(self.BASE_URL)

            yield

            self.browser.close()
            self.browser.quit()
        finally:
            try:
                behave_app_container.stop()
            except:
                pass
            try:
                mqtt_container.stop()
            except:
                pass
            try:
                influxdb_container.stop()
            except:
                pass

    def test_root_redirects_to_virtual_entities(self):
        self.browser.get(self.BASE_URL)
        assert re.compile('.+virtual-entities.*').match(self.browser.current_url)

    def test_overview_shows_virtual_entities(self):
        self.browser.get(VirtualEntityPage.url(self.BASE_URL))
        ve_page = VirtualEntityPage(self.browser)
        assert ve_page.shows_virtual_entities()

    def test_overview_shows_appliances(self):
        self.browser.get(VirtualEntityPage.url(self.BASE_URL))
        ve_page = VirtualEntityPage(self.browser)
        for appliance_name in ['washing-machine', 'dishwasher', 'dryer']:
            assert any(
                appliance_element.find_element(By.CLASS_NAME, 'name').text == appliance_name for appliance_element in
                ve_page.appliances())

    def test_overview_shows_rooms(self):
        self.browser.get(VirtualEntityPage.url(self.BASE_URL))
        ve_page = VirtualEntityPage(self.browser)
        for appliance_name in ['Parents bedroom', 'Kitchen', 'Bathroom', 'Hallway', 'Living room']:
            assert any(
                appliance_element.find_element(By.CLASS_NAME, 'name').text == appliance_name for appliance_element in
                ve_page.rooms())

    def test_overview_shows_persons(self):
        self.browser.get(VirtualEntityPage.url(self.BASE_URL))
        ve_page = VirtualEntityPage(self.browser)
        for appliance_name in ['Robin', 'Ash']:
            assert any(
                appliance_element.find_element(By.CLASS_NAME, 'name').text == appliance_name for appliance_element in
                ve_page.persons())
