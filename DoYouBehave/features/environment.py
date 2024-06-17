import json
import logging
import os.path
import sys

import paho.mqtt.client as paho_mqtt
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
    context.influxdb_container = influxdb_container
    try:
        influxdb_container.start()
        yield influxdb_container
    finally:
        influxdb_container.stop()


@fixture
def mqtt_container_setup(context, timeout=20, **kwargs):
    mqtt_container = MosquittoContainer(8883)
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
    use_fixture(appliances_setup, context)


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
