import random
import re
from typing import Optional

from behave import *
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.support.wait import WebDriverWait


@given('the user goes to the {page_name} page')
def load_page(context, page_name: str):
    context.pages[page_name].navigate_to()
    context.pages[page_name].is_current_page()


@given('the user goes to the {page_name} page of {entity_name}')
def load_page(context, page_name: str, entity_name: str):
    # "the" may be added to entity name because of grammar, thus, remove it
    entity_name = entity_name.replace('the ', '')
    context.entity_name = entity_name
    context.pages[page_name].navigate_to_entity(entity_name)
    context.pages[page_name].is_current_page()


@When('the power consumption of the {appliance_name} is updated')
def send_power_consumption(context, appliance_name: str):
    context.new_value = round(random.random() * 2400, 2)
    context.appliances[appliance_name].send_power_consumption_update(context.new_value)


@When('the room climate of the {room_name} is updated')
def send_room_climate(context, room_name: str):
    context.new_value = {'temperature': round(random.random() * 6 + 18, 2),
                         'humidity': round(random.random() * 40 + 50, 2)}
    context.rooms[room_name].send_room_climate_update(context.new_value)


@When('they click on the {entity_name}')
def click_on_name(context, entity_name: str):
    clicked = False
    for name_element in context.webdriver.find_elements(By.CLASS_NAME, 'name'):
        if name_element.text.find(entity_name) >= 0:
            name_element.click()
            clicked = True
            break
    assert clicked


@When('they change the {field_name} to {new_value}')
def change_input(context, field_name, new_value):
    input: WebElement = context.webdriver.find_element(By.ID, field_name)
    input.clear()
    input.send_keys(new_value)


@When('they submit the form')
def submit_form(context):
    context.webdriver.find_element(By.CSS_SELECTOR, 'form *[type=submit]').click()


@When('they click the {class_name} button')
def click_on_button(context, class_name: str):
    clicked = False
    buttons_matching_class = context.webdriver.find_elements(By.CSS_SELECTOR,
                                                             'button.%s' % class_name.lower().replace(' ', '-'))
    for matching_element in buttons_matching_class:
        matching_element.click()
        clicked = True
        break
    assert clicked


@then('they are {redirect_or_on} the {page_name} page')
def current_page_is(context, redirect_or_on, page_name: str):
    context.pages[page_name].is_current_page()


@then('they see rooms in the room catalog')
def rooms_in_catalog(context):
    WebDriverWait(context.webdriver, 10).until(
        lambda d: context.webdriver.find_elements(By.CSS_SELECTOR, '.room-catalog .room'),
        "No room catalog containing rooms")


@then('they see appliances in the appliance depot')
def appliances_in_depot(context):
    WebDriverWait(context.webdriver, 10).until(
        lambda d: context.webdriver.find_elements(By.CSS_SELECTOR, '.appliance-depot .appliance'),
        "No appliance depot containing appliances")


@then('they see person in the register of persons')
def persons_in_register(context):
    WebDriverWait(context.webdriver, 10).until(
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


@then('the user sees the new {property_name} for the {entity_name} after a refresh')
def property_has_new_value(context, property_name, entity_name):
    entity_type = 'appliance' if property_name in ['power consumption'] else 'room'
    property_name_in_class = property_name.replace(' ', '-')
    new_value = context.new_value if type(context.new_value) is not dict else context.new_value[
        property_name.replace(' ', '_')]
    WebDriverWait(context.webdriver, 10).until(
        lambda d: _verify_property(d, entity_name, entity_type, f'.{property_name_in_class}', new_value,
                                   refresh=context.webdriver),
        f"No property {property_name} of entity {entity_name} with value {new_value} found")


@then('the user sees the {property_name} for the {entity_name}')
def property_has_new_value(context, property_name, entity_name):
    entity_type = 'appliance' if property_name in ['power consumption'] else 'room'
    property_name_in_class = property_name.replace(' ', '-')
    WebDriverWait(context.webdriver, 10).until(
        lambda d: _verify_property(d, entity_name, entity_type, f'.{property_name_in_class}'),
        f"No property {property_name} of entity {entity_name} found")


def _verify_property(d, entity_name, entity_type, property_selector, value=None, refresh=None):
    if refresh is not None:
        refresh.refresh()
    for entity_element in d.find_elements(By.CLASS_NAME, entity_type):
        if entity_element.find_element(By.CLASS_NAME, 'name').text == entity_name:
            value_with_unit = entity_element.find_element(By.CSS_SELECTOR, property_selector).text
            extracted_float = float(
                re.search(r'[-+]?[0-9]*\.?[0-9]+', value_with_unit).group(0)) if value_with_unit.find(
                '?') < 0 else None
            return extracted_float == float(value) if value is not None else True
    return False


@then('the main headline contains {some_string}')
def headline_contains(context, some_string):
    return context.webdriver.find_element(By.TAG_NAME, 'h1').text.find(some_string) >= 0


@then('they see an icon indicating {entity_type} being the type of {entity_category}')
def icon_indicating_entity_type(context, entity_type: str, entity_category: str):
    assert any(icon_element.get_attribute('src').lower().find(entity_type.lower()) for icon_element in
               context.webdriver.find_elements(By.CSS_SELECTOR, '.%s img.icon' % entity_category))


@then('they see the {class_name} is {some_string}')
def some_string_in_class_name(context, class_name: str, some_string: str):
    elements = context.webdriver.find_elements(By.CLASS_NAME, class_name)
    assert any(matching_element.text.lower().find(some_string.lower()) >= 0 for matching_element in elements)


@then('they see an input for the {field_name} having value {value}')
def input_with_value(context, field_name, value):
    WebDriverWait(context.webdriver, 10).until(
        lambda d: d.find_element(By.ID, field_name).get_attribute('value') == value)


@then('they see a {message_type} message')
def message_of_type(context, message_type):
    WebDriverWait(context.webdriver, 10).until(
        presence_of_element_located((By.CSS_SELECTOR, '.messages .message.%s' % message_type)))


@then(u'the user sees a diagram with {property_type} values')
def step_impl(context, property_type: str):
    value = _get_diagram_path_for_property(context.webdriver, property_type)
    setattr(context, f'prop_{property_type}', value)


@then(u'the user sess the diagram with updated {property_type} values')
def step_impl(context, property_type):
    old_value = getattr(context, f'prop_{property_type}')
    WebDriverWait(context.webdriver, 10, 1).until(lambda d: _get_diagram_path_for_property(d,
                                                                                           property_type) is not None and old_value != _get_diagram_path_for_property(
        d, property_type))
    setattr(context, f'prop_{property_type}', _get_diagram_path_for_property(context.webdriver, property_type))


@then('they see the calendar called {calendar_name}')
def find_calendar(context, calendar_name: str):
    context.webdriver.find_elements()
    WebDriverWait(context.webdriver, 10).until(
        lambda d: _verify_property(d, context.entity_name, 'person', 'calendar', calendar_name),
        f"No calendar {calendar_name} of person {context.entity_name} found")


def _get_diagram_path_for_property(webdriver, property_type) -> Optional[str]:
    webdriver.refresh()
    try:
        css_selector = '.diagram[data-attribute="%s"] svg > g > path' % property_type.replace(' ', '-')
        new_value = webdriver.find_element(By.CSS_SELECTOR, css_selector).get_dom_attribute('d')
        return new_value
    except:
        return None
