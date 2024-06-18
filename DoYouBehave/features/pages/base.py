from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.expected_conditions import url_matches
from selenium.webdriver.support.wait import WebDriverWait


class BasePage(object):
    """Base class to initialize the base page that will be called from all
    pages"""

    def __init__(self, webdriver, base_url: str, page_name: str, path=''):
        self._webdriver: WebDriver = webdriver
        self.page_name = page_name
        self.base_url = base_url
        self.url = f"{self.base_url}{path}"
        self.url_matcher = f"^{self.url.replace('%s', '(([-A-Za-z0-9_.,() ]+)((%20)?[-A-Za-z0-9_.,() ]+)*)')}/?".replace(
            '/', '\/')

    def is_current_page(self):
        WebDriverWait(self._webdriver, 10).until(url_matches(self.url_matcher),
                                                 "Failed to navigate to %s" % self.page_name)

    def navigate_to(self):
        self._webdriver.get(self.url)
