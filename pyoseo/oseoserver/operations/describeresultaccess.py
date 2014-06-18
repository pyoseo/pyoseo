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
Implements the OSEO DescribeResultAccess operation
'''

import logging
import datetime as dt
import socket

from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
import pyxb
import pyxb.bundles.opengis.oseo as oseo

from oseoserver import models
from oseoserver import errors
from oseoserver import views
from oseoserver.operations.base import OseoOperation

logger = logging.getLogger('.'.join(('pyoseo', __name__)))

class DescribeResultAccess(OseoOperation):

    # subFunction values for DescribeResultAccess operation
    ALL_READY = 'allReady'
    NEXT_READY = 'nextReady'

    def __call__(self, request, user, user_password=None, **kwargs):
        '''
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
        '''

        status_code = 200
        try:
            order = models.Order.objects.get(id=request.orderId)
        except ObjectDoesNotExist:
            raise errors.OseoError('InvalidOrderIdentifier',
                                   'Invalid value for order',
                                   locator=request.orderId)
        if order.user != user:
            raise errors.OseoError('AuthorizationFailed', 'The client is not '
                                   'authorized to call the operation',
                                   locator=request.orderId)
        completed_items = self._get_completed_items(order,
                                                    request.subFunction)
        logger.info('completed_items: %s' % completed_items)
        order.last_describe_result_access_request = dt.datetime.utcnow()
        order.save()
        response = oseo.DescribeResultAccessResponse(status='success')
        for i in completed_items:
            try:
                gdo = i.selected_delivery_option.group_delivery_option
            except ObjectDoesNotExist:
                try:
                    gdo = order.selected_delivery_option.group_delivery_option
                except ObjectDoesNotExist:
                    pass # this object does not specify onlineDataAccess
            try:
                protocol = gdo.delivery_option.onlinedataaccess.protocol
                iut = oseo.ItemURLType()
                iut.itemId = i.item_id
                iut.productId = oseo.ProductIdType(
                    identifier=i.identifier,
                )
                if i.collection_id is not None:
                    iut.productId.collectionId = self._n(i.collection_id)
                iut.itemAddress = oseo.OnLineAccessAddressType()
                iut.itemAddress.ResourceAddress = pyxb.BIND()
                iut.itemAddress.ResourceAddress.URL = self.get_url(
                    protocol,
                    i,
                    user.user.username,
                    user_password
                )
                response.URLs.append(iut)
            except ObjectDoesNotExist:
                pass
        return response, status_code

    def _get_completed_items(self, order, behaviour):
        '''
        :arg order:
        :type order: oseoserver.models.Order
        :arg behaviour: Either 'allReady' or 'nextReady', as defined in the 
                        OSEO specification
        :type behaviour: str
        :return: a list with the completed order items for this order
        '''

        now = dt.datetime.utcnow()
        last_time = order.last_describe_result_access_request
        completed_items = []
        for batch in order.batches.all():
            for order_item in batch.order_items.all():
                if order_item.status == models.CustomizableItem.COMPLETED:
                    if last_time is None or behaviour == self.ALL_READY:
                        completed_items.append(order_item)
                    elif behaviour == self.NEXT_READY and \
                            order_item.completed_on >= last_time:
                        completed_items.append(order_item)
        return completed_items

    def get_url(self, protocol, order_item, user_name, user_password):
        '''
        Return the URL where the order item is available for online access.

        :arg protocol:
        :type protocol: str
        :arg order_item:
        :type order_item:
        :arg user: User that made the order
        :type user: oseoserver.models.OseoUser
        :arg user_name:
        :type user_name: str
        '''

        host_name = socket.gethostname()
        if protocol == models.OnlineDataAccess.HTTP:
            uri = reverse(views.show_item, args=(user_name,
                          order_item.batch.order.id, order_item.file_name))
            url = ''.join(('http://', host_name, uri))
        elif protocol == models.OnlineDataAccess.FTP:
            url_template = 'ftp://{user}@{host}/order_{order:02d}/{file}'
            url = url_template.format(user=user_name, password=user_password,
                                      host=host_name,
                                      order=order_item.batch.order.id,
                                      file=order_item.file_name)
        else:
            raise NotImplementedError
        return url
