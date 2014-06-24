Celery tasks
============

.. automodule:: oseoserver.tasks
   :members:
   :undoc-members:
   :show-inheritance:

   .. autofunction:: process_normal_order(order_id)
   .. autofunction:: process_batch(batch_id)
   .. autofunction:: process_online_data_access_item(order_item_id, delivery_option_id)
   .. autofunction:: process_online_data_delivery_item(order_item_id, delivery_option_id)
   .. autofunction:: process_media_delivery_item(order_item_id, delivery_option_id)
   .. autofunction:: update_order_status(order_id)
   .. autofunction:: monitor_ftp_downloads()
   .. autofunction:: delete_old_orders()
