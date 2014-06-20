Installing pyoseo
=================
pyoseo
------

Installing pyoseo requires following these instructions:

1. Install some system-wide dependencies:

   .. code:: bash

      sudo apt-get install apache2 rabbitmq-server redis-server python-dev \
          python-virtualenv

#. Decide on a directory to host your server, create a virtualenv and activate
   it

   .. code:: bash

      mkdir -p ~/giosystem
      cd ~/giosystem
      virtualenv venv
      source venv/bin/activate

#. Install the giosystemcore library. For now pyoseo depends on this library,
   but in the future it will be independent. Follow the installation
   instructions available at `giosystemcore's readthedocs page`_.

.. _giosystemcore's readthedocs page: http://giosystemcore.readthedocs.org

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
       GIOSYSTEM_SETTINGS_URL = 'http://gio-gl.meteo.pt/giosystem/settings/api/v1/'

   Add any other settings that you may need, for example, for the
   authentication module

#. Create the django database structure, choosing to create a superuser for
   django administration when prompted

   .. code:: bash

      cd ..
      python manage.py syncdb

#. Populate the django database with some initial fixture data

   .. code:: bash

      python manage.py loaddata oseoserver/fixtures/default_data.json

#. Run the collectstatic command in order to copy the admin backend's assets to
   the proper directory

   .. code:: bash

      python manage.py collectstatic --noinput --verbosity=0

#. Configure an apache2 virtual host for serving the site

   .. code:: bash

      sudo vim /etc/apache2/sites-available/giosystem.conf

   Add the following lines inside the `VirtualHost` directive::

       # settings for the ordering server (preview)
       Alias /giosystem/ordering/static /home/geo6/giosystem/venv/src/pyoseo/pyoseo/sitestatic/

       <Directory /home/geo6/giosystem/venv/src/pyoseo/pyoseo/sitestatic/>
           Order deny,allow
           Allow from all
       </Directory>

       WSGIDaemonProcess giosystem_ordering user=geo6 group=geo6 processes=1 
       threads=1 display-name='%{GROUP}' 
       python-path=/home/geo6/giosystem/venv/lib/python2.7/site-packages:/home/geo6/giosystem/venv/src/pyoseo/pyoseo
       WSGIProcessGroup giosystem_ordering
       WSGIScriptAlias /giosystem/ordering /home/geo6/giosystem/venv/src/pyoseo/pyoseo/pyoseo/wsgi.py

       <Location /giosystem/ordering>
           WSGIProcessGroup giosystem_ordering
       </Location>

       <Directory /home/geo6/giosystem/venv/src/pyoseo/pyoseo/pyoseo>
           <Files wsgi.py>
               Order deny,allow
               Allow from all
           </Files>
       </Directory>

#. The server should now be available on your host. Test it by visiting the
   admin section. Access:

       http://yourserver/giosystem/ordering/admin/

Installing other components
---------------------------

PyOSEO glues together several software packages and makes them work together in
order to receive and process ordering requests

proftpd
.......

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

#. Add write permission to the *ftpuser* group on /home/ftpuser

   .. code:: bash

      sudo chmod 775 /home/ftpuser

#. When creating a new virtual user for FTP, remember to remove execution 
   permissions of the *ftpuser* on the virtual user root dir. This way the
   giosystem user is allowed to place the ordered items there (because it
   owns this directory) and the *ftpuser* user can't upload files to the
   server

   .. code:: bash

      mkdir /home/ftpuser/johndoe
      chmod 755 /home/ftpuser/johndoe

celery
......

In order to process orders, pyoseo uses the celery distributed task queue.
Celery installation and configuration requires the following:

1. Install the following system-wide dependencies:

   .. code:: bash

      sudo apt-get install rabbitmq-server redis-server

#. Since it is currently a hard dependency of pyoseo, celery has already been
   installed by pip. For the record, these are the additional python packages
   needed (there are others, that get pulled automatically by these):

   .. code:: bash

      pip install celery redis

#. Place a copy of the celeryd sysv init script in /etc/init.d and give it
   executable permissions

   .. code:: bash

      sudo cp pyoseo/oseoserver/scripts/celeryd.init /etc/init.d/celeryd
      sudo chmod 755 /etc/init.d/celeryd

#. Copy the init configuration file to the correct location

   .. code:: bash

      sudo cp pyoseo/oseoserver/scripts/celeryd.conf /etc/default/celeryd

#. Tweak the configuration file by pointing the `CELERY_BIN` and `CELERY_CHDIR`
   variables to the correct paths and adjusting the `CELERY_USER` and
   `CELERY_GROUP` variables

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

#. There is also a graphical tool for inspecting celery. It is called
   *flower*. You can install it by running:

   .. code:: bash

      pip install flower

   Start flower with:

   .. code:: bash

      celery flower

   Now point your web browser to `http://localhost:5555`

