pyoseo celery daemonization
===========================

In order to process orders, pyoseo uses the celery distributed task queue.

* Create a *celery* user with the useradd command

  .. code:: bash

     sudo useradd --system celery

* Place a copy of the celeryd sysv init script in /etc/init.d and give it
  executable permissions

  .. code:: bash

     sudo cp scripts/celeryd.init /etc/init.d/celeryd
     sudo chmod 755 /etc/init.d/celeryd

* Copy the init configuration file to the correct location

  .. code:: bash

     sudo cp scripts/celeryd.init /etc/init.d/celeryd
     sudo cp scripts/celeryd.conf /etc/default/celeryd

* Install the service

  .. code:: bash

     sudo update-rc.d celeryd defaults

* Start the service with

  .. code:: bash

     sudo service celeryd start

* you can check the status of the service by running

  .. code:: bash

     sudo service celeryd status

* From now on, celery will be auto started at boot
