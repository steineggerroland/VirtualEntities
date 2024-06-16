import logging
import os.path
import sys

from behave import fixture, use_fixture
from selenium import webdriver
from testcontainers.core.docker_client import DockerClient
from testcontainers_python_influxdb.influxdb2 import InfluxDb2Container

from features.container.BehaveAppContainer import BehaveAppContainer
from features.container.MosquittoContainer import MosquittoContainer
from features.pages.virtual_entity_page import VirtualEntityPage


@fixture
def influxdb_container_setup(context, timeout=20, **kwargs):
    influxdb_container = InfluxDb2Container(host_port=8884, username="influx", password="influx",
                                            bucket="time_series")
    try:
        influxdb_container.start()
        yield influxdb_container
    finally:
        influxdb_container.stop()


@fixture
def mqtt_container_setup(context, timeout=20, **kwargs):
    mqtt_container = MosquittoContainer(8883)
    try:
        mqtt_container.start()
        yield mqtt_container
    finally:
        mqtt_container.stop()


@fixture
def app_container_setup(context, timeout=30, **kwargs):
    influxdb_container = use_fixture(influxdb_container_setup, context)
    mqtt_container = use_fixture(mqtt_container_setup, context)
    client = DockerClient()
    app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    behave_app_container = BehaveAppContainer(app_dir, 8086)
    behave_app_container.configure_influxdb(client.gateway_ip(influxdb_container.get_wrapped_container().id))
    behave_app_container.configure_mqtt(client.gateway_ip(mqtt_container.get_wrapped_container().id))
    try:
        behave_app_container.start()
        yield behave_app_container
    finally:
        behave_app_container.stop()


@fixture
def browser_setup_and_teardown(context, timeout=30, **kwargs):
    use_selenoid = False  # set to True to run tests with Selenoid

    browser = webdriver.Chrome()

    browser.maximize_window()
    browser.implicitly_wait(10)

    browser.get(context.base_url)

    context.webdriver = browser
    context.urls = {
        'home': context.base_url,
        'virtual entities': VirtualEntityPage.url(context.base_url)
    }
    yield

    browser.close()
    browser.quit()


def before_all(context):
    app_container = use_fixture(app_container_setup, context)
    context.base_url = app_container.get_behave_url()


def before_scenario(context, scenario):
    use_fixture(browser_setup_and_teardown, context, timeout=90)


def setup_debug_logging(context, timeout=5, **kwargs):
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    logging.basicConfig(encoding='utf-8',
                        level=logging.DEBUG,
                        format='%(asctime)s - %(name)s(%(lineno)s) - %(levelname)s - %(message)s',
                        handlers=[stdout_handler],
                        force=True)
    logging.getLogger('urllib3.connectionpool').setLevel(logging.INFO)


def teardown_debug_logging(context, timeout=5, **kwargs):
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    logging.basicConfig(encoding='utf-8',
                        level=logging.INFO,
                        format='%(asctime)s - %(name)s(%(lineno)s) - %(levelname)s - %(message)s',
                        handlers=[stdout_handler],
                        force=True)
    logging.getLogger('urllib3.connectionpool').setLevel(logging.INFO)


def before_tag(context, tag):
    if tag == "debug":
        use_fixture(setup_debug_logging, context, timeout=10)


def after_tag(context, tag):
    if tag == "debug":
        use_fixture(teardown_debug_logging, context, timeout=10)
