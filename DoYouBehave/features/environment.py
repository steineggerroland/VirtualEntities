import json
import logging
import os.path
import re
import sys

import paho.mqtt.client as paho_mqtt
from behave import fixture, use_fixture
from behave.model_core import Status
from selenium import webdriver
from testcontainers.core.docker_client import DockerClient

from features.container.BehaveAppContainer import BehaveAppContainer
from features.container.InfluxDbContainer import InfluxDbContainerWrapper
from features.container.MosquittoContainer import MosquittoContainer
from features.pages.base import BasePage, VirtualEntityPage, AppliancePage, ApplianceConfigurationPage, RoomPage

save_screenshot_of_failed_steps = True
global_logging = False
app_logging = False
influxdb_logging = False
mqtt_logging = False
BUCKET_NAME = "time_series"
app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
stdout_handler = logging.StreamHandler(sys.stdout)


@fixture
def influxdb_container_setup(context, timeout=20, **kwargs):
    influxdb_container = InfluxDbContainerWrapper(image='influxdb:1.8', app_dir=app_dir, log_container_logs=influxdb_logging,
                                                  host_port=8884, username="influxdb", password="influxdb",
                                                  bucket=BUCKET_NAME, org_name='behave', init_mode='setup')
    context.influxdb_container = influxdb_container
    try:
        influxdb_container.start()
        yield influxdb_container
    except Exception as e:
        logging.getLogger(__file__).exception(e)
    finally:
        influxdb_container.stop()


@fixture
def mqtt_container_setup(context, timeout=20, **kwargs):
    mqtt_container = MosquittoContainer(log_container_logs=mqtt_logging, port=8883)
    context.mqtt_container = mqtt_container
    try:
        mqtt_container.start()
        yield mqtt_container
    finally:
        mqtt_container.stop()


class Appliance:
    def __init__(self, mqtt_client: paho_mqtt.Client, name: str, pc_topic=None, load_topic=None, unload_topic=None):
        self.mqtt_client = mqtt_client
        self.name = name
        self.power_consumption_topic = pc_topic
        self.load_topic = load_topic
        self.unload_topic = unload_topic

    def send_power_consumption_update(self, new_watt: float):
        self.mqtt_client.publish(self.power_consumption_topic, new_watt)


class Room:
    def __init__(self, mqtt_client: paho_mqtt.Client, name: str, rc_topic, t_topic=None, h_topic=None):
        self.mqtt_client = mqtt_client
        self.name = name
        self.room_climate_topic = rc_topic
        self.temperature_topic = t_topic
        self.humidity_topic = h_topic

    def send_room_climate_update(self, new_values: dict):
        self.mqtt_client.publish(self.room_climate_topic, json.dumps(new_values))


@fixture
def appliances_setup(context, timeout=10, **kwargs):
    client = DockerClient()
    mqtt_client = paho_mqtt.Client(client_id='selenium-test-client')
    mqtt_client.username_pw_set('mqtt', 'mqtt')
    mqtt_client.connect(client.gateway_ip(context.mqtt_container.get_wrapped_container().id), 8883)
    context.appliances = {
        'Washing machine': Appliance(mqtt_client, 'Washing machine',
                                     'measurements/home/indoor/washing_machine/power/power',
                                     'home/things/washing_machine/load', 'home/things/washing_machine/unload'),
        'Dishwasher': Appliance(mqtt_client, 'Dishwasher',
                                'measurements/home/indoor/dishwasher/power', 'home/things/dishwasher/load',
                                'home/things/dishwasher/unload'),
        'Dryer': Appliance(mqtt_client, 'Dryer',
                           'zigbee/home/indoor/dryer', 'home/things/dryer/load', 'home/things/dryer/unload')
    }
    context.rooms = {
        'Kitchen': Room(mqtt_client, 'Kitchen', 'zigbee/home/kitchen/sensor01'),
        'Living room': Room(mqtt_client, 'Living room', 'zigbee/home/living-room/sensor01'),
        'Terrace': Room(mqtt_client, 'Terrace', 'zigbee/home/terrace/sensor01'),
        'Bathroom': Room(mqtt_client, 'Bathroom', 'zigbee/home/bathroom/sensor01'),
        'Hallway': Room(mqtt_client, 'Hallway', 'zigbee/home/hallway/sensor01'),
        'Parents bedroom': Room(mqtt_client, 'Parents bedroom', 'zigbee/home/parents-bedroom/sensor01')
    }


@fixture
def app_container_setup(context, timeout=30, **kwargs):
    influxdb_container = use_fixture(influxdb_container_setup, context)
    mqtt_container = use_fixture(mqtt_container_setup, context)
    client = DockerClient()
    behave_app_container = BehaveAppContainer(app_dir, app_logging, port=8090)
    behave_app_container.configure_influxdb(client.gateway_ip(influxdb_container.get_wrapped_container().id))
    behave_app_container.configure_mqtt(client.gateway_ip(mqtt_container.get_wrapped_container().id))
    try:
        behave_app_container.start()
        yield behave_app_container
    except Exception as e:
        logging.getLogger(__file__).exception(e)
    finally:
        behave_app_container.stop()


@fixture
def browser_setup_and_teardown(context, timeout=30, **kwargs):
    use_selenoid = False  # set to True to run tests with Selenoid
    browser = webdriver.Chrome()
    browser.maximize_window()
    browser.get(context.base_url)
    context.webdriver = browser

    pages = [BasePage(browser, context.base_url, 'home'), VirtualEntityPage(browser, context.base_url),
             AppliancePage(browser, context.base_url), ApplianceConfigurationPage(browser, context.base_url),
             RoomPage(browser, context.base_url)]
    context.pages = dict([(page.page_name, page) for page in pages])

    yield

    browser.close()
    browser.quit()


def before_all(context):
    logging.basicConfig(encoding='utf-8',
                        level=logging.DEBUG if global_logging else logging.ERROR,
                        format='%(asctime)s - %(name)s(%(lineno)s) - %(levelname)s - %(message)s',
                        handlers=[stdout_handler],
                        force=True)
    logging.getLogger('BehaveAppContainer').setLevel(logging.DEBUG)
    logging.getLogger('InfluxDBContainer').setLevel(logging.DEBUG)
    logging.getLogger('MosquittoContainer').setLevel(logging.DEBUG)
    if global_logging:
        _enable_debug_logging()
    app_container = use_fixture(app_container_setup, context)
    context.base_url = app_container.get_behave_url()
    use_fixture(appliances_setup, context)

    screenshots_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'screenshots'))
    if not os.path.exists(screenshots_path):
        os.makedirs(screenshots_path)


def before_scenario(context, scenario):
    use_fixture(browser_setup_and_teardown, context, timeout=90)


def setup_debug_logging(context, timeout=5, **kwargs):
    if not global_logging:
        _enable_debug_logging()


def teardown_debug_logging(context, timeout=5, **kwargs):
    if not global_logging:
        _enable_info_logging()


def _enable_debug_logging():
    stdout_handler.setLevel(logging.DEBUG)


def _enable_info_logging():
    stdout_handler.setLevel(logging.INFO)


def before_tag(context, tag):
    if tag == "debug":
        use_fixture(setup_debug_logging, context, timeout=10)


def after_tag(context, tag):
    if tag == "debug":
        use_fixture(teardown_debug_logging, context, timeout=10)


def after_step(context, step):
    """Save screenshots of failed steps"""
    if save_screenshot_of_failed_steps and step.status is Status.failed:
        file_name = "fail.%s_%s_%s.png" % (
            step.filename[step.filename.find('/') + 1:], step.line, re.sub('\W', '', step.name))
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'screenshots', file_name))
        context.webdriver.save_screenshot(path)
