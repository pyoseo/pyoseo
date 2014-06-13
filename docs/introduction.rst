Introduction
============

pyoseo is an ordering server. It processes requests for spatial data and makes
the data available to the requesting user upon completion.

It implements the OGC OSEO standard

OSEO operations
---------------

* GetCapabilities - Not implemented
* GetOptions
* GetQuotation - Not implemented
* GetQuotationResponse - Not implemented
* Submit
* SubmitResponse - Not implemented
* Getstatus
* DescribeResultAccess
* Cancel
* CancelResponse - Not implemented

How it works internally
-----------------------

pyoseo is composed of the following parts:

* web server - listens to incoming requests and issues replies
* database - records every order and associated parameters. Tracks an order's
  state as it gets processed
* queueing system - A process that is continuously running, preparing orders as
  they are requested. Order processing is asynchronous.


.. graphviz::

   digraph pyoseo_components {
       "client" -> "web server";
       "web server" -> "database";
       "database" -> "queueing system";
   }
