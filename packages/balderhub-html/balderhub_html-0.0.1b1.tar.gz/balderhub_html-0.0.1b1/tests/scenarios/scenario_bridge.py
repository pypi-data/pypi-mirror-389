import balder

from balderhub.selenium.lib.scenario_features import SeleniumFeature
from tests.lib.setup_features.test_page import TestPage


class ScenarioBridge(balder.Scenario):

    class Client(balder.Device):
        selenium = SeleniumFeature()
        testpage = TestPage()

    @balder.fixture('testcase')
    def connect_selenium(self):
        self.Client.selenium.create()
        yield
        self.Client.selenium.quit()

    def test_check_username(self):
        self.Client.testpage.open()
        self.Client.testpage.wait_for_page()
        assert self.Client.testpage.input_username.exists()
