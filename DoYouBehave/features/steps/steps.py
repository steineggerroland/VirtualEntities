from behave import *
from selenium.webdriver.common.by import By

from features.pages.virtual_entity_page import VirtualEntityPage


@given('the user goes to the {page_name} page')
def load_page(context, page_name: str):
    context.webdriver.get(context.urls[page_name])


@then('they see rooms in the room catalog')
def rooms_in_catalog(context):
    assert context.webdriver.find_elements(By.CSS_SELECTOR, '.room-catalog .room')


@then('they see appliances in the appliance deoot')
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
