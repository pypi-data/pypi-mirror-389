Installation
************

This section shows how you can install this BalderHub package.

Install python
==============

For this python in the version ``3.9`` or higher is required. You can get the latest version of python at
`https://www.python.org/downloads/ <https://www.python.org/downloads/>`_ or install it with your packet management
system of your operating system.

Install balder
==============

You can easily install balder in different ways, that are described here.

.. code-block::

    python -m pip install baldertest

Install balderhub-html
======================

You can easily install this package with the following command:

.. code-block::

    python -m pip install balderhub-html

Install and Assign GUIControl Package
=====================================

If you want to control the HTML components in this package, you'll need a package that implements GUI controls, at least
at the setup level.

The following list shows some examples of these packages, along with instructions on how to install them:

+--------------------------+--------------------------------------+-----------------------------------------------------+----------------------------------------------------------------+
| Project                  | Install with Command                 | Description                                         | Link to Documentation                                          |
+==========================+======================================+=====================================================+================================================================+
| ``balderhub-selenium``   | ``pip install balderhub-selenium``   | package to control browsers with                    | `Documentation <https://hub.balder.dev/projects/selenium>`__   |
|                          |                                      | `selenium <https://www.selenium.dev/>`__            | `GitHub <https://github.com/balder-dev/balderhub-selenium>`__  |
+--------------------------+--------------------------------------+-----------------------------------------------------+----------------------------------------------------------------+
| ``balderhub-playwright`` |                                      | package to control browsers with                    | NOT YET RELEASED                                               |
| (COMING SOON)            |                                      | `playwright <https://playwright.dev/>`__            |                                                                |
+--------------------------+--------------------------------------+-----------------------------------------------------+----------------------------------------------------------------+
| ``balderhub-appium``     |                                      | package to control browsers or android/ios apps     | NOT YET RELEASED                                               |
| (COMING SOON)            |                                      | with `Appium <https://appium.io/>`__                |                                                                |
+--------------------------+--------------------------------------+-----------------------------------------------------+----------------------------------------------------------------+
| ``balderhub-textual``    |                                      | package for testing textual applications            | NOT YET RELEASED                                               |
| (COMING SOON)            |                                      | (see Textual                                        |                                                                |
|                          |                                      | `Documentation <https://textual.textualize.io/>`__) |                                                                |
+--------------------------+--------------------------------------+-----------------------------------------------------+----------------------------------------------------------------+


Just assign these to the device that represents the HTML page, and this package will handle everything else.

.. code-block:: python

    import balder
    from balderhub.selenium.lib.setup_features import SeleniumChromeWebdriverFeature  # or any other WebDriver implementing feature
    from lib.pages import MyPage


    class SetupBase(balder.Setup):

        class Client(balder.Device):
            selenium = SeleniumChromeWebdriverFeature()
            page = MyPage()

Read more about the details in the `Example Section <Examples>`_.