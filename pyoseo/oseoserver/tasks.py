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

import os
import re
import shutil
import datetime as dt

import pytz
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.conf import settings as django_settings
from celery import shared_task
from celery import group, chord
from celery.utils.log import get_task_logger

from oseoserver import models
from oseoserver import utilities

logger = get_task_logger(__name__)


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
        order.save()
    except models.ProductOrder.DoesNotExist:
        logger.error('could not find order {}'.format(order_id))
        raise
    g = []
    for batch in order.batches.all():
        sig = process_batch.subtask((batch.id,))
        g.append(sig)
    job = group(g)
    job.apply_async()


@shared_task(bind=True)
def process_batch(self, batch_id):
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
    for order_item in batch.order_items.all():
        try:
            selected = order_item.selected_delivery_option
        except models.SelectedDeliveryOption.DoesNotExist:
            selected = order_item.batch.order.selected_delivery_option
        if hasattr(selected.option, 'onlinedataaccess'):
            sig = process_online_data_access_item.subtask(
                (order_item.id, selected.id)
            )
        elif hasattr(selected.option, 'onlinedatadelivery'):
            sig = process_online_data_delivery_item.subtask(
                (order_item.id, selected.id)
            )
        elif hasattr(selected.option, 'mediadelivery'):
            sig = process_media_delivery_item.subtask(
                (order_item.id, selected.id)
            )
        else:
            raise
        header.append(sig)
    body = update_order_status.subtask((batch.order.id,), immutable=True)
    c = chord(header, body)
    c.apply_async()


@shared_task(bind=True)
def process_online_data_access_item(self, order_item_id,
                                    selected_delivery_option_id):
    """
    Process an order item that specifies online data access as delivery
    """

    print("SELECTED_DELIVERY_OPTION_ID: {}".format(selected_delivery_option_id))

    order_item = models.OrderItem.objects.get(pk=order_item_id)
    logger.debug('Retrieved order item from the database: {}'.format(
                 order_item))
    order_item.status = models.CustomizableItem.IN_PRODUCTION
    order_item.save()
    logger.debug('Changed the order_item status to {}'.format(
                 models.CustomizableItem.IN_PRODUCTION))
    try:
        selected_delivery_option = models.SelectedDeliveryOption.objects.get(
            pk=selected_delivery_option_id)
        protocol = selected_delivery_option.option.onlinedataaccess.protocol
        protocol_path_map = {
            models.OnlineDataAccess.HTTP: "OSEOSERVER_ONLINE_DATA_ACCESS_"
                                          "HTTP_PROTOCOL_ROOT_DIR",
            models.OnlineDataAccess.FTP: "OSEOSERVER_ONLINE_DATA_ACCESS_"
                                         "FTP_PROTOCOL_ROOT_DIR",
        }
        protocol_root_dir = getattr(
            django_settings,
            protocol_path_map.get(protocol, ''),
        )
        item_identifier = order_item.identifier
        order = order_item.batch.order
        user_name = order.user.user.username
        processing_class = order_item.collection.item_preparation_class
        logger.debug('processing_class: {}'.format(processing_class))
        processor = utilities.import_class(processing_class, under_celery=True)
        logger.debug('processor: {}'.format(processor))
        options = order_item.export_options()
        delivery_options = order_item.export_delivery_options()
        items, details = processor.process_item_online_access(item_identifier,
                                                              order.id,
                                                              user_name,
                                                              order.packaging,
                                                              options,
                                                              delivery_options)
        order_item.additional_status_info = details
        if any(items):
            order_item.status = models.CustomizableItem.COMPLETED
            order_item.completed_on = dt.datetime.now(pytz.utc)
            for i in items:
                f = models.OseoFile(name=os.path.basename(i),
                                    available=True,
                                    order_item=order_item)
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
def process_online_data_delivery_item(self, order_item_id, delivery_option_id):
    """
    Process an order item that specifies online data delivery
    """

    raise NotImplementedError


@shared_task(bind=True)
def process_media_delivery_item(self, order_item_id, delivery_option_id):
    """
    Process an order item that specifies media delivery
    """

    raise NotImplementedError


@shared_task(bind=True)
def update_order_status(self, order_id):
    """
    Update the status of a normal order whenever the status of its batch
    changes

    :arg order_id:
    :type order_id: oseoserver.models.Order
    """

    order = models.Order.objects.get(pk=order_id)
    if order.order_type.name == models.Order.PRODUCT_ORDER:
        old_order_status = order.status
        batch = order.batches.get()  # ProductOrder's have only one batch
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
def monitor_ftp_downloads(self):
    """
    Monitor FTP downloads

    This function will parse an xferlog file from the FTP server.
    Read more about xferlog file format by typing `man xferlog` at a
    terminal.

    The way this function should be run is by adding it in the
    :data:`~pyoseo.settings.CELERYBEAT_SCHEDULE` setting so that it 
    runs once per day. It will try to analyze the log file from the previous 
    day, in order to not miss any downloads. This implies that the FTP 
    server's logs are always rotated on a daily basis, even if they are empty.
    As such, the logrotate daemon should be properly configured, as indicated 
    in the :ref:`proftpd-installation-label` installation instructions.
    """

    ftp_log_file = '/var/log/proftpd/xferlog.1' # analyzing previous day log
    #ftp_log_file = '/var/log/proftpd/xferlog'
    try:
        with open(ftp_log_file) as fh:
            for line in fh:
                order_item, download_dt = parse_ftp_log_line(line)
                if order_item is not None:
                    order_item.downloads += 1
                    order_item.status = models.CustomizableItem.DOWNLOADED
                    order_item.save()
    except IOError:
        pass # the log file does not exist


# TODO
# this task can be generalized and executed as smaller tasks
@shared_task(bind=True)
def delete_old_orders(self):
    """
    Find completed orders that are lying around past their time.

    This task should run once per day by being added to the 
    :data:`~pyoseo.settings.CELERYBEAT_SCHEDULE` setting.

    Orders that have been completed will remain on the server for an ammount of
    days specified by the 
    :data:`~pyoseo.settings.OSEOSERVER_ORDER_DELETION_THRESHOLD` setting.
    Once this threshold is passed, an order becomes elligible for deletion.
    """

    ftp_root = getattr(
        django_settings,
        'OSEOSERVER_ONLINE_DATA_ACCESS_FTP_PROTOCOL_ROOT_DIR',
        None
    )
    deletion_threshold = getattr(
        django_settings,
        'OSEOSERVER_ORDER_DELETION_THRESHOLD',
        None
    )
    for user in (u for u in os.listdir(ftp_root) if not u.startswith('.')):
        logger.warn('Analyzing user {}'.format(user))
        user_root = os.path.join(ftp_root, user)
        for order_exp in (i for i in os.listdir(user_root)):
            order_root = os.path.join(user_root, order_exp)
            try:
                order_id = int(re.search(r'order_(?P<id>\d+)',
                               order_exp).groupdict()['id'])
                order = models.Order.objects.get(pk=order_id)
                completed_on = order.completed_on
                today = dt.datetime.now(pytz.utc)
                delta = (today - completed_on).days
                if (deletion_threshold is not None) and \
                        (delta > deletion_threshold):
                    logger.warn('Order {} has been completed for more than {} '
                                'days. Deleting order items...'.format(
                                order_id, deletion_threshold))
                    shutil.rmtree(order_root, ignore_errors=True)
                else:
                    logger.warn('Order {} has not passed the {} day '
                                'threshold yet'.format(order_id,
                                deletion_threshold))
            except TypeError:
                # (dt.datetime - None) raises TypeError
                # it means the order is not complete yet
                pass
            except (ObjectDoesNotExist, AttributeError) as err:
                logger.warn(err)


def parse_ftp_log_line(line):
    """
    Parse a line of the FTP transfer log file looking for downloaded items.

    :arg line: One of the lines of the FTP's server transfer log
    :type line: str
    :returns: the order item being requested in the line and the time when 
              the download was performed
    :rtype: (oseoserver.models.OrderItem, datetime.datetime)
    """

    # Do not uncomment this line except for debugging purposes, as it
    # produces a lot of output
    #logger.debug('line: {}'.format(line))
    ftp_root = getattr(
        django_settings,
        'OSEOSERVER_ONLINE_DATA_ACCESS_FTP_PROTOCOL_ROOT_DIR',
        None
    )
    info = line.rsplit(' ', 13)
    file_name = info[4]
    direction = info[7]
    completion_status = info[13]
    is_pyoseo_transfer = file_name.startswith(ftp_root)
    is_outgoing = True if direction == 'o' else False
    is_completed = True if completion_status.strip() == 'c' else False
    result = None, None
    if is_pyoseo_transfer and is_outgoing and is_completed:
        print('this is a pyoseo transfer')
        sub_path = file_name.partition(ftp_root)[-1][1:]
        ftp_user, order_id, file_name = sub_path.split('/')
        try:
            order = int(re.search(r'order_(?P<id>\d+)', 
                        order_id).groupdict()['id'])
        except AttributeError:
            order = None
        current_time = dt.datetime.strptime(info[0],
                                            '%a %b %d %H:%M:%S %Y')
        current_time = pytz.timezone('UTC').localize(current_time)
        try:
            oi = models.OrderItem.objects.get(batch__order__pk=order,
                                              file_name=file_name)
        except (ObjectDoesNotExist, MultipleObjectsReturned) as err:
            logger.warning(err)
            oi = None
        result = oi, current_time
    return result


@shared_task(bind=True)
def test_task(self):
    print('printing something from within a task')
    logger.debug('logging something from within a task with level: debug')
    logger.info('logging something from within a task with level: info')
    logger.warning('logging something from within a task with level: warning')
    logger.error('logging something from within a task with level: error')
    processing_class = getattr(django_settings,
                               'OSEOSERVER_PROCESSING_CLASS')
    logger.debug('processing_class: {}'.format(processing_class))
    p = utilities.import_class(processing_class, under_celery=True)
    logger.debug('p: {}'.format(p))
    try:
        raise ValueError('Error raised on purpose')
    except ValueError as err:
        logger.error(err)
        utilities.send_mail_to_admins(str(err))

