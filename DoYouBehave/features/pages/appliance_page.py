from features.pages.base import BasePage


class AppliancePage(BasePage):
    def __init__(self, driver, base_url):
        super().__init__(driver, base_url, '/appliance/%s')

    def navigate_to_entity(self, entity_name: str):
        self._webdriver.get(self.url % entity_name)
