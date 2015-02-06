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
Implements the OSEO DescribeResultAccess operation
"""

import os
import logging
import datetime as dt

from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.conf import settings as django_settings
import pyxb
import pyxb.bundles.opengis.oseo_1_0 as oseo

from oseoserver import models
from oseoserver import errors
from oseoserver.operations.base import OseoOperation

logger = logging.getLogger('.'.join(('pyoseo', __name__)))

class DescribeResultAccess(OseoOperation):

    # subFunction values for DescribeResultAccess operation
    ALL_READY = 'allReady'
    NEXT_READY = 'nextReady'

    def __call__(self, request, user, **kwargs):
        """
        Implements the OSEO DescribeResultAccess operation.

        This operation returns the location of the order items that are 
        ready to be downloaded by the user.

        The DescribeResultAccess operation only reports on the availability
        of order items that specify onlineDataAccess as their delivery option.

        :arg request: The instance with the request parameters
        :type request: pyxb.bundles.opengis.raw.oseo.OrderOptionsRequestType
        :arg user: User making the request
        :type user: oseoserver.models.OseoUser
        :arg user_password: Password of the user making the request
        :type user_password: str
        :return: The DescribeResultAccess response object and the HTTP status
                 code
        :rtype: tuple(pyxb.bundles.opengis.oseo.DescribeResultAccessResponse,
                int)
        """

        status_code = 200
        try:
            order = models.Order.objects.get(id=request.orderId)
        except ObjectDoesNotExist:
            raise errors.OseoError('InvalidOrderIdentifier',
                                   'Invalid value for order',
                                   locator=request.orderId)
        if not self._user_is_authorized(user, order):
            raise errors.OseoError('AuthorizationFailed',
                                   'The client is not authorized to '
                                   'call the operation',
                                   locator='orderId')
        if order.order_type.name == models.Order.PRODUCT_ORDER:
            completed_files = self.get_product_order_completed_files(
                order, request.subFunction)
        else:
            raise NotImplementedError
        logger.info('completed_files: {}'.format(completed_files))
        order.last_describe_result_access_request = dt.datetime.utcnow()
        order.save()
        response = oseo.DescribeResultAccessResponse(status='success')

        item_id = None
        if len(completed_files) == 1 and order.packaging == models.Order.ZIP:
            item_id = "Packaged order items"
        for oseo_file, delivery in completed_files:
            item = oseo_file.order_item
            iut = oseo.ItemURLType()
            iut.itemId = item_id if item_id is not None else item.item_id
            iut.productId = oseo.ProductIdType(
                identifier=item.identifier,
                )
            iut.productId.collectionId = item.collection.collection_id
            iut.itemAddress = oseo.OnLineAccessAddressType()
            iut.itemAddress.ResourceAddress = pyxb.BIND()
            iut.itemAddress.ResourceAddress.URL = oseo_file.url
            iut.expirationDate = oseo_file.expires_on
            response.URLs.append(iut)
        return response, status_code, None

    def get_product_order_completed_files(self, order, behaviour):
        """
        Get the completed files for product orders.

        :arg order:
        :type order: oseoserver.models.Order
        :arg behaviour: Either 'allReady' or 'nextReady', as defined in the 
                        OSEO specification
        :type behaviour: str
        :return: a list with the completed order items for this order
        :rtype: [(models.OseoFile, models.DeliveryOption)]
        """


        last_time = order.last_describe_result_access_request
        order_delivery = order.selected_delivery_option.option
        batch = order.batches.get()  # ProductOrder has a single batch
        batch_status = batch.status()
        completed = []
        if batch_status != models.CustomizableItem.COMPLETED:
            # batch is either still being processed,
            # failed or already downloaded, so we don't care for it
            pass
        else:
            batch_complete_items = []
            order_items = batch.order_items.all()
            for oi in order_items:
                try:
                    delivery = oi.selected_delivery_option.option
                except models.SelectedDeliveryOption.DoesNotExist:
                    delivery = order_delivery
                if not hasattr(delivery, "onlinedataaccess"):
                    # getStatus only applies to items with onlinedataaccess
                    continue
                if oi.status == models.CustomizableItem.COMPLETED:
                    if (last_time is None or behaviour == self.ALL_READY) or \
                            (behaviour == self.NEXT_READY and
                                     oi.completed_on >= last_time):
                        for f in oi.files.filter(available=True):
                            batch_complete_items.append((f, delivery))
            if order.packaging == models.Order.ZIP:
                if len(batch_complete_items) == len(order_items):
                    # the zip is ready, lets get only a single file
                    # because they all point to the same URL
                    completed.append(batch_complete_items[0])
                else:  # the zip is not ready yet
                    pass
            else:  # lets get each file that is complete
                completed = batch_complete_items
        return completed

