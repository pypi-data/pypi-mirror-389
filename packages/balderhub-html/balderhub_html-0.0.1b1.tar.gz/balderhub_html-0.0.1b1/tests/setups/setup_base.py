import balder
from ..lib.setup_features.selenium_feature import SeleniumFeature
from ..lib.setup_features.test_page import TestPage


class SetupBase(balder.Setup):

    class Client(balder.Device):
        selenium = SeleniumFeature()
        testpage = TestPage()

