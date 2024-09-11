import random
import re
from datetime import timedelta, datetime
from typing import Optional

from behave import *
from dateutil.tz import tzlocal
from influxdb import InfluxDBClient
from influxdb_client import Point, WritePrecision
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.expected_conditions import presence_of_element_located, url_matches, none_of
from selenium.webdriver.support.wait import WebDriverWait

use_step_matcher('re')


@given(r'(?>the user goes|they go) to the (?P<page_name>\w+(?> \w+)*) page')
def load_page(context, page_name: str):
    context.pages[page_name].navigate_to()
    context.pages[page_name].is_current_page()


@given(r'(?>the user goes|they go) to the (?P<page_name>\w+(?> \w+)*) page of (?P<entity_name>\w+(?> \w+)*)')
def load_page_for_entity(context, page_name: str, entity_name: str):
    # "the" may be added to entity name because of grammar, thus, remove it
    entity_name = re.sub('^the ', '', entity_name)
    context.entity_name = entity_name
    context.pages[page_name].navigate_to_entity(entity_name)
    context.pages[page_name].is_current_page_for_entity(entity_name)


@When(r'the power consumption of the (?P<appliance_name>\w+(?> \w+)*?) is updated(?> to (?P<value>\d+))?')
def send_power_consumption(context, appliance_name: str = None, value: int = None):
    setattr(context, f'prop_{to_class("power consumption")}',
            round(random.random() * 2400, 2) if value is None else float(value))
    context.appliances[appliance_name].send_power_consumption_update(
        getattr(context, f'prop_{to_class("power consumption")}'))


@given(r'(?P<count>\d+) power consumptions are created for the (?P<appliance_name>\w+(?> \w+)*?)(?> '
       r'spread over the last (?>(?>(?P<timeperiod_days>\d+) days)|(?>(?P<timeperiod_hours>\d+) hours)|(?>(?P<timeperiod_seconds>\d+) seconds)))?')
def send_bulk_power_consumptions(context, count: int, appliance_name: str, timeperiod_days: int = 0,
                                 timeperiod_hours: int = 0, timeperiod_seconds: int = 0):
    count, timeperiod_days, timeperiod_hours, timeperiod_seconds = int(count), int(
        timeperiod_days) if timeperiod_days else 0, int(
        timeperiod_hours) if timeperiod_hours else 0, int(timeperiod_seconds) if timeperiod_seconds else 0
    total_seconds = timedelta(days=timeperiod_days, hours=timeperiod_hours, seconds=timeperiod_seconds).total_seconds()
    total_seconds = total_seconds if total_seconds > 0 else 60 * 60
    lines = '\n'.join(Point('power_consumption')
                      .tag('thing', appliance_name)
                      .field('consumption', round(min(2400.0, max(0.0, random.gauss() * i * 2400 / count)), 2))
                      .time(datetime.now(tzlocal()) -
                            timedelta(seconds=max(0, round(i * total_seconds / count))),
                            WritePrecision.NS)
                      .to_line_protocol(precision=WritePrecision.NS) for i in range(1, count + 1)) + '\n'
    client: InfluxDBClient = context.influxClient
    client.write_points(lines, protocol='line')
    assert len(list(client.query('SELECT * FROM power_consumption WHERE time >= now() - 7200s')
                    .get_points(measurement='power_consumption',
                                tags={'thing': appliance_name}))) > 0


@When(r'the room climate of the (?P<room_name>\w+(?> \w+)*?) is updated')
def send_room_climate(context, room_name: str):
    context.prop_temperature = round(random.random() * 6 + 18, 2)
    context.prop_humidity = round(random.random() * 40 + 50, 2)
    context.rooms[room_name].send_room_climate_update(
        {'temperature': context.prop_temperature, 'humidity': context.prop_humidity})


@Given(r'(?P<count>\d+) room climate measures are created for the (?P<room_name>\w+(?> \w+)*?)'
       r'(?> spread over the last (?>(?>(?P<timeperiod_days>\d+) days)|(?>(?P<timeperiod_hours>\d+) hours)|'
       r'(?>(?P<timeperiod_seconds>\d+) seconds)))?')
def send_bulk_room_climate(context, count: int, room_name: str, timeperiod_days: int = 0,
                           timeperiod_hours: int = 0, timeperiod_seconds: int = 0):
    count, timeperiod_days, timeperiod_hours, timeperiod_seconds = int(count), int(
        timeperiod_days) if timeperiod_days else 0, int(
        timeperiod_hours) if timeperiod_hours else 0, int(timeperiod_seconds) if timeperiod_seconds else 0
    total_seconds = timedelta(days=timeperiod_days, hours=timeperiod_hours, seconds=timeperiod_seconds).total_seconds()
    total_seconds = total_seconds if total_seconds > 0 else 60 * 60
    lines = '\n'.join(Point('indoor_climate')
                      .tag('thing', room_name)
                      .field('temperature', round(min(30.0, max(15.0, random.gauss() * i * 15 / count) + 15), 2))
                      .field('humidity', round(min(100.0, max(20.0, random.gauss() * i * 80 / count) + 20), 2))
                      .time(datetime.now(tzlocal()) -
                            timedelta(seconds=max(0, round(i * total_seconds / count))),
                            WritePrecision.NS)
                      .to_line_protocol(precision=WritePrecision.NS) for i in range(1, count + 1)) + '\n'
    client: InfluxDBClient = context.influxClient
    client.write_points(lines, protocol='line')
    assert len(list(client.query('SELECT * FROM indoor_climate WHERE time >= now() - 7200s')
                    .get_points(measurement='indoor_climate',
                                tags={'thing': room_name}))) > 0


use_step_matcher('parse')


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
    # rename internal entity too
    if field_name == 'name':
        old_name = input.get_attribute('value')
        entity_type = get_type_for_entity_with_name(context, old_name)
        if entity_type == 'appliance':
            context.appliances[new_value] = old_name
        elif entity_type == 'room':
            context.rooms[new_value] = old_name
        else:
            context.persons[new_value] = old_name
    input.clear()
    input.send_keys(new_value)


@When('they submit the form')
def submit_form(context):
    context.webdriver.find_element(By.CSS_SELECTOR, 'form *[type=submit]').click()


use_step_matcher('re')


@When(r'they click the (?P<class_name>\w+(?> \w+)*?) (?P<clickable_type>button)'
      r'(?> of (?P<entity_type>appliance|room|person) (?P<entity_name>\w+(?> \w+)*))?')
def click_on_something(context, class_name: str, clickable_type: str, entity_type=None, entity_name=None):
    if entity_type is None:
        parent = context.webdriver.find_element(By.TAG_NAME, 'body')
    else:
        elements_of_entity_type = context.webdriver.find_elements(By.CLASS_NAME, to_class(entity_type))
        parent = (list(filter(lambda entity_element:
                              entity_element.find_element(By.CLASS_NAME, 'name').text == entity_name,
                              elements_of_entity_type))
                  .pop())
    button_matching_class = parent.find_element(By.CSS_SELECTOR, '%s.%s' % (clickable_type, to_class(class_name)))
    assert button_matching_class is not None
    button_matching_class.click()


@when(r'they (?P<state>activate|deactivate) (?P<option_name>\w+(?> \w+)*)')
def adapt_switch(context, state, option_name):
    d: WebDriver = context.webdriver
    checkbox = d.find_element(By.CSS_SELECTOR, 'input.%s' % to_class(option_name))
    form = d.find_element(By.CSS_SELECTOR, 'form:has(input.%s)' % to_class(option_name))
    if state == 'activate' and not checkbox.is_selected():
        form.submit()
    elif state == 'deactivate' and checkbox.is_selected():
        form.submit()


use_step_matcher('parse')


@when('a new appointment for calendar {calendar_name} is created')
def step_impl(context, calendar_name: str):
    person_name = context.entity_name
    context.prop_name = f'Test event #{random.randint(0, 99999)}'
    context.persons[person_name].create_new_appointment(context.entity_name, calendar_name,
                                                        context.prop_name)


use_step_matcher('re')


@then(
    r'they are (?>redirected to|on) the (?P<page_name>\w+(?> \w+)*) page(?> of(?> the)? (?P<entity_name>\w+(?> \w+)*))?')
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


@then(r'(?>the user sees|they see) the(?! diagram)(?> (?P<new>new|previous))? ?(?P<property_name>\w+(?> \w+)*?) of the '
      r'(?P<entity_name>\w+(?> \w+)*?)(?> (?>being (?P<value>(?>\d|\w)+(?> (?>\d|\w)+)*?) )?after a refresh)?')
def property_has_new_value(context, property_name=None, entity_name=None, value=None, new=None):
    entity_type = get_type_for_entity_with_name(context, entity_name) if entity_name else None
    if new is None:
        return property_has_value(context, property_name, entity_name, entity_type)
    value = value if value is not None else getattr(context, f'prop_{to_class(property_name)}')
    WebDriverWait(context.webdriver, 30).until(
        lambda d: _verify_property(d, entity_name, entity_type, f'.{to_class(property_name)}', value,
                                   refresh=d))
    setattr(context, f'prop_{to_class(property_name)}', value)


def get_type_for_entity_with_name(context, entity_name):
    entity_type = 'appliance' if any(a == entity_name for a in context.appliances) else \
        'room' if any(r == entity_name for r in context.rooms) else \
            'person' if any(p == entity_name for p in context.persons) else None
    if entity_type is None:
        raise AttributeError('%s is not a known entity' % entity_name)
    return entity_type


def property_has_value(context, property_name, entity_name, entity_type):
    value = WebDriverWait(context.webdriver, 30).until(
        lambda d: _verify_property(d, entity_name, entity_type, f'.{to_class(property_name)}'))
    setattr(context, f'prop_{to_class(property_name)}', value)


def _verify_property(d, entity_name, entity_type, property_selector, value=None, refresh=None):
    if refresh is not None:
        refresh.refresh()
    values_not_matching = []
    try:
        elements_for_entity_with_name = _find_element_for_entity_with_name(d, entity_type, entity_name)
    except AssertionError as e:
        print(e)
        return None
    for e in elements_for_entity_with_name:
        found_value = _find_property_and_match_with(value, e, property_selector, values_not_matching)
        if found_value is not None:
            return found_value
    if len(values_not_matching) > 0:
        print(f'None of the found values ({values_not_matching}) matches expected value "{value}" for '
              f'entity {entity_name} ({entity_type})')
    else:
        print(f'Found {len(elements_for_entity_with_name)} entities for {entity_name} ({entity_type})'
              f' but no values for property {property_selector}')
    return None


def _find_element_for_entity_with_name(webdriver, entity_type: str, entity_name: str):
    elements_for_entity_type = webdriver.find_elements(By.CLASS_NAME, entity_type)
    found_elements = list(filter(lambda element: element.find_element(By.CLASS_NAME, 'name').text == entity_name,
                                 elements_for_entity_type))
    if len(elements_for_entity_type) == 0:
        raise AssertionError('There are no elements of type %s' % entity_type)
    if len(found_elements) == 0:
        raise AssertionError('There are no elements of type %s with name %s' % (entity_type, entity_name))
    return found_elements


def _find_property_and_match_with(value, entity_element, property_selector, values_not_matching):
    if value is None:
        if any(entity_element.find_elements(By.CSS_SELECTOR, property_selector)):
            return entity_element.find_elements(By.CSS_SELECTOR, property_selector)[0].text
        else:
            return None
    elif type(value) is float:
        if _find_and_compare_float_property(value, entity_element, property_selector,
                                            values_not_matching):
            return value
        else:
            return None
    else:
        if _find_and_compare_property(value, entity_element, property_selector, values_not_matching):
            return value
        else:
            return None


def _find_and_compare_float_property(value, entity_element, property_selector, values_not_matching):
    property_values = list(map(lambda e: e.text,
                               entity_element.find_elements(By.CSS_SELECTOR, property_selector)))
    if not any(
            _extracted_value_matches(extracted_value_with_unit, value) for extracted_value_with_unit in
            property_values):
        values_not_matching.extend(property_values)
        return None
    else:
        return value


def _extracted_value_matches(extracted_value_with_unit, value):
    regex_match = re.search(r'[-+]?[0-9]*\.?[0-9]+', extracted_value_with_unit)
    if regex_match is None:
        return None
    extracted_float = float(regex_match.group(0)) if extracted_value_with_unit.find('?') < 0 else None
    if abs((extracted_float / value) - 1) < 0.01:
        return value
    if re.search(r'[-+]?[0-9]*\.?[0-9]+k\w*', extracted_value_with_unit) is not None:
        extracted_float *= 1000
        if abs((extracted_float / value) - 1) < 0.05:
            return value
    return None


def _find_and_compare_property(value, entity_element, property_selector, values_not_matching):
    property_values = list(map(lambda e: e.text,
                               entity_element.find_elements(By.CSS_SELECTOR, property_selector)))
    if type(value) is str:
        if any(extracted_value.lower().find(value.lower()) >= 0 for extracted_value in property_values):
            return value
        else:
            values_not_matching.extend(property_values)
            return None
    else:
        if any(extracted_value == value for extracted_value in property_values):
            return value
        else:
            values_not_matching.extend(property_values)
            return None


@then(r'the main headline contains (?P<some_string>\w+(?> \w+)*)')
def headline_contains(context, some_string):
    return context.webdriver.find_element(By.TAG_NAME, 'h1').text.find(some_string) >= 0


@then(r'(?P<may_contain_not>.*see[s]?) an icon indicating (?P<entity_type>\w+(?> \w+)*) '
      r'being the type of (?P<entity_category>\w+(?> \w+)*)')
def icon_indicating_entity_type(context, may_contain_not: str, entity_type: str, entity_category: str):
    negate = may_contain_not.find('not') >= 0 or may_contain_not.find('n\'t') >= 0
    assert not negate == any(icon_element.get_attribute('src').lower().find(entity_type.lower()) for icon_element in
                             context.webdriver.find_elements(By.CSS_SELECTOR, '.%s img.icon' % entity_category))


@then(r'(?P<may_contain_not>.*see[s]?) the (?P<class_name>\w+(?> \w+)*?) (?P<clickable_type>button)'
      r'(?> of (?P<entity_type>appliance|room|person) (?P<entity_name>\w+(?> \w+)*))?')
def contains_button_with_class(context, may_contain_not: str, class_name: str, clickable_type: str, entity_type: str,
                               entity_name: str):
    negate = may_contain_not.find('not') >= 0 or may_contain_not.find('n\'t') >= 0

    def any_clickable_element_exists(webdriver: WebDriver):
        if entity_type is None:
            parent = webdriver.find_element(By.TAG_NAME, 'body')
        else:
            elements_of_entity_type = webdriver.find_elements(By.CLASS_NAME, to_class(entity_type))
            parent = (list(filter(lambda entity_element:
                                  entity_element.find_element(By.CLASS_NAME, 'name').text == entity_name,
                                  elements_of_entity_type))
                      .pop())

        return any(parent.find_elements(By.CSS_SELECTOR, '%s.%s' % (clickable_type, to_class(class_name))))

    if negate:
        WebDriverWait(context.webdriver, 30).until(none_of(any_clickable_element_exists),
                                                   "No clickable element with selector '%s' expected." % (
                                                           '%s.%s' % (clickable_type, to_class(class_name))))
    else:
        WebDriverWait(context.webdriver, 30).until(any_clickable_element_exists,
                                                   "Clickable element with selector '%s' expected." % (
                                                           '%s.%s' % (clickable_type, to_class(class_name))))


@then(r'(?>the user sees|they see) the (?P<class_name>\w+(?> \w+)*) is (?P<some_string>\w+(?> \w+)*)')
def some_string_in_class_name(context, class_name: str, some_string: str):
    WebDriverWait(context.webdriver, 30).until(
        lambda d: any(matching_element.text.lower().find(some_string.lower()) >= 0 for matching_element in
                      d.find_elements(By.CLASS_NAME, to_class(class_name))))


@then(r'(?>the user sees|they see) an input for the (?P<field_name>\w+(?> \w+)*) having value (?P<value>\w+(?> \w+)*)')
def input_with_value(context, field_name, value):
    WebDriverWait(context.webdriver, 30).until(
        lambda d: d.find_element(By.ID, field_name).get_attribute('value') == value)


@then(r'(?>the user sees|they see) a (?P<message_type>\w+(?> \w+)*) message')
def message_of_type(context, message_type):
    WebDriverWait(context.webdriver, 30).until(presence_of_element_located(
        (By.CSS_SELECTOR, '.messages .message.%s' % message_type)),
        'No message of type "%s" found' % message_type)


@then(r'(?>the user sees|they see) the new appointment after a refresh')
def find_appointment(context):
    summary = context.prop_name
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
      r'with (?>(?P<updated>updated|the previous) )*(?P<property_type>\w+(?> \w+)*) values'
      r'(?> (?>for|of)(?> the)? (?P<entity_name>\w+(?> \w+)*))?')
def get_or_verify_diagram_path(context, property_type, updated: str = None, entity_name: str = None):
    if entity_name is not None:
        entity_type = get_type_for_entity_with_name(context, entity_name)
    else:
        entity_type = None
    values = None
    if updated is not None:
        shall_be_same = updated != 'updated'
        old_value = getattr(context, f'prop_diagram_{property_type}')
        values = WebDriverWait(context.webdriver, 30, 5).until(
            lambda d: _compare_diagram_path_for_property(d, property_type, old_value,
                                                         entity_type, entity_name) == shall_be_same)
    values = values if values is not None else WebDriverWait(context.webdriver, 30, 5) \
        .until(lambda d: _get_diagram_path_for_property(d, property_type, entity_type, entity_name),
               "Could not retrieve diagram for property %s" % property_type)
    assert values is not None and (type(values) is not str or len(values) > 0)
    setattr(context, f'prop_diagram_{property_type}', values)


def _compare_diagram_path_for_property(webdriver, property_type, old_value, entity_type: str = None,
                                       entity_name: str = None) -> bool:
    value = _get_diagram_path_for_property(webdriver, property_type, entity_type, entity_name)
    print(f'Old value "{old_value}", found value "{value}"')
    if value is not None and type(value) is str and len(value) > 100:  # long texts shall be compared more fuzzy
        suffix_to_compare_length = round(len(value) * 2.0 / 3.0)
        offset = round(len(value) / 6.0)
        if (len(old_value) / len(value)) >= 0.9:  # verify that the length of the two values have a quite similar length
            return value.find(old_value[offset:offset + suffix_to_compare_length]) >= 0
        else:  # the old value is much shorter than the new value
            return False
    if old_value == value:
        return True
    else:
        return False


def _get_diagram_path_for_property(webdriver, property_type, entity_type: str = None, entity_name: str = None) -> \
        Optional[str]:
    webdriver.refresh()
    try:
        if entity_name is None:
            container = webdriver
        else:
            try:
                matching_elements_of_entity = _find_element_for_entity_with_name(webdriver, entity_type, entity_name)
                if len(matching_elements_of_entity) > 1:
                    print('There are more elements matching the entity, but only one is compared.')
                container = matching_elements_of_entity[0]
            except AssertionError as e:
                print(e)
                return None
        css_selector = '.diagram.%s' % to_class(property_type)
        new_value = container.find_element(By.CSS_SELECTOR, css_selector).get_dom_attribute('data-displayed-measures')
        return new_value
    except:
        return None


@then(r'(?>the user sees|they see) the calendar called (?P<calendar_name>\w+(?> \w+)*)')
def find_calendar(context, calendar_name: str):
    context.webdriver.find_elements()
    WebDriverWait(context.webdriver, 30).until(
        lambda d: _verify_property(d, context.entity_name, 'person', '.calendar .name', calendar_name),
        f"No calendar {calendar_name} of person {context.entity_name} found")


@then(r'the (?P<option_name>\w+(?> \w+)*) (?>is|are)'
      r'(?>(?> still)? (?P<state>active|inactive)| set to (?P<value>\w+(?> \w+)*))')
def verify_option_in_url(context, option_name, state=None, value=None):
    if option_name == 'dark mode':
        html: WebElement = context.webdriver.find_element(By.TAG_NAME, 'html')
        assert html.get_attribute('data-bs-theme') == 'dark' if state == 'active' else None

    elif option_name == 'fullscreen mode':
        html: WebElement = context.webdriver.find_element(By.TAG_NAME, 'html')
        assert (html.get_attribute('class').find('fullscreen') < 0) == (state == 'active')

    matcher = r'.*(\?|&)%s=%s(&.*)?' % (to_url_param(option_name),
                                        'on' if state == 'active' else 'false' if state == 'inactive' else value)
    WebDriverWait(context.webdriver, 10).until(url_matches(matcher),
                                               "The option %s is not %s, the url looks as follows: %s" % (
                                                   option_name, state if state is not None else value,
                                                   context.webdriver.current_url))


def _scroll_and_click_on_element(webdriver, element):
    actions = ActionChains(webdriver)
    actions.click(element)
    actions.perform()


def to_class(name: str) -> str:
    return name.lower().replace(' ', '-')


def to_url_param(name: str) -> str:
    return name.lower().replace(' ', '_')
