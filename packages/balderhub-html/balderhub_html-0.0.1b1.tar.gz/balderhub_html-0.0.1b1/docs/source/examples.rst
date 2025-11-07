Examples
********

This section shows different simple examples how you can integrate these tests.

Testing the Web
===============

This BalderHub package offers various features and components that make it easy to write simple tests for any kind of
web page.

Define your HTML-Page with the ``HtmlPage`` feature
---------------------------------------------------

For example, you can use the :class:`balderhub.html.lib.scenario_features.HtmlPage` class to implement elements
according to the page-object model and take advantage of the predefined `HTML Components <Components>`_:

.. code-block:: python

    from typing import Union, List

    from balderhub.html.lib.utils import components as html
    from balderhub.html.lib.utils.selector import Selector
    from balderhub.url.lib.utils import Url

    from .base_page import BasePage


    class PageLogin(BasePage):

        @property
        def applicable_on_url_schema(self) -> Union[Url, List[Url]]:
            return Url(f'https://example.com/login')

        @property
        def input_username(self):
            return html.inputs.HtmlTextInput.by_selector(self.driver, Selector.by_name('user'))

        @property
        def input_password(self):
            return html.inputs.HtmlPasswordInput.by_selector(self.driver, Selector.by_name('password'))

        @property
        def btn_login(self):
            return html.inputs.HtmlButtonInput.by_selector(self.driver, Selector.by_id('login'))

You will see shortly, that you don't need to care about how this stuff is controlled (with selenium for example).

You'll soon see that you don't need to worry about how these elements are controlled - whether it's using Selenium or
any other browser control tool.

Write the test
--------------

You can, of course, use this page directly in your scenario. If you want to write a login test yourself, you could
incorporate this feature into your scenario, for example:

.. code-block:: python

    import balder

    from lib.pages import PageLogin

    class ScenarioSimpleLogin(balder.Scenario):

        class Server(balder.Device):
            ...

        @balder.connect('Server', over_connection=balder.Connection())
        class Browser(balder.Device):
            login_page = UserLoginFeature()

        def test_login(self):
            self.Browser.login_page.wait_for_page(10)

            self.Client.login_page.input_username.type_text('username')
            self.Client.login_page.input_password.type_text('password')

            self.Client.login_page.btn_login.click()

            # verify that user was logged in successfully
            ...


Finally: Add GUIControl and run your test
-----------------------------------------

To control the HTML components, you need to add a GUI control feature (e.g., Selenium) to your setup.

The best part is that you don't need to worry about controlling the interface. This is all handled by
`the balderhub-guicontrol interface <https://hub.balder.dev/projects/guicontrol>`_. You just need to select one GUI
control implementing project (e.g., `balderhub-selenium <https://hub.balder.dev/projects/selenium>`_) and add it to
your setup, as shown below:

.. code-block:: python

    import balder
    from balderhub.selenium.lib.setup_features import SeleniumChromeWebdriverFeature  # select your browser
    from ..lib.setup_features import PageLogin


    class SetupBase(balder.Setup):

         class App(balder.Device):
            pass

        @balder.connect('App', over_connection=balder.Connection())
        class Client(balder.Device):
            selenium = SeleniumChromeWebdriverFeature()
            page = PageLogin()

That's it! Now you can run your test without having to write any Selenium-specific code.


.. code-block:: none

    +----------------------------------------------------------------------------------------------------------------------+
    | BALDER Testsystem                                                                                                    |
    |  python version 3.12.3 (main, Aug 14 2025, 17:47:21) [GCC 13.3.0] | balder version 0.1.0b14                          |
    +----------------------------------------------------------------------------------------------------------------------+
    Collect 1 Setups and 1 Scenarios
      resolve them to 1 valid variations

    ================================================== START TESTSESSION ===================================================
    SETUP SetupBase
      SCENARIO ScenarioSimpleLogin
        VARIATION ScenarioSimpleLogin.Browser:SetupBase.Client | ScenarioSimpleLogin.Server:SetupBase.App
          TEST ScenarioSimpleLogin.test_login [.]
    ================================================== FINISH TESTSESSION ==================================================
    TOTAL NOT_RUN: 0 | TOTAL FAILURE: 0 | TOTAL ERROR: 0 | TOTAL SUCCESS: 1 | TOTAL SKIP: 0 | TOTAL COVERED_BY: 0


You can interact with the project using its HTML components, without having to worry about how they are controlled. You
can read more about that in the `Examples section <Examples>`_.
