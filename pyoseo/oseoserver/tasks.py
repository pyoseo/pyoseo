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
from django.conf import settings as django_settings
from celery import shared_task
from celery.utils.log import get_task_logger

import giosystemcore.settings
import giosystemcore.files
import giosystempackages.cswinterface
from oseoserver import models

logger = get_task_logger(__name__)

@shared_task(bind=True)
def process_order(self, order_id):
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
        for batch in order.batches.all():
            for order_item in batch.order_items.all():
                ids.append(order_item.identifier)
        settings_url = django_settings.GIOSYSTEM_SETTINGS_URL
        manager = giosystemcore.settings.get_settings(settings_url,
                                                      initialize_logging=False)
        c = giosystempackages.cswinterface.CswInterface()
        item_titles = c.get_records(ids)
        g2files = []
        for file_id, file_name in item_titles:
            g2files.append(giosystemcore.files.GioFile.from_file_name(file_name))
        logger.info('g2files: %s' % g2files)
    except ObjectDoesNotExist:
        logger.error('could not find order')
