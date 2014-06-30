Database structure
==================

Pyoseo's data model follows the concepts described in `OGC's OSEO Standard`_. The database is
built and managed by using `django's orm`_.

.. _django's orm: https://docs.djangoproject.com/en/1.6/topics/db/models/

.. _OGC's OSEO Standard: http://opengeospatial.org/standards/oseo/

In general terms, the database stores each order's details. An *order* is
composed of one or more *batches*, which are themselves composed of one or more
*order items*.

An :class:`~oseoserver.models.Order` is a container that groups together 
batches of order items and the selected processing and delivery options.

A :class:`~oseoserver.models.Batch` is a group of order items which are 
processed and delivered to the client in the same processing run. Normal 
orders are composed of a single batch. Massive orders can be composed of 
more than one batch, depending on the size of the ordered items. Such an order
can be broken down into smaller batches which get processed and delivered 
sequentially, as to prevent flooding the server's filesystem with a massive
number of files.

An :class:`~oseoserver.models.OrderItem` is a single file that has been 
requested as part of an order. Each order item may define custom processing 
and delivery options, or it may inherit the definitions of its order.

Quotations and tasking requests are not implemented yet.
