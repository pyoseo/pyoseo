Introduction
============

pyoseo is an ordering server. It processes requests for spatial data and makes
the data available to the requesting user upon completion.

It implements the OGC OSEO standard

GetOptions operation
--------------------

For more info refer to section ?? of the OSEO specification

Submit operation
----------------

For more info refer to section ?? of the OSEO specification

Getstatus operation
-------------------

For more info refer to section ?? of the OSEO specification

DescribeResultAccess operation
------------------------------

For more info refer to section ?? of the OSEO specification
Cancel operation
----------------

For more info refer to section ?? of the OSEO specification

GetCapabilities - Not implemented
GetQuotation - Not implemented
GetQuotationResponse - Not implemented
SubmitResponse - Not implemented
CancelResponse - Not implemented

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
