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

Example
-------
