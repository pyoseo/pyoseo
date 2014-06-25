Introduction
============

Overview
--------

pyoseo is an ordering server. It processes requests for spatial data and makes
the data available to the requesting user upon completion.

It implements the OGC OSEO standard. OSEO stands for Ordering Services
Framework for Earth Observation Products. The standard defines interfaces,
bindings and requirements for establishing a workflow for ordering of Earth
Observation data between a server and client.

An effective OSEO server needs to implement the following components:

* web server - listens to incoming requests, passes them to the oseo engine 
  for processing. Issues the appropriate response back to the client;
* oseo engine - Parses the requests and build responses according to the OSEO
  standard;
* database - records every order and associated parameters. Tracks an order's
  state as it gets processed as well as associated data;
* queueing system - A process that is continuously running, preparing orders as
  they are requested. Order processing is asynchronous;
* order processing module - A set of tasks that perform the actual processing
  of each ordered item;
* authentication framework - Ensures that the client that made the request has
  the necessary permissions to use the server;
* order delivery module - Makes the ordered items available to the client after
  they have been processed.

.. graphviz::

   graph pyoseo_components {
       "web server" [shape = "box" style = "rounded"];
       "oseo engine" [shape = "box" style = "rounded"];
       "queueing system" [shape = "box" style = "rounded"];
       "database" [shape = "box" style = "rounded"];
       "authentication framework" [shape = "box" style = "rounded"];
       "order processing module" [shape = "box" style = "rounded"];
       "order delivery module" [shape = "box" style = "rounded"];
       "web server" -- "oseo engine";
       "oseo engine" -- "queueing system";
       "oseo engine" -- "database";
       "oseo engine" -- "authentication framework" [style = "dashed"];
       "queueing system" -- "order processing module" [style = "dashed"];
       "database" -- "order processing module" [style = "dashed"];
       "order processing module" -- "order delivery module" [style = "dashed"];
   }

Some of these components are specific to each particular implementation. As
such, instead of trying to cater to every possible situation, pyoseo provides
hooks into these modules and leaves their concrete implementation to each
particular instance. This means that the following components **must** be
implemented independently:

* Authentication framework. Check the :doc:`customauth` page for more details;
* Order processing module. Check the :doc:`customprocessing` page for more
  details;
* Order delivery module.

OSEO operations
---------------

The following operations are currently implemented:

.. toctree::
   :maxdepth: 2

   getcapabilities
   getoptions
   getquotation
   getquotationresponse
   submit
   submitresponse
   getstatus
   describeresultaccess
   cancel
   cancelresponse
