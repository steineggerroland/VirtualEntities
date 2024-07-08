import random
import re
from datetime import timedelta, datetime
from typing import Optional

import pytz
from behave import *
from influxdb import InfluxDBClient
from influxdb_client import Point, WritePrecision
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.support.wait import WebDriverWait

use_step_matcher('re')


@given(r'(?>the user goes|they go) to the (?P<page_name>\w+(?> \w+)*) page')
def load_page(context, page_name: str):
    context.webdriver.switch_to.new_window('tab')
    context.pages[page_name].navigate_to()
    context.pages[page_name].is_current_page()


@given(r'(?>the user goes|they go) to the (?P<page_name>\w+(?> \w+)*) page of (?P<entity_name>\w+(?> \w+)*)')
def load_page_for_entity(context, page_name: str, entity_name: str):
    # "the" may be added to entity name because of grammar, thus, remove it
    entity_name = re.sub('^the ', '', entity_name)
    context.entity_name = entity_name
    context.webdriver.switch_to.new_window('tab')
    context.pages[page_name].navigate_to_entity(entity_name)
    context.pages[page_name].is_current_page()


@given(r'(?P<count>\d+) power consumptions are created for the (?P<appliance_name>\w+(?> \w+)*?)(?> '
       r'spread over the last (?>(?>(?P<timeperiod_days>\d+) days)|(?>(?P<timeperiod_hours>\d+) hours)|(?>(?P<timeperiod_seconds>\d+) seconds)))?')
def create_bulk_power_consumptions(context, count: int, appliance_name: str, timeperiod_days: int = 0,
                                   timeperiod_hours: int = 0, timeperiod_seconds: int = 0):
    count, timeperiod_days, timeperiod_hours, timeperiod_seconds = int(count), int(
        timeperiod_days) if timeperiod_days else 0, int(
        timeperiod_hours) if timeperiod_hours else 0, int(timeperiod_seconds) if timeperiod_seconds else 0
    total_seconds = timedelta(days=timeperiod_days, hours=timeperiod_hours, seconds=timeperiod_seconds).total_seconds()
    total_seconds = total_seconds if total_seconds > 0 else 60 * 60
    lines = '\n'.join(Point('power_consumption')
                      .tag('thing', appliance_name)
                      .field('consumption', round(min(2400.0, max(0.0, random.gauss() * i * 2400 / count)), 2))
                      .time(datetime.now().astimezone(pytz.timezone("Europe/Berlin")) -
                            timedelta(seconds=max(0, round(i * total_seconds / count))),
                            WritePrecision.NS)
                      .to_line_protocol(precision=WritePrecision.NS) for i in range(1, count + 1)) + '\n'
    client: InfluxDBClient = context.influxClient
    client.write_points(lines, protocol='line')
    assert len(list(client.query('SELECT * FROM power_consumption WHERE time >= now() - 7200s')
                    .get_points(measurement='power_consumption',
                                tags={'thing': appliance_name}))) > 0


@When(r'the power consumption of the (?P<appliance_name>\w+(?> \w+)*?) is updated(?> to (?P<value>\d+))?')
def send_power_consumption(context, appliance_name: str = None, value: int = None):
    context.new_value = round(random.random() * 2400, 2) if value is None else float(value)
    context.appliances[appliance_name].send_power_consumption_update(context.new_value)


use_step_matcher('parse')


@When('the room climate of the {room_name} is updated')
def send_room_climate(context, room_name: str):
    context.new_value = {'temperature': round(random.random() * 6 + 18, 2),
                         'humidity': round(random.random() * 40 + 50, 2)}
    context.rooms[room_name].send_room_climate_update(context.new_value)


@When('they click on the {entity_name}')
def click_on_name(context, entity_name: str):
    # when navigating to persons, suffix "name" is used due to grammar and has to be removed
    entity_name = entity_name.replace('name ', '')

    def find_and_click(webdriver: WebDriver) -> bool:
        for name_element in webdriver.find_elements(By.CLASS_NAME, 'name'):
            if name_element.text.find(entity_name) >= 0:
                ActionChains(webdriver) \
                    .click(name_element) \
                    .perform()
                return True

    assert WebDriverWait(context.webdriver, 30).until(find_and_click)


@When('they successfully submit the change of the {field_name} to {new_value}')
def submit_change_input(context, field_name, new_value):
    context.execute_steps(f'''
        when they change the {field_name} to {new_value}
        and they submit the form
        then they see a success message
    ''')


@When('they change the {field_name} to {new_value}')
def change_input(context, field_name, new_value):
    input: WebElement = context.webdriver.find_element(By.ID, field_name)
    input.clear()
    input.send_keys(new_value)


@When('they submit the form')
def submit_form(context):
    context.webdriver.find_element(By.CSS_SELECTOR, 'form *[type=submit]').click()


use_step_matcher('re')


@When(
    r'they click the (?P<class_name>\w+(?> \w+)*) button(?> of (?P<entity_type>appliance|room|person) (?P<entity_name>\w+(?> \w+)*))?')
def click_on_button(context, class_name: str, entity_type=None, entity_name=None):
    if entity_type is None:
        parent = context.webdriver.find_element(By.TAG_NAME, 'body')
    else:
        elements_of_entity_type = context.webdriver.find_elements(By.CLASS_NAME, to_class(entity_type))
        parent = (list(filter(lambda entity_element:
                              entity_element.find_element(By.CLASS_NAME, 'name').text == entity_name,
                              elements_of_entity_type))
                  .pop())
    button_matching_class = parent.find_element(By.CSS_SELECTOR, 'button.%s' % to_class(class_name))
    assert button_matching_class is not None
    button_matching_class.click()


use_step_matcher('parse')


@when('a new appointment for calendar {calendar_name} is created')
def step_impl(context, calendar_name: str):
    person_name = context.entity_name
    context.new_value = f'Test event #{random.randint(0, 99999)}'
    context.persons[person_name].create_new_appointment(context.entity_name, calendar_name, context.new_value)


use_step_matcher('re')


@then(r'they are (?>redirected to|on) the (?P<page_name>\w+(?> \w+)*) page(?> of (?P<entity_name>\w+(?> \w+)*))?')
def current_page_is(context, page_name: str, entity_name: str = None):
    if entity_name:
        context.pages[page_name].is_current_page_for_entity(entity_name)
    else:
        context.pages[page_name].is_current_page()


use_step_matcher('parse')


@then('they see rooms in the room catalog')
def rooms_in_catalog(context):
    WebDriverWait(context.webdriver, 30).until(
        lambda d: context.webdriver.find_elements(By.CSS_SELECTOR, '.room-catalog .room'),
        "No room catalog containing rooms")


@then('they see appliances in the appliance depot')
def appliances_in_depot(context):
    WebDriverWait(context.webdriver, 30).until(
        lambda d: context.webdriver.find_elements(By.CSS_SELECTOR, '.appliance-depot .appliance'),
        "No appliance depot containing appliances")


@then('they see person in the register of persons')
def persons_in_register(context):
    WebDriverWait(context.webdriver, 30).until(
        lambda d: context.webdriver.find_elements(By.CSS_SELECTOR, '.register-of-persons .person'),
        "No register of persons containing persons")


@then('they see the rooms {room_names}')
def room_is_shown(context, room_names: str):
    room_names = map(lambda r: r.strip().replace('"', ''), room_names.split(","))
    for room_name in room_names:
        assert any(
            r.find_element(By.CLASS_NAME, 'name').text == room_name for r in context.pages['virtual entities'].rooms())


@then('they see the appliances {appliance_names}')
def appliance_is_shown(context, appliance_names: str):
    appliance_names = map(lambda a: a.strip().replace('"', ''), appliance_names.split(","))
    for appliance_name in appliance_names:
        assert any(a.find_element(By.CLASS_NAME, 'name').text == appliance_name for a in
                   context.pages['virtual entities'].appliances())


@then('they see the persons {person_names}')
def appliance_is_shown(context, person_names: str):
    person_names = map(lambda p: p.strip().replace('"', ''), person_names.split(","))
    for person_name in person_names:
        assert any(p.find_element(By.CLASS_NAME, 'name').text == person_name for p in
                   context.pages['virtual entities'].persons())


use_step_matcher('re')


@then(r'(?>the user sees|they see) the(?> (?P<new>new))? ?(?P<property_name>\w+(?> \w+)*?) of the '
      r'(?P<entity_name>\w+(?> \w+)*?)(?> (?>being (?P<value>(?>\d|\w)+(?> (?>\d|\w)+)*?) )?after a refresh)?')
def property_has_new_value(context, property_name=None, entity_name=None, value=None, new=None):
    entity_type = 'appliance' if any(a == entity_name for a in context.appliances) else \
        'room' if any(r == entity_name for r in context.rooms) else 'person'
    if new is None:
        return property_has_value(context, property_name, entity_name, entity_type)
    property_name_in_class = property_name.replace(' ', '-')
    value = value if value is not None else (
        context.new_value if type(context.new_value) is not dict else context.new_value[
            property_name.replace(' ', '_')])
    WebDriverWait(context.webdriver, 30).until(
        lambda d: _verify_property(d, entity_name, entity_type, f'.{property_name_in_class}', value,
                                   refresh=d))


def property_has_value(context, property_name, entity_name, entity_type):
    property_name_in_class = property_name.replace(' ', '-')
    WebDriverWait(context.webdriver, 30).until(
        lambda d: _verify_property(d, entity_name, entity_type, f'.{property_name_in_class}'))


def _verify_property(d, entity_name, entity_type, property_selector, value=None, refresh=None):
    if refresh is not None:
        refresh.refresh()
    matching_names = 0
    elements_matching_entity_type = d.find_elements(By.CLASS_NAME, entity_type)
    values_not_matching = []
    for entity_element in elements_matching_entity_type:
        if entity_element.find_element(By.CLASS_NAME, 'name').text == entity_name:
            matching_names += 1
            match_found = _find_property_and_match_with(value, entity_element, property_selector, values_not_matching)
            if match_found:
                return True
    _handle_property_of_entity_not_found(elements_matching_entity_type, entity_name, entity_type, matching_names, value,
                                         values_not_matching)
    return False


def _find_property_and_match_with(value, entity_element, property_selector, values_not_matching):
    if value is None:
        return True
    elif type(value) is float:
        return _find_and_compare_float_property(value, entity_element, property_selector,
                                                values_not_matching)
    else:
        return _find_and_compare_property(value, entity_element, property_selector, values_not_matching)


def _find_and_compare_float_property(value, entity_element, property_selector, values_not_matching):
    property_values = list(map(lambda e: e.text,
                               entity_element.find_elements(By.CSS_SELECTOR, property_selector)))
    if not any(
            _extracted_value_matches(extracted_value_with_unit, value) for extracted_value_with_unit in
            property_values):
        values_not_matching.extend(property_values)
        return False
    else:
        return True


def _extracted_value_matches(extracted_value_with_unit, value):
    regex_match = re.search(r'[-+]?[0-9]*\.?[0-9]+', extracted_value_with_unit)
    if regex_match is None:
        return False
    extracted_float = float(regex_match.group(0)) if extracted_value_with_unit.find('?') < 0 else None
    return extracted_float == value


def _find_and_compare_property(value, entity_element, property_selector, values_not_matching):
    property_values = list(map(lambda e: e.text,
                               entity_element.find_elements(By.CSS_SELECTOR, property_selector)))
    if type(value) is str:
        if any(extracted_value.lower().find(value.lower()) >= 0 for extracted_value in property_values):
            return True
        else:
            values_not_matching.extend(property_values)
            return False
    else:
        if any(extracted_value == value for extracted_value in property_values):
            return True
        else:
            values_not_matching.extend(property_values)
            return False


def _handle_property_of_entity_not_found(elements_matching_entity_type, entity_name, entity_type, matching_names, value,
                                         values_not_matching):
    if len(values_not_matching) > 0:
        print(f'None of the found values ({values_not_matching}) matches expected value "{value}" for '
              f'entity {entity_name} ({entity_type})')
    elif len(elements_matching_entity_type) <= 0:
        print(f'Could not find any entity of type {entity_type} with name {entity_name}')
    else:
        print(f'Found {matching_names} entities for {entity_name} ({entity_type}) but no expected value {value}')


@then(r'the main headline contains (?P<some_string>\w+(?> \w+)*)')
def headline_contains(context, some_string):
    return context.webdriver.find_element(By.TAG_NAME, 'h1').text.find(some_string) >= 0


@then(r'(?>the user sees|they see) an icon indicating (?P<entity_type>\w+(?> \w+)*) '
      r'being the type of (?P<entity_category>\w+(?> \w+)*)')
def icon_indicating_entity_type(context, entity_type: str, entity_category: str):
    assert any(icon_element.get_attribute('src').lower().find(entity_type.lower()) for icon_element in
               context.webdriver.find_elements(By.CSS_SELECTOR, '.%s img.icon' % entity_category))


@then(r'(?>the user sees|they see) the (?P<class_name>\w+(?> \w+)*) is (?P<some_string>\w+(?> \w+)*)')
def some_string_in_class_name(context, class_name: str, some_string: str):
    elements = context.webdriver.find_elements(By.CLASS_NAME, class_name)
    assert any(matching_element.text.lower().find(some_string.lower()) >= 0 for matching_element in elements)


@then(r'(?>the user sees|they see) an input for the (?P<field_name>\w+(?> \w+)*) having value (?P<value>\w+(?> \w+)*)')
def input_with_value(context, field_name, value):
    WebDriverWait(context.webdriver, 30).until(
        lambda d: d.find_element(By.ID, field_name).get_attribute('value') == value)


@then(r'(?>the user sees|they see) a (?P<message_type>\w+(?> \w+)*) message')
def message_of_type(context, message_type):
    WebDriverWait(context.webdriver, 30).until(
        presence_of_element_located((By.CSS_SELECTOR, '.messages .message.%s' % message_type)),
        'No message of type "%s" found' % message_type)


@then(r'(?>the user sees|they see) the new appointment after a refresh')
def find_appointment(context):
    summary = context.new_value
    WebDriverWait(context.webdriver, 30).until(lambda d: _find_appointment(d, summary, d))


def _find_appointment(webdriver: WebDriver, summary, refresh=None):
    if refresh is not None:
        refresh.refresh()
    summary_elements = webdriver.find_elements(By.CSS_SELECTOR, '.appointment .summary')
    found_summaries = list(map(lambda e: e.text, summary_elements))
    if not any(s == summary for s in found_summaries):
        print('No appointment with summary "%s" in appointments "%s" found' %
              (summary, str.join(', ', found_summaries)))
        return False
    return True


@then(r'(?>the user sees|they see) (?>a|the) diagram '
      r'with (?>(?P<updated>updated|the previous) )?(?P<property_type>\w+(?> \w+)*) values')
def get_or_verify_diagram_path(context, property_type, updated: str = None):
    values = None
    if updated is not None:
        shall_be_same = updated != 'updated'
        old_value = getattr(context, f'prop_{property_type}')
        values = WebDriverWait(context.webdriver, 30, 5).until(
            lambda d: _compare_diagram_path_for_property(d, property_type, old_value) == shall_be_same)
    values = values if values is not None else WebDriverWait(context.webdriver, 30, 5) \
        .until(lambda d: _get_diagram_path_for_property(d, property_type),
               "Could not retrieve diagram for property %s" % property_type)
    assert values is not None and (type(values) is not str or len(values) > 0)
    setattr(context, f'prop_{property_type}', values)


def _compare_diagram_path_for_property(webdriver, property_type, old_value) -> bool:
    value = _get_diagram_path_for_property(webdriver, property_type)
    print(
        f'Old value "{old_value if old_value is None or type(old_value) is not str or len(old_value) < 30 else old_value[:15] + old_value[-15:]}", '
        f'found value "{value if value is None or type(value) is not str or len(value) < 30 else value[:15] + value[-15:]}"')
    if old_value == value:
        return True
    else:
        return False


def _get_diagram_path_for_property(webdriver, property_type) -> Optional[str]:
    webdriver.refresh()
    try:
        css_selector = '.diagram[data-attribute="%s"] svg > g.data-%s > path' % (
            to_class(property_type), to_class(property_type))
        new_value = webdriver.find_element(By.CSS_SELECTOR, css_selector).get_dom_attribute('d')
        return new_value
    except:
        return None


@then(r'(?>the user sees|they see) the calendar called (?P<calendar_name>\w+(?> \w+)*)')
def find_calendar(context, calendar_name: str):
    context.webdriver.find_elements()
    WebDriverWait(context.webdriver, 30).until(
        lambda d: _verify_property(d, context.entity_name, 'person', '.calendar .name', calendar_name),
        f"No calendar {calendar_name} of person {context.entity_name} found")


def _scroll_and_click_on_element(webdriver, element):
    actions = ActionChains(webdriver)
    actions.click(element)
    actions.perform()


def to_class(name: str) -> str:
    return name.lower().replace(' ', '-')
