pyoseo celery daemonization
===========================

* Create a celery user with the useradd command

  .. code:: bash

     sudo useradd --system celery

* Create celery directories in /var/log and /var/run and assign the celery user
  as their owner

  .. code:: bash

     sudo mkdir /var/log/celery
     sudo chwon celery:celery /var/log/celery
     sudo mkdir /var/run/celery
     sudo chwon celery:celery /var/run/celery

* Place a copy of the celeryd initv script in /etc/init.d and give it
  executable permissions

  .. code:: bash

     sudo cp scripts/celeryd.init /etc/init.d/celeryd
     sudo chmod 755 /etc/init.d/celeryd

* Copy the init configuration file to the correct location

  .. code:: bash

     sudo cp scripts/celeryd.init /etc/init.d/celeryd
     sudo cp scripts/celeryd.conf /etc/default/celeryd

* Start the service with

  .. code:: bash

     sudo service celeryd start

* From now on, celery will be auto started at boot
