import json
import logging
import os.path
import random
import re
import shutil
import sys
import uuid
from datetime import datetime, time, timedelta
from pathlib import Path

import paho.mqtt.client as paho_mqtt
from behave import fixture, use_fixture
from behave.model_core import Status
from testcontainers.core.docker_client import DockerClient

from features.clients.CaldavTestClient import CaldavTestClient
from features.container.BehaveAppContainer import BehaveAppContainer
from features.container.InfluxDbContainer import InfluxDbContainerWrapper
from features.container.MosquittoContainer import MosquittoContainer
from features.container.RadicaleCalendarContainer import RadicaleCalendarContainer
from features.container.SeleniumContainer import SeleniumContainer
from features.pages.base import BasePage, VirtualEntityPage, AppliancePage, ApplianceConfigurationPage, RoomPage, \
    RoomConfigurationPage, PersonPage

BROWSER = 'firefox'
save_screenshot_of_failed_steps = True
global_logging = False
app_logging = False
influxdb_logging = False
mqtt_logging = False
calendar_logging = False
BUCKET_NAME = "time_series"
app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
stdout_handler = logging.StreamHandler(sys.stdout)


@fixture
def influxdb_container_setup(context, timeout=20, **kwargs):
    influxdb_container = InfluxDbContainerWrapper(image='influxdb:1.8', test_dir=context.influxdb_test_dir,
                                                  log_container_logs=influxdb_logging,
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
    mqtt_container = MosquittoContainer(test_dir=context.mqtt_test_dir, log_container_logs=mqtt_logging, port=8883)
    context.mqtt_container = mqtt_container
    try:
        mqtt_container.start()
        yield mqtt_container
    finally:
        mqtt_container.stop()


@fixture
def radicale_container_setup(context, timeout=20, **kwargs):
    radicale_container = RadicaleCalendarContainer(context.calendar_test_dir,
                                                   log_container_logs=calendar_logging,
                                                   port=9086)
    context.mqtt_container = radicale_container
    try:
        radicale_container.start()
        context.caldav_client = CaldavTestClient(host='localhost', port=9086, user="billy", password="secret12112")
        yield radicale_container
    finally:
        radicale_container.stop()


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


class Person:
    def __init__(self, caldav_client: CaldavTestClient, name: str):
        self.caldav_client = caldav_client
        self.name = name

    def create_new_appointment(self, person_name, calendar_name, appointment_summary: str):
        start = datetime.combine(datetime.today(), time(hour=random.randint(5, 21)))
        self.caldav_client.create_event(person_name, calendar_name, appointment_summary, start,
                                        start + timedelta(hours=1, minutes=30), 'test event')


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
    context.persons = {
        'Ash': Person(context.caldav_client, 'Ash'),
        'Robin': Person(context.caldav_client, 'Robin'),
        'Billy': Person(context.caldav_client, 'Billy')
    }
    for person_name in context.persons.keys():
        context.caldav_client.create_calendar(person_name, f'{person_name.capitalize()} Private')
        context.caldav_client.create_event(person_name, f'{person_name.capitalize()} Private',
                                           'Skating', datetime.combine(datetime.today(), time(hour=8)),
                                           datetime.combine(datetime.today(), time(hour=9)), 'Have fun and skate 😍')


@fixture
def app_container_setup(context, timeout=30, **kwargs):
    influxdb_container = use_fixture(influxdb_container_setup, context)
    mqtt_container = use_fixture(mqtt_container_setup, context)
    calendar_container = use_fixture(radicale_container_setup, context)
    client = DockerClient()
    behave_app_container = BehaveAppContainer(app_dir, context.behave_test_dir, app_logging, port=8090)
    behave_app_container.configure_influxdb(client.gateway_ip(influxdb_container.get_wrapped_container().id))
    behave_app_container.configure_mqtt(client.gateway_ip(mqtt_container.get_wrapped_container().id))
    behave_app_container.configure_caldav(client.gateway_ip(calendar_container.get_wrapped_container().id))
    try:
        behave_app_container.start()
        yield behave_app_container
    except Exception as e:
        logging.getLogger(__file__).exception(e)
    finally:
        behave_app_container.stop()


@fixture
def browser_setup_and_teardown(context, timeout=30, **kwargs):
    context.webdriver_container = SeleniumContainer(BROWSER)
    context.webdriver_container.start()
    browser = context.webdriver_container.get_driver()
    browser.maximize_window()
    browser.get(context.base_url)
    context.webdriver = browser

    pages = [BasePage(browser, context.base_url, 'home'),
             VirtualEntityPage(browser, context.base_url),
             AppliancePage(browser, context.base_url),
             ApplianceConfigurationPage(browser, context.base_url),
             RoomPage(browser, context.base_url),
             RoomConfigurationPage(browser, context.base_url),
             PersonPage(browser, context.base_url)]
    context.pages = dict([(page.page_name, page) for page in pages])

    yield

    browser.close()
    context.webdriver_container.stop()


def before_all(context):
    logging.basicConfig(encoding='utf-8',
                        level=logging.DEBUG if global_logging else logging.ERROR,
                        format='%(asctime)s - %(name)s(%(lineno)s) - %(levelname)s - %(message)s',
                        handlers=[stdout_handler],
                        force=True)
    logging.getLogger('BehaveAppContainer').setLevel(logging.DEBUG)
    logging.getLogger('InfluxDBContainer').setLevel(logging.DEBUG)
    logging.getLogger('MosquittoContainer').setLevel(logging.DEBUG)
    logging.getLogger('RadicaleContainer').setLevel(logging.DEBUG)
    logging.getLogger('testcontainers.core.container').setLevel(logging.ERROR)
    logging.getLogger('testcontainers.core.waiting_utils').setLevel(logging.ERROR)
    if global_logging:
        _enable_debug_logging()

    screenshots_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'screenshots'))
    if not os.path.exists(screenshots_path):
        os.makedirs(screenshots_path)

    context.run_path = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'runs', str(uuid.uuid4()))))
    applications = {
        'behave': 'container/app',
        'mqtt': 'container/mqtt',
        'influxdb': 'container/influxdb',
        'calendar': 'container/calendar'
    }

    for app_name, app_base in applications.items():
        test_dir = create_test_directory(context.run_path, app_name)
        setattr(context, f'{app_name}_test_dir', test_dir)
        setup_application_data(os.path.join(os.path.dirname(__file__), '..', app_base), test_dir)
        logging.debug(f'Data setup complete for {app_name} in {test_dir}')

    app_container = use_fixture(app_container_setup, context)
    context.base_url = app_container.get_behave_url()
    use_fixture(appliances_setup, context)
    use_fixture(browser_setup_and_teardown, context, timeout=90)


def create_test_directory(base_path, app_name):
    test_dir = base_path / app_name
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir


def setup_application_data(source_path, test_dir):
    for item in os.listdir(source_path):
        s = os.path.join(source_path, item)
        d = os.path.join(test_dir, item)
        if os.path.isdir(s):
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)


def after_all(context):
    run_path = context.run_path
    if run_path is not None and run_path.exists() and run_path.is_dir():
        shutil.rmtree(run_path)
        logging.debug(f"Cleaned up test data at {run_path}")
    else:
        logging.debug(f"No cleanup needed for {run_path}")


def setup_debug_logging(context, timeout=5, **kwargs):
    if not global_logging:
        _enable_debug_logging()


def teardown_debug_logging(context, timeout=5, **kwargs):
    if not global_logging:
        _enable_error_logging()


def _enable_debug_logging():
    stdout_handler.setLevel(logging.DEBUG)


def _enable_error_logging():
    stdout_handler.setLevel(logging.ERROR)


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
            step.filename[step.filename.find('/') + 1:], step.line, re.sub('\\W', '', step.name))
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'screenshots', file_name))
        context.webdriver.save_screenshot(path)
