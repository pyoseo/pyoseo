Hooking up your order processing modules
========================================

Every organization has its own way to process orders. You may be using
sophisticated processing lines, simple shell scripts or some other. Either
way, pyoseo cannot cope with all the diversity out there. As such, you must
implement the order processing and connect it to pyoseo.

Order processing classes
------------------------

You must create a custom class for processing individual order items and
specify it in the
:attr:`~pyoseo.settings.OSEOSERVER_ORDER_ITEM_PROCESSING_CLASS` setting

This class must provide at least a `process_item` method. This method will be
called by pyoseo whenever it needs to process an order item. It must have the
following signature:

.. py:class:: MyOrderItemProcessor

   .. py:method:: process_item(item_id, delivery_method)

      Some stuff here

The order processing class has three main responsabilities:

1. Converting between an order item id and the real file(s) that have been
   requested. This may involve querying an OGC CSW server or some other
   procedure

#. Fetching the ordered files from your organization's storage facilities. This
   may be as simple as a local filesystem copy command, or a bit more
   complicated, like searching a remote long term archive system and retrieving
   the files via some specialized protocol.

#. Handling the delivery of the files to the user. PyOSEO

Example
-------
