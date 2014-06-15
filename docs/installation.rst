Installing pyoseo
=================

.. toctree::
   :maxdepth: 2

   celery

Installing pyoseo requires following these instructions:

1. Install some system-wide dependencies:

   .. code:: bash

      sudo apt-get install apache2 rabbitmq-server python-dev python-virtualenv

#. Decide on a directory to host your server, create a virtualenv and activate
   it

   .. code:: bash

      mkdir -p ~/giosystem
      cd ~/giosystem
      virtualenv venv
      source venv/bin/activate

#. Install the giosystemcore library. For now pyoseo depends on this library,
   but in the future it will be independent. Follow the installation
   instructions available at giosystemcore's readthedocs page.

#. Be sure to install pyxb with the OGC schemas. It is part of giosystemcore's
   install procedure.

#. install pyoseo itself, using pip:

   .. code:: bash

      pip install --editable https://github.com/ricardogsilva/pyoseo.git

#. Create a settings_local.py file with your local settings, including
   sensitive data

   .. code:: bash

      cd venv/src/pyoseo/pyoseo/pyoseo
      touch settings_local.py

   The contents of this file should be:

       STATIC_URL = 
       DEBUG = False
       ALLOWED_HOSTS = 
       GIOSYSTEM_SETTINGS_URL = <url for the giosystem settings app>

    Add any other settings that you may need, for example, for the
    authentication module

#. Create the django database structure, choosing to create a superuser for
   django administration when prompted

   .. code:: bash

      cd venv/src/pyoseo/pyoseo
      python manage.py syncdb

#. Populate the django database with some initial fixture data

   .. code:: bash

      python manage.py loaddata oseoserver/fixtures/default_data.json

#. Run the collectstatic command in order to copy the admin backend's assets to
   the proper directory

   .. code:: bash

      python manage.py collectstatic --noinput --verbosity=0

#. Test that the django admin can be accessed using the testing server

#. Install celery as a service that runs at boot

#. Configure an apache2 virtual host for serving the site


Don't forget to populate the database with the initial values for the following
models:

* OptionGroup
* At least one of OnlineDataAccess OnlineDataDelivery, MediaDelivery
* DeliveryOptionOrderType
* GroupDeliveryOption
