from typing import List

from features.pages.base import BasePage
from selenium.webdriver.common.by import By


class VirtualEntityPage(BasePage):
    def __init__(self, driver, base_url):
        super().__init__(driver, base_url, '/virtual-entities')

    def shows_virtual_entities(self):
        return self.appliances() and self.rooms() and self.persons()

    def appliances(self) -> List:
        return self._webdriver.find_elements(By.CSS_SELECTOR, '.appliance-depot .appliance')

    def rooms(self) -> List:
        return self._webdriver.find_elements(By.CSS_SELECTOR, '.room-catalog .room')

    def persons(self) -> List:
        return self._webdriver.find_elements(By.CSS_SELECTOR, '.register-of-persons .person')
