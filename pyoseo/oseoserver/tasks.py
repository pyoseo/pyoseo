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

The celery worker can be started with the command:

.. code:: bash

   pyoseo/pyoseo$ celery worker --app=pyoseo.celery_app --loglevel=info
'''

# TODO
# * Instead of calling oseoserver.models directly, develop a RESTful API
#   and communicate with the database over HTTP. This allows the task to
#   run somewhere else, instead of having it in the same machine

import os
import datetime as dt

from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings as django_settings
from celery import shared_task
from celery import group
from celery.utils.log import get_task_logger

import giosystemcore.settings
import giosystemcore.files
import giosystemcore.catalogue.cswinterface
import giosystemcore.orders.orderpreparator as op

from oseoserver import models

logger = get_task_logger(__name__)

@shared_task(bind=True)
def process_normal_order(self, order_id):
    '''
    Process a normal order.

    A normal order is one that does not come from a subscription and is also 
    not considered to be a massive order.

    :arg order_id:
    :type order_id: int
    '''

    try:
        order = models.Order.objects.get(pk=order_id)
        order.status = models.CustomizableItem.IN_PRODUCTION
        order.save()
    except ObjectDoesNotExist:
        logger.error('could not find order')
        raise
    g = []
    for batch in order.batches.all():
        g.append(process_batch.s(batch.id))
    job = group(g)
    job.apply_async()

@shared_task(bind=True)
def process_batch(self, batch_id):
    '''
    Process an order batch.

    :arg batch_id:
    :type batch_id: int
    '''

    try:
        batch = models.Batch.objects.get(pk=batch_id)
    except ObjectDoesNotExist:
        logger.error('could not find batch %s in the order server database'
                     % batch_id)
        raise
    g = []
    for item in batch.order_items.all():
        g.append(process_order_item.s(item.id))
    job = group(g)
    job.apply_async()

@shared_task(bind=True)
def process_order_item(self, order_item_id):
    '''
    Process an order item.

    :arg order_item_id: Database identifier of the ordered item
    :type order_item_id: int
    '''

    giosystemcore.settings.get_settings(django_settings.GIOSYSTEM_SETTINGS_URL,
                                        initialize_logging=False)
    csw_interface = giosystemcore.catalogue.cswinterface.CswInterface()
    order_item = models.OrderItem.objects.get(pk=order_item_id)
    try:
        id, title = csw_interface.get_records([order_item.identifier])[0]
    except IndexError:
        logger.error('could not find order item %s in the catalogue' % \
                     order_item_id)
        raise 
    user_name = order_item.batch.order.user.username
    preparator = op.OrderPreparator(user_name)
    order_item.status = models.CustomizableItem.IN_PRODUCTION
    order_item.save()
    gio_file = giosystemcore.files.GioFile.from_file_name(title)
    fetched = preparator.fetch(gio_file)
    # customization is not supported yet
    customized = preparator.customize(gio_file, fetched, options=None)
    moved = preparator.move(customized)
    if moved is not None:
        order_item.file_name = os.path.basename(moved)
        order_item.completed_on = dt.datetime.utcnow()
        order_item.status = models.CustomizableItem.COMPLETED
        order_item.save()
        _update_order_status(order_item.batch.order)
    else:
        pass

def _update_order_status(order):
    '''
    Update the status of a normal order whenever the status of its batch
    changes

    :arg order:
    :type order: oseoserver.models.Order
    '''

    if order.order_type.name == models.OrderType.PRODUCT_ORDER:
        batch_statuses = set([b.status() for b in order.batches.all()])
        old_order_status = order.status
        if len(batch_statuses) == 1:
            new_order_status = batch_statuses.pop()
            if old_order_status != new_order_status:
                order.status = new_order_status
                if new_order_status == models.CustomizableItem.COMPLETED:
                    order.completed_on = dt.datetime.utcnow()
                order.save()
