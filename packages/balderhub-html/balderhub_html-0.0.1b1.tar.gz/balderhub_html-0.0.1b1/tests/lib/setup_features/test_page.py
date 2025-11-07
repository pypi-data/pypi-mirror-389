from typing import Union, List

from balderhub.html.lib.utils.selector import Selector
from balderhub.html.lib.utils import components as html
import balderhub.html.lib.scenario_features
from balderhub.url.lib.utils import Url


class TestPage(balderhub.html.lib.scenario_features.HtmlPage):

    @property
    def applicable_on_url_schema(self) -> Union[Url, List[Url]]:
        return Url('http://webserver:8000')

    def open(self):
        self.driver.navigate_to(self.applicable_on_url_schema)

    # TODO add other stuff

    @property
    def input_username(self):
        return html.inputs.HtmlTextInput.by_selector(self.driver, Selector.by_name('username'))
