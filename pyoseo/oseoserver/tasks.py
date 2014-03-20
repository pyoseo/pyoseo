# Copyright 2014 Ricardo Garcia Silva
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

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
from celery import group
from celery.utils.log import get_task_logger

import giosystemcore.settings
import giosystemcore.files
import giosystempackages.cswinterface
import giosystemcore.orders.orderpreparator as op
from oseoserver import models

logger = get_task_logger(__name__)


@shared_task(bind=True)
def process_order(self, order_id):
    '''
    Process an order.

    :arg order_id:
    :type order_id: int
    '''

    try:
        order = models.Order.objects.get(id=order_id)
        _update_status(order, models.CustomizableItem.IN_PRODUCTION)
    except ObjectDoesNotExist:
        logger.error('could not find order')
        raise
    g = []
    settings_manager = giosystemcore.settings.get_settings(
        django_settings.GIOSYSTEM_SETTINGS_URL,
        initialize_logging=False
    )
    c = giosystempackages.cswinterface.CswInterface()
    prep = op.OrderPreparator(order.user.username)
    for batch in order.batches.all():
        g.append(process_batch.s(batch, prep, c))
    job = group(g)
    job.apply_async()

@shared_task(bind=True)
def process_batch(self, batch, order_preparator, csw_interface):
    '''
    Process an order batch.

    :arg batch:
    :type batch: models.Batch
    '''

    g = []
    for item in [item.identifier for item in batch.order_items.all()]:
        g.append(process_order_item.s(order_preparator, item, csw_interface))
    job = group(g)
    job.apply_async()

@shared_task(bind=True)
def process_order_item(self, preparator, order_item_id, csw_interface):
    '''
    Process an order item.

    :arg order_item_id:
    :type order_item_id: str
    '''

    try:
        id, title = csw_interface.get_records([order_item_id.identifier])[0]
    except IndexError:
        logger.error('could not find order item %s in the catalogue' % \
                     order_item_id)
        raise 
    order_item = models.OrderItem.objects.get(identifier=order_item_id)
    _update_status(order_item, models.CustomizableItem.IN_PRODUCTION)
    gio_file = giosystemcore.files.GioFile.from_file_name(title)
    fetched = preparator.fetch(gio_file)
    customized = preparator.customize(fetched)
    moved = preparator.move(customized)
    if moved is not None:
        _update_status(order_item, models.CustomizableItem.COMPLETED)
    else:
        pass

#@shared_task(bind=True)
#def process_order(self, order_id):
#    '''
#    Process a normal order.
#
#    * get order details from the database
#    * fetch the products from giosystem
#    * apply any customization options
#    * update the database whenever an order/item changes status
#    * if needed, send notifications on order/item status changes
#    * send the ordered items to the appropriate destination
#
#    :arg order_id: The id of the order in the pyoseo database
#    :type order_id: int
#    '''
#
#    ids = []
#    try:
#        order = models.Order.objects.get(id=order_id)
#        _update_status(order, models.CustomizableItem.IN_PRODUCTION)
#    except ObjectDoesNotExist:
#        logger.error('could not find order')
#        raise
#    for batch in order.batches.all():
#        for order_item in batch.order_items.all():
#            ids.append(order_item.identifier)
#    settings_manager = giosystemcore.settings.get_settings(
#        django_settings.GIOSYSTEM_SETTINGS_URL,
#        initialize_logging=False
#    )
#    c = giosystempackages.cswinterface.CswInterface()
#    item_titles = c.get_records(ids)
#    if not _check_items(ids, item_titles):
#        raise
#    preparator = giosystemcore.orders.orderpreparator.OrderPreparator()
#    for file_id, file_name in item_titles:
#        order_item = models.OrderItem.objects.get(identifier=file_id)
#        _update_status(order_item, models.CustomizableItem.IN_PRODUCTION)
#        gio_file = giosystemcore.files.GioFile.from_file_name(file_name)
#        preparator.add_item(gio_file)
#    logger.debug('preparator working_dir: %s' % preparator.working_dir)
#    fetched = preparator.get_products()
#    customized = preparator.customize_order(fetched)
#    if order.packaging == models.Order.BZIP2:
#        result = customized # not doing anything at the moment
#    else:
#        result = customized
#    moved = preparator.move_data(result)

def _update_status(model, new_status):
    model.status = new_status
    model.save()

#def _check_items(ordered_items, found_records):
#    '''
#    Check if all of the ordered items are indeed present in the catalog.
#    '''
#
#    result = True
#    delta = set(ordered_items).difference(set([i[0] for i in found_records]))
#    if any(delta):
#        logger.error('Some items are not present in the catalogue: %s' % \
#                     list(delta))
#        result = False
#    return result
