from typing import List

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.expected_conditions import url_matches
from selenium.webdriver.support.wait import WebDriverWait


class BasePage(object):
    """Base class to initialize the base page that will be called from all
    pages"""

    def __init__(self, webdriver: WebDriver, base_url: str, page_name: str, path=''):
        self._webdriver: WebDriver = webdriver
        self.page_name = page_name
        self.base_url = base_url
        self.url = f"{self.base_url}{path}"
        self.url_matcher = f"^{self.url.replace('%s', r'(([-A-Za-z0-9_.,() ]+)((%20)?[-A-Za-z0-9_.,() ]+)*)')}/?(\\?.*)?".replace(
            '/', r'\/')

    def is_current_page(self):
        WebDriverWait(self._webdriver, 10).until(url_matches(self.url_matcher),
                                                 "Failed to navigate to %s page. Current page is %s" % (
                                                     self.page_name, self._webdriver.current_url))

    def navigate_to(self):
        self._webdriver.get(self.url)


class EntityPage(BasePage):
    def __init__(self, driver: WebDriver, base_url: str, page_name: str, path_suffix: str = None,
                 path_prefix: str = None):
        super().__init__(driver, base_url, page_name,
                         f'{("/" + path_prefix) if path_prefix else ""}/%s{("/" + path_suffix) if path_suffix else ""}.html')

    def navigate_to_entity(self, entity_name: str):
        self._webdriver.get(self.url % entity_name)

    def is_current_page_for_entity(self, name: str):
        WebDriverWait(self._webdriver, 10).until(
            url_matches((("^%s/?(\\?.*)?$" % self.url.replace('.', r'\.')) % name.replace(' ', '%20')).replace(
                '/', r'\/')),
            "Failed to navigate to %s page of %s. Current page is %s" % (
                self.page_name, name, self._webdriver.current_url))


class VirtualEntityPage(BasePage):
    def __init__(self, driver, base_url):
        super().__init__(driver, base_url, 'virtual entities', '/virtual-entities.html')

    def shows_virtual_entities(self):
        return self.appliances() and self.rooms() and self.persons()

    def appliances(self) -> List:
        return self._webdriver.find_elements(By.CSS_SELECTOR, '.appliance-depot .appliance')

    def rooms(self) -> List:
        return self._webdriver.find_elements(By.CSS_SELECTOR, '.room-catalog .room')

    def persons(self) -> List:
        return self._webdriver.find_elements(By.CSS_SELECTOR, '.register-of-persons .person')


class AppliancePage(EntityPage):
    def __init__(self, driver, base_url):
        super().__init__(driver, base_url, 'appliance', path_prefix='appliance')


class ApplianceConfigurationPage(EntityPage):
    def __init__(self, driver, base_url):
        super().__init__(driver, base_url, 'appliance configuration', path_prefix='appliance',
                         path_suffix='configuration')


class RoomPage(EntityPage):
    def __init__(self, driver, base_url):
        super().__init__(driver, base_url, 'room details', path_prefix='room')


class RoomConfigurationPage(EntityPage):
    def __init__(self, driver, base_url):
        super().__init__(driver, base_url, 'room configuration', path_prefix='room',
                         path_suffix='configuration')


class PersonPage(EntityPage):
    def __init__(self, driver, base_url):
        super().__init__(driver, base_url, 'person details', path_prefix='person')


class PersonConfigurationPage(EntityPage):
    def __init__(self, driver, base_url):
        super().__init__(driver, base_url, 'person configuration', path_prefix='person',
                         path_suffix='configuration')
