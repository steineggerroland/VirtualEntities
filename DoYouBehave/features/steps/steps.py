import random
import re

from behave import *
from selenium.webdriver.common.by import By

from features.pages.virtual_entity_page import VirtualEntityPage


@given('the user goes to the {page_name} page')
def load_page(context, page_name: str):
    context.webdriver.get(context.urls[page_name])


@When('the power consumption of the {appliance_name} is updated')
def send_power_consumption(context, appliance_name: str):
    context.new_value = round(random.random() * 2400, 2)
    context.appliances[appliance_name].send_power_consumption_update(context.new_value)


@When('the room climate of the {room_name} is updated')
def send_room_climate(context, room_name: str):
    context.new_value = {'temperature': round(random.random() * 6 + 18, 2),
                         'humidity': round(random.random() * 40 + 50, 2)}
    context.rooms[room_name].send_room_climate_update(context.new_value)


@then('they are {redirect_or_on} the {page_name} page')
def current_page_is(context, redirect_or_on, page_name: str):
    expected_url = context.urls[page_name]
    assert context.webdriver.current_url.startswith(expected_url)


@then('they see rooms in the room catalog')
def rooms_in_catalog(context):
    assert context.webdriver.find_elements(By.CSS_SELECTOR, '.room-catalog .room')


@then('they see appliances in the appliance depot')
def appliances_in_depot(context):
    assert context.webdriver.find_elements(By.CSS_SELECTOR, '.appliance-depot .appliance')


@then('they see person in the register of persons')
def persons_in_register(context):
    assert context.webdriver.find_elements(By.CSS_SELECTOR, '.register-of-persons .person')


@then('they see the rooms {room_names}')
def room_is_shown(context, room_names: str):
    ve_page = VirtualEntityPage(context.webdriver)
    room_names = map(lambda r: r.strip().replace('"', ''), room_names.split(","))
    for room_name in room_names:
        assert any(r.find_element(By.CLASS_NAME, 'name').text == room_name for r in ve_page.rooms())


@then('they see the appliances {appliance_names}')
def appliance_is_shown(context, appliance_names: str):
    ve_page = VirtualEntityPage(context.webdriver)
    appliance_names = map(lambda a: a.strip().replace('"', ''), appliance_names.split(","))
    for appliance_name in appliance_names:
        assert any(a.find_element(By.CLASS_NAME, 'name').text == appliance_name for a in ve_page.appliances())


@then('they see the persons {person_names}')
def appliance_is_shown(context, person_names: str):
    ve_page = VirtualEntityPage(context.webdriver)
    person_names = map(lambda p: p.strip().replace('"', ''), person_names.split(","))
    for person_name in person_names:
        assert any(p.find_element(By.CLASS_NAME, 'name').text == person_name for p in ve_page.persons())


@then('the user sees the new {property_name} for the {entity_name} after a refresh')
def appliance_has_power_consumption(context, property_name, entity_name):
    context.webdriver.refresh()
    entity_type = 'appliance' if property_name in ['power consumption'] else 'room'
    entity_name_in_class = property_name.replace(' ', '-')
    new_value = context.new_value if type(context.new_value) is not dict else context.new_value[property_name]
    found_matching_entity = False
    for appliance_element in context.webdriver.find_elements(By.CSS_SELECTOR, '.%s' % entity_type):
        if appliance_element.find_element(By.CLASS_NAME, 'name').text == entity_name:
            value_with_unit = appliance_element.find_element(By.CLASS_NAME, entity_name_in_class).text
            extracted_float = float(re.search(r'[-+]?[0-9]*\.?[0-9]+', value_with_unit).group(0))
            assert extracted_float == float(new_value)
            found_matching_entity = True
    assert found_matching_entity
