from typing import List

from test.pages.base import BasePage
from selenium.webdriver.common.by import By


class VirtualEntityPage(BasePage):
    @staticmethod
    def url(base_url):
        return f"{base_url}/virtual-entities"

    def shows_virtual_entities(self):
        return self.appliances() and self.rooms() and self.persons()

    def appliances(self) -> List:
        return self.driver.find_elements(By.CSS_SELECTOR, '.appliance-depot .appliance')

    def rooms(self) -> List:
        return self.driver.find_elements(By.CSS_SELECTOR, '.room-catalog .room')

    def persons(self) -> List:
        return self.driver.find_elements(By.CSS_SELECTOR, '.register-of-persons .person')
