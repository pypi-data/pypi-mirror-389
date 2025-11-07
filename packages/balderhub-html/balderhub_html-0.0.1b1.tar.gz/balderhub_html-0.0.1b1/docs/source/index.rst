BalderHub-HTML
==============

This is a BalderHub package for the `Balder <https://docs.balder.dev/>`_ test framework. It allows you to test HTML
elements without needing to write your own tests from scratch. If you are new to Balder, check out the
`official documentation <https://docs.balder.dev>`_ first.

It provides different kinds of features and components that make it easy to write simple tests for any kind of web page.

For example, you can use the :class:`balderhub.html.lib.scenario_features.HtmlPage` class to implement elements
according to the page-object model and take advantage of the predefined HTML components:

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


The best part is, that you don't need to care about controlling the interface. This is all done by
`the balderhub-guicontrol interface <https://hub.balder.dev/projects/guicontrol>`_, you just need to select one
guicontrol implementing project (f.e. `balderhub-selenium <https://hub.balder.dev/projects/selenium>`_ and add it to
your setup, like shown below:

The best part is that you don't need to worry about controlling the interface. This is all handled by the
`the balderhub-guicontrol interface <https://hub.balder.dev/projects/guicontrol>`_ interface. You just need to select
one webdriver (for this project more specific guicontrol interface) implementing project (e.g.,
`balderhub-selenium <https://hub.balder.dev/projects/selenium>`_) and add it to your setup, as shown below:

.. code-block:: python

    import balder
    from balderhub.selenium.lib.setup_features import SeleniumChromeWebdriverFeature  # select your browser
    from ..lib.setup_features import PageLogin


    class SetupBase(balder.Setup):

        class Client(balder.Device):
            selenium = SeleniumChromeWebdriverFeature()
            page = PageLogin()

        # and use it
        @balder.fixture('session')
        def login_user(self):
            ...
            self.Client.page.input_username.type_text('username')
            self.Client.page.input_password.type_text('password')
            self.Client.page.btn_login.click()
            ....

You can interact with the project through its HTML components without worrying about how they are controlled. You can
read more about that in the `Examples section <Examples>`_.

.. note::
   Please note, this package is still under development. If you would
   like to contribute, take a look into the `GitHub project <https://github.com/balder-dev/balderhub-html>`_.


.. toctree::
   :maxdepth: 2

   installation.rst
   topic_intro.rst
   scenarios.rst
   features.rst
   examples.rst
   utilities.rst
