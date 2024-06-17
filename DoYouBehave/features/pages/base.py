import re


class BasePage(object):
    """Base class to initialize the base page that will be called from all
    pages"""

    def __init__(self, webdriver, base_url: str, path=''):
        self._webdriver = webdriver
        self.base_url = base_url
        self.url = f"{self.base_url}{path}"

    def is_current_page(self):
        return re.compile(f"^{self.url.replace('%s', '([-A-Za-z0-9_.,() ]+)')}/?").fullmatch(
            self._webdriver.current_url) is not None

    def navigate_to(self):
        self._webdriver.get(self.url)
