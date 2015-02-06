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

"""
Celery tasks for pyoseo

The celery worker can be started with the command:

.. code:: bash

   pyoseo/pyoseo$ celery worker --app=pyoseo.celery_app --loglevel=info
"""

# TODO
# * Instead of calling oseoserver.models directly, develop a RESTful API
#   and communicate with the database over HTTP. This allows the task to
#   run somewhere else, instead of having it in the same machine

import re
import datetime as dt
from datetime import datetime, timedelta

import pytz
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.conf import settings as django_settings
from django.contrib.sites.models import Site
from celery import shared_task
from celery import group, chord
from celery.utils.log import get_task_logger

from oseoserver import models
from oseoserver import utilities

logger = get_task_logger('.'.join(('celery', __name__)))


@shared_task(bind=True)
def process_product_order(self, order_id):
    """
    Process a product order.

    :arg order_id:
    :type order_id: int
    """

    try:
        order = models.ProductOrder.objects.get(pk=order_id)
        order.status = models.CustomizableItem.IN_PRODUCTION
        order.additional_status_info = "Order is being processed"
        order.save()
    except models.ProductOrder.DoesNotExist:
        logger.error('could not find order {}'.format(order_id))
        raise
    g = []
    for batch in order.batches.all():
        sig = process_product_order_batch.subtask((batch.id,))
        g.append(sig)
    job = group(g)
    job.apply_async()


@shared_task(bind=True)
def process_product_order_batch(self, batch_id):
    """
    Process an order batch.

    :arg batch_id:
    :type batch_id: int
    """

    try:
        batch = models.Batch.objects.get(pk=batch_id)
    except models.Batch.DoesNotExist:
        logger.error('Could not find batch {}'.format(batch_id))
        raise
    header = []
    order = batch.order
    for order_item in batch.order_items.all():
        try:
            selected = order_item.selected_delivery_option
        except models.SelectedDeliveryOption.DoesNotExist:
            selected = order.selected_delivery_option
        if hasattr(selected.option, 'onlinedataaccess'):
            sig = process_online_data_access_item.subtask((order_item.id,))
        elif hasattr(selected.option, 'onlinedatadelivery'):
            sig = process_online_data_delivery_item.subtask((order_item.id,))
        elif hasattr(selected.option, 'mediadelivery'):
            sig = process_media_delivery_item.subtask((order_item.id,))
        else:
            raise
        header.append(sig)
    body = update_product_order_status.subtask((order.id,),
                                               immutable=True)
    c = chord(header, body)
    c.apply_async()


@shared_task(bind=True)
def process_online_data_access_item(self, order_item_id):
    """
    Process an order item that specifies online data access as delivery
    """

    order_item = models.OrderItem.objects.get(pk=order_item_id)
    order_item.status = models.CustomizableItem.IN_PRODUCTION
    order_item.additional_status_info = "Item is being processed"
    order_item.save()
    try:
        # for testing purposes only
        #if order_item.item_id == "item_01":
        #    raise IOError("Some fake error")
        order = order_item.batch.order
        processor, params = utilities.get_processor(
            order.order_type,
            models.ItemProcessor.PROCESSING_PROCESS_ITEM,
            logger_type="pyoseo"
        )
        options = order_item.export_options()
        delivery_options = order_item.export_delivery_options()
        urls, details = processor.process_item_online_access(
            order_item.identifier, order_item.item_id, order.id,
            order.user.user.username, options, delivery_options,
            domain=Site.objects.get_current().domain,
            **params)
        order_item.additional_status_info = details
        if any(urls):
            now = datetime.now(pytz.utc)
            expiry_date = now + timedelta(
                days=order.order_type.item_availability_days)
            order_item.status = models.CustomizableItem.COMPLETED
            order_item.completed_on = now
            for url in urls:
                f = models.OseoFile(url=url, available=True,
                                    order_item=order_item,
                                    expires_on=expiry_date)
                f.save()
        else:
            order_item.status = models.CustomizableItem.FAILED
            logger.error('THERE HAS BEEN AN ERROR: order item {} has '
                         'failed'.format(order_item_id))
    except Exception as e:
        order_item.status = models.CustomizableItem.FAILED
        order_item.additional_status_info = str(e)
        logger.error('THERE HAS BEEN AN ERROR: order item {} has failed '
                     'with the error: {}'.format(order_item_id, e))
    finally:
        order_item.save()


@shared_task(bind=True)
def process_online_data_delivery_item(self, order_item_id):
    """
    Process an order item that specifies online data delivery
    """

    raise NotImplementedError


@shared_task(bind=True)
def process_media_delivery_item(self, order_item_id):
    """
    Process an order item that specifies media delivery
    """

    raise NotImplementedError


@shared_task(bind=True)
def update_product_order_status(self, order_id):
    """
    Update the status of a normal order whenever the status of its batch
    changes

    :arg order_id:
    :type order_id: oseoserver.models.Order
    """

    order = models.ProductOrder.objects.get(pk=order_id)
    old_order_status = order.status
    batch = order.batches.get()  # ProductOrder's have only one batch
    if batch.status() == models.CustomizableItem.COMPLETED and \
                    order.packaging != '':
        try:
            _package_batch(batch, order.packaging)
        except Exception as e:
            order.status = models.CustomizableItem.FAILED
            order.additional_status_info = str(e)
            order.save()
            raise
    new_order_status = batch.status()
    if old_order_status != new_order_status or \
                    old_order_status == models.CustomizableItem.FAILED:
        order.status = new_order_status
        if new_order_status == models.CustomizableItem.COMPLETED:
            order.completed_on = dt.datetime.now(pytz.utc)
            order.additional_status_info = ""
        elif new_order_status == models.CustomizableItem.FAILED:
            msg = ""
            for oi in batch.order_items.all():
                if oi.status == models.CustomizableItem.FAILED:
                    additional = oi.additional_status_info
                    msg = "\n\t".join(
                        (
                            msg,
                             "* Order item {}: {}".format(oi.id,
                                                          additional)
                        ),
                    )
            order.additional_status_info = ("Order {} has "
                                            "failed.{}".format(order.id,
                                                               msg))
            utilities.send_order_failed_email(order, details=msg)
        order.save()


@shared_task(bind=True)
def delete_expired_order_items(self):
    """
    Go over all of the batches that have files that are available and
    delete the ones that have been expired.

    :return:
    """

    for ot in models.OrderType.objects.filter(enabled=True):
        logger.warn("Going over orders of type {}".format(ot.name))
        g = []
        for batch in models.Batch.objects.filter(order__order_type=ot).filter(
                order_items__files__available=True).distinct():
            g.append(delete_batch.subtask((batch.id,)))
        job = group(g)
        job.apply_async()


@shared_task(bind=True)
def delete_batch(self, batch_id, expired_files_only=True):
    """
    Delete all of the files associated with a batch

    :param batch_id:
    :return:
    """

    batch = models.Batch.objects.get(id=batch_id)
    if expired_files_only:
        to_delete = batch.expired_files()
    else:  # we can delete all of the batch's associated files
        to_delete = models.OseoFile.objects.filter(order_item__batch=batch)
    logger.info("to_delete: {}".format(to_delete))
    order_type = batch.order.order_type
    processor, params = utilities.get_processor(
        order_type,
        models.ItemProcessor.PROCESSING_CLEAN_ITEM,
        logger_type="pyoseo"
    )
    unique_urls = list(set([f.url for f in to_delete]))
    logger.info("unique_urls: {}".format(unique_urls))
    try:
        processor.clean_files(file_urls=unique_urls,
                              **params)
    except Exception as e:
        logger.error("there has been an error deleting "
                     "batch {} ".format(batch))
        utilities.send_cleaning_error_email(order_type, unique_urls,
                                            str(e))
    for oseo_file in to_delete:
        oseo_file.available = False
        oseo_file.save()


@shared_task(bind=True)
def delete_failed_orders(self):
    g = []
    for order in models.Order.objects.filter(
            status=models.CustomizableItem.FAILED):
        if order.order_type.name == models.Order.PRODUCT_ORDER:
            batch = order.batches.get()
            g.append(delete_batch.subtask((batch.id,),
                                          {"expired_files_only": False}))
        else:
            logger.warn("Deleting orders of type {} is not implemented "
                        "yet".format(order.order_type.name))
    job = group(g)
    job.apply_async()


def _package_batch(batch, compression):
    order_type = batch.order.order_type
    processor, params = utilities.get_processor(
        order_type,
        models.ItemProcessor.PROCESSING_PROCESS_ITEM,
        logger_type="pyoseo"
    )
    domain = Site.objects.get_current().domain
    files_to_package = []
    try:
        for item in batch.order_items.all():
            for oseo_file in item.files.all():
                files_to_package.append(oseo_file.url)
        packed = processor.package_files(compression, domain,
                                         file_urls=files_to_package,
                                         **params)
    except Exception as e:
        logger.error("there has been an error packaging the "
                     "batch {}: {}".format(batch, str(e)))
        utilities.send_batch_packaging_failed_email(batch, str(e))
        raise
    expiry_date = datetime.now(pytz.utc) + timedelta(
        days=order_type.item_availability_days)
    for item in batch.order_items.all():
        item.files.all().delete()
        f = models.OseoFile(url=packed, available=True, order_item=item,
                            expires_on=expiry_date)
        f.save()


@shared_task(bind=True)
def test_task(self):
    print('printing something from within a task')
    logger.debug('logging something from within a task with level: debug')
    logger.info('logging something from within a task with level: info')
    logger.warning('logging something from within a task with level: warning')
    logger.error('logging something from within a task with level: error')
