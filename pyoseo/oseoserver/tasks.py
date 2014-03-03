'''
Celery tasks for pyoseo
'''

# TODO
# - Refine the task that processes orders
# - Break it down into smaller tasks
# - Instead of calling oseoserver.models directly, develop a RESTful API
#   and communicate with the database over HTTP. This allows the task to
#   run somewhere else, instead of having it in the same machine

from django.core.exceptions import ObjectDoesNotExist
from celery import shared_task

import giosystemcore.settings
import giosystemcore.files
import giosystempackages.cswinterface
from oseoserver import models

@shared_task()
def process_order(order_id):
    '''
    Process a normal order.

    * get order details from the database
    * fetch the products from giosystem
    * apply any customization options
    * update the database whenever an order/item changes status
    * if needed, send notifications on order/item status changes
    * send the ordered items to the appropriate destination

    :arg order_id: The id of the order in the pyoseo database
    :type order_id: int
    '''

    ids = []
    try:
        order = models.Order.objects.get(id=order_id)
    except ObjectDoesNotExist:
        print('could not find order')
        raise
    for batch in order.batch_set.all():
        for order_item in batch.orderitem_set.all():
            ids.append(order_item.identifier)
    settings_url = 'http://geo2.meteo.pt/giosystem/settings/api/v1/'
    manager = giosystemcore.settings.get_settings(settings_url)
    c = giosystempackages.cswinterface.CswInterface()
    item_titles = c.get_records(ids)
    g2files = []
    for file_id, file_name in item_titles:
        g2files.append(giosystemcore.files.GioFile.from_file_name(file_name))
