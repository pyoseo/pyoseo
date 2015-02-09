Installing pyoseo
=================
pyoseo
------

Installing pyoseo requires following these instructions:

1. Install some system-wide dependencies:

   .. code:: bash

      sudo apt-get install apache2 rabbitmq-server redis-server python-dev \
          python-virtualenv python-virtualenvwrapper

#. Configure virtualenvwrapper. Choose a directory to hold your python
   virtualenvs (here we suggest ~/venvs) and another for your code. Finally
   add some extra lines to your bashrc, in order to setup virtualenvwrapper.

   .. code:: bash

      mkdir ~/venvs
      mkdir ~/dev
      echo 'export WORKON_HOME=$HOME/.venvs' >> ~/.bashrc
      echo 'export PROJECT_HOME=$HOME/dev' >> ~/.bashrc
      echo 'export PIP_DOWNLOAD_CACHE=$HOME/.pip-downloads' >> ~/.bashrc
      echo 'source /usr/local/bin/virtualenvwrapper.sh' >> ~/.bashrc

#. Reload your `.bashrc`

   .. code:: bash

      source ~/.bashrc

#. Create a virtualenv for pyoseo. The first time you create it, it gets
   automatically activated (When you want to work on it later on, remember
   to activate it yourself)

   .. code:: bash

   mkvirtualenv pyoseo
   # workon pyoseo

#. Install the Pyxb python package. Pyoseo requires that the OGC schemas be
   compiled with pyxb. This requires editing some pyxb scripts before
   installation:

   .. code:: bash

      pip install --no-install pyxb
      cd $VIRTUAL_ENV/build/pyxb
      export PYXB_ROOT=$(pwd)
      pyxb/bundles/opengis/scripts/genbind
      pip install --no-download pyxb
      cd -

#. install pyoseo itself, using a combination of git and pip:

   .. code:: bash

      cd $PROJECT_HOME
      git clone https://github.com/ricardogsilva/pyoseo.git
      pip install --editable pyoseo

#. Create a settings_local.py file with your local settings, including
   sensitive data

   .. code:: bash

      cd venv/src/pyoseo/pyoseo/pyoseo
      touch settings_local.py

   The contents of this file should be, for example:

   .. code:: python

      STATIC_URL = '/giosystem/ordering/static/'
      DEBUG = False
      ALLOWED_HOSTS = ['.<yourdomainname>',]
      OSEOSERVER_AUTHENTICATION_CLASS = 'python.path.to.auth.class'
      OSEOSERVER_PROCESSING_CLASS = 'python.path.to.order.processing.class'
      OSEOSERVER_OPTIONS_CLASS = 'python.path.to.options.class'

   Add any other settings that you may need, for example, for the
   authentication module

#. Create the django database structure and also a superuser for the django
   administration backend

   .. code:: bash

      cd $PROJECT_HOME/pyoseo/pyoseo
      python manage.py migrate
      python manage.py createsuperuser

#. Setup the default pyoseo values by running the `pyoseodefaults` management
   script.

   .. code:: bash

      python manage.py pyoseodefaults

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

.. note::

   These extra components need to be properly configured. This is specially
   important in regard to log file configuration. The log files are usually
   rotated using `logrotated`, the standard daemon for rotating and saving
   logfiles on linux.

.. _proftpd-installation-label:

proftpd
.......

ProFTPd is an FTP server. Depending on your use case you may not need an FTP
server in order to use pyoseo. If you do need one, there are some to choose
from. Proftpd works well if you want to use an LDAP based authentication
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

#. Change the log rotation configuration for proftpd in order to produce log
   files that can be world-readable. This is necessary for pyoseo to be able to
   monitor FTP downloads. Add the following to
   `/etc/logrotate.d/proftpd-basic`::

       /var/log/proftpd/xferlog
       {
           daily
           missingok
           rotate 5
           compress
           delaycompress
           create 644 root adm
           sharedscripts
           postrotate
               # reload could be not sufficient for all logs, a restart is safer
               invoke-rc.d proftpd restart 2>/dev/null >/dev/null || true
           endscript
       }

   This configuration will cause proftpd's logs to be rotated every day.

   .. note::

      When does the log file rotate?
      
      This gets a little confusing.
      The logrotate command is set to run as a cron job, as indicated in
      `/etc/cron.daily/logrotate`. cron.daily entries can either run standalone
      or run under `anacron`. If run standalone, they are configured in
      `/etc/crontab`. If run by `anacron`, the file `/etc/anacrontab` should
      hold a line with the execution of cron.daily and the correct time.
      Now, anacron is itself run by cron, so there will be a file
      `/etc/cron.d/anacron` that specifies when anacron is to be run.
      By default, on Ubuntu, anacron *is* installed and setup to run at 7:30.
      Cron.daily is setup to run once a day, with a delay of five minutes,
      meaning it will run at about 7:35.

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

#. Change proftpd's init script in order to workaround `bug #1293416`_. Edit
   the `/etc/init.d/proftpd` init script, adding a `sleep 2` to line #180.
   Since the bug report is a bit unclear, a safe choice is to add the sleep
   command both before and after line #180.

.. _bug #1293416: https://bugs.launchpad.net/ubuntu/+source/proftpd-dfsg/+bug/1293416

#. restart the proftpd daemon

   .. code:: bash

      sudo service proftpd restart

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

#. In order for pyoseo to work, we must use (at least one) celery worker and
   also a celerybeat instance. Celery workers are the processes that manage the
   execution queue. Celerybeat is a process that allows running tasks
   periodically. Pyoseo needs both queued and periodic tasks.
   To allow the celery daemon processes to start at boot, we need to install
   these processes enabling them to run as services.

   * Place a copy of the pyoseo-worker sysv init script in `/etc/init.d`,
     and give it executable permissions.

     .. code:: bash

        sudo cp pyoseo/oseoserver/scripts/pyoseo-worker /etc/init.d
        sudo chmod 755 /etc/init.d/pyoseo-worker

   * Place a copy of the pyoseo-beat.conf sysv init script in `/etc/init.d`,
     and give it executable permissions.


   .. code:: bash

      sudo cp pyoseo/oseoserver/scripts/pyoseo-beat /etc/init.d
      sudo chmod 755 /etc/init.d/pyoseo-beat

#. Copy the init configuration files to the correct locations

   .. code:: bash

      sudo cp pyoseo/oseoserver/scripts/pyoseo-worker.conf /etc/default/pyoseo-worker
      sudo cp pyoseo/oseoserver/scripts/pyoseo-beat.conf /etc/default/pyoseo-beat

#. Tweak the configuration files by pointing the `CELERY_BIN` and `CELERY_CHDIR`
   variables to the correct paths and adjusting the `CELERY_USER` and
   `CELERY_GROUP` variables

#. Add configuration for enabling the rotation of celery log files, to ensure
   that they don't grow forever. Add the following to
   `/etc/logrotate.d/pyoseo-celery`::

      /var/log/celery/*.log
      {
          weekly
          missingok
          rotate 7
          compress
          delaycompress
          notifempty
          copytruncate
          create 640 root adm
      }

#. Install the services

   .. code:: bash

      sudo update-rc.d pyoseo-worker defaults
      sudo update-rc.d pyoseo-beat defaults

#. Start the services with

   .. code:: bash

      sudo service pyoseo-worker start
      sudo service pyoseo-beat start

#. you can check the status of the services by running

   .. code:: bash

      sudo service pyoseo-worker status
      sudo service pyoseo-beat status

#.  From now on, celery services will be auto started at boot

#. You can inspect the celery daemon's log file at
   `/var/log/celery/worker1.log` and `/var/log/celery/celeryd.log`.

#. There is also a graphical tool for inspecting celery. It is called
   *flower*. You can install it by running:

   .. code:: bash

      pip install flower

   Start flower with:

   .. code:: bash

      celery flower

   Now point your web browser to `http://localhost:5555`

