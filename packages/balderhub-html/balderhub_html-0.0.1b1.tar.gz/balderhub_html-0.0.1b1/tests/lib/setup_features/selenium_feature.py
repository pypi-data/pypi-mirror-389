import os
from selenium.webdriver.common.options import BaseOptions
from selenium.webdriver.firefox.options import Options

import balderhub.selenium.lib.setup_features


class SeleniumFeature(balderhub.selenium.lib.setup_features.SeleniumRemoteWebdriverFeature):

    @property
    def command_executor(self):
        hostname = os.getenv('SELENIUM_HOSTNAME')
        if not hostname:
            hostname = '127.0.0.1'
        return f"http://{hostname}:4444"

    @property
    def selenium_options(self) -> BaseOptions:
        return Options()
