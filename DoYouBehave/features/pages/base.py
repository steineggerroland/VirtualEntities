import re

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.expected_conditions import url_matches


class BasePage(object):
    """Base class to initialize the base page that will be called from all
    pages"""

    def __init__(self, webdriver, base_url: str, path=''):
        self._webdriver: WebDriver = webdriver
        self.base_url = base_url
        self.url = f"{self.base_url}{path}"
        self.url_matcher = f"^{self.url.replace('%s', '([-A-Za-z0-9_.,() ]+)')}/?"

    def is_current_page_matcher(self):
        return url_matches(self.url_matcher)


    def navigate_to(self):
        self._webdriver.get(self.url)
