PyOSEO - a Python OGC OSEO server
=================================

This project aims to create a server implementing OGC Ordering Service for
Earth Observation Products (OGC 06-141)

The ordering server itself is implemented as a `django application`_. This
project makes use of django-oseoserver and runs a full Django project that
is easily installed.

It is still in heavy development.

Documentation is available at `readthedocs`_

Running the tests
-----------------

Pyoseo is using `pytest`_ for its test suites. In order to run the tests be
sure to install the test requirements. Then run:

.. code:: bash

   py.test -m functional --coverage=oseoserver


.. _readthedocs: http://pyoseo.readthedocs.org
.. _django application: https://github.com/pyoseo/django-oseoserver
