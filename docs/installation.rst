Installing pyoseo
=================
pyoseo
------

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

      pip install --editable git+https://github.com/ricardogsilva/pyoseo.git#egg=pyoseo

#. Create a settings_local.py file with your local settings, including
   sensitive data

   .. code:: bash

      cd venv/src/pyoseo/pyoseo/pyoseo
      touch settings_local.py

   The contents of this file should be, for example::

       STATIC_URL = '/giosystem/ordering/static/'
       DEBUG = False
       ALLOWED_HOSTS = ['.geo2.meteo.pt',]
       GIOSYSTEM_SETTINGS_URL = http://gio-gl.meteo.pt/giosystem/settings/api/v1/

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

#. Test that the django admin can be accessed using the development server.
   Since we turned debug off in the settings_local.py file, we must start the
   development server like this:

   .. code:: bash

      python manage.py runserver geo2.meteo.pt:8000

   Now access `http://geo2.meteo.pt:8000/admin` in your browser and confirm you
   can access pyoseo's administration backend

#. Configure an apache2 virtual host for serving the site

PyOSEO glues together several software packages and makes them work together in
order to receive and process ordering requests

proftpd
-------

ProFTPd is an FTP server. Depending on your use case you may not need an FTP
server in order to use pyoseo. If you do need one, there are some to choose
from. Proftpd works well if you watn to use an LDAP based authentication
scheme.

1. Create a system user to handle the ftp service

   .. code:: bash

      sudo useradd --system --create-home ftpuser

#. Install the following packages

   .. code:: bash

      sudo apt-get install proftpd proftpd-mod-ldap

#. Adapt the following configuration files

   /etc/proftpd/ldap.conf
   /etc/proftpd/proftpd.conf
   /etc/proftpd/modules.conf

   fazer backup destes ficheiros que estão na máquina virtual <- segunda-feira

#. Add the user that will execute pyoseo to the *ftpuser* group so that it can
   manage order item placements. For example:

   .. code:: bash

      sudo usermod --append --groups ftpuser geo2

#. Refresh group information

   .. code:: bash

      newgrp ftpuser

celery
------

In order to process orders, pyoseo uses the celery distributed task queue.
Celery installation and configuration requires the following:

1. Create a *celery* user with the useradd command

   .. code:: bash

      sudo useradd --system celery

#. Place a copy of the celeryd sysv init script in /etc/init.d and give it
   executable permissions

   .. code:: bash

      sudo cp scripts/celeryd.init /etc/init.d/celeryd
      sudo chmod 755 /etc/init.d/celeryd

#. Copy the init configuration file to the correct location

   .. code:: bash

      sudo cp scripts/celeryd.conf /etc/default/celeryd

#. Tweak the configuration file by pointing the `CELERY_BIN` and `CELERY_CHDIR`
   variables to the correct paths

#. Install the service

   .. code:: bash

      sudo update-rc.d celeryd defaults

#. Start the service with

   .. code:: bash

      sudo service celeryd start

#. you can check the status of the service by running

   .. code:: bash

      sudo service celeryd status

#.  From now on, celery will be auto started at boot

#. You can inspect the celery daemon's log file at
   `/var/log/celery/worker1.log`



Don't forget to populate the database with the initial values for the following
models:

* OptionGroup
* At least one of OnlineDataAccess OnlineDataDelivery, MediaDelivery
* DeliveryOptionOrderType
* GroupDeliveryOption
