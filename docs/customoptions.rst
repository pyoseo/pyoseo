Hooking up your custom order options
====================================

Every server has its own options for customizing orders and order items.
In order to advertise your options with PyOSEO you must:

* add them in the administration backend

* add the :attr:`~pyoseo.settings.OSEOSERVER_OPTIONS_CLASS` setting,
  indicating the path to a Python class that knows how to extract the options
