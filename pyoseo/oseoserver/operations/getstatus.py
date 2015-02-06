# Copyright 2015 Ricardo Garcia Silva
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
Implements the OSEO GetStatus operation
"""

import re
import datetime as dt

from django.core.exceptions import ObjectDoesNotExist
import pyxb
import pyxb.bundles.opengis.oseo_1_0 as oseo

from oseoserver import models
from oseoserver import errors
from oseoserver.operations.base import OseoOperation
from oseoserver.server import OseoServer


class GetStatus(OseoOperation):

    SUCCESS = "success"
    FULL_PRESENTATION = "full"

    def __call__(self, request, user, **kwargs):
        """
        Implements the OSEO Getstatus operation.

        See section 14 of the OSEO specification for details on the
        Getstatus operation.

        :arg request: The instance with the request parameters
        :type request: pyxb.bundles.opengis.raw.oseo.GetStatusRequestType
        :arg user: User making the request
        :type user: oseoserver.models.OseoUser
        :return: The XML response object and the HTTP status code
        :rtype: tuple(str, int)
        """

        status_code = 200
        records = []
        if request.orderId is not None:  # 'order retrieve' type of request
            try:
                order = models.Order.objects.get(id=int(request.orderId))
                if self._user_is_authorized(user, order):
                    records.append(order)
                else:
                    raise errors.OseoError('AuthorizationFailed',
                                           'The client is not authorized to '
                                           'call the operation',
                                           locator='orderId')
            except (models.Order.DoesNotExist, ValueError):
                raise errors.OseoError('InvalidOrderIdentifier',
                                       'Invalid value for order',
                                       locator=request.orderId)
        else:  # 'order search' type of request
            records = self._find_orders(request, user)
        response = self._generate_get_status_response(records,
                                                      request.presentation)
        return response, status_code, None

    def _generate_get_status_response(self, records, presentation):
        """
        :arg records:
        :type records: either a one element list with a pyoseo.models.Order
                       or a django queryset, that will be evaluated to an
                       list of pyoseo.models.Order while iterating.
        :arg presentation:
        :type presentation: str
        """

        response = oseo.GetStatusResponse()
        response.status = self.SUCCESS
        for r in records:
            om = oseo.CommonOrderMonitorSpecification()
            if r.order_type.name == models.Order.MASSIVE_ORDER:
                om.orderType = models.OrderType.PRODUCT_ORDER
                om.orderReference = OseoServer.MASSIVE_ORDER_REFERENCE
            else:
                om.orderType = r.order_type.name
                om.orderReference = self._n(r.reference)
            om.orderId = str(r.id)
            om.orderStatusInfo = oseo.StatusType(
                status=r.status,
                additionalStatusInfo=self._n(r.additional_status_info),
                missionSpecificStatusInfo=self._n(
                    r.mission_specific_status_info)
            )
            om.orderDateTime = r.status_changed_on
            om.orderRemark = self._n(r.remark)
            try:
                del_info = oseo.DeliveryInformationType()
                optional_attrs = [
                    r.delivery_information.first_name,
                    r.delivery_information.last_name,
                    r.delivery_information.company_ref,
                    r.delivery_information.street_address,
                    r.delivery_information.city,
                    r.delivery_information.state,
                    r.delivery_information.postal_code,
                    r.delivery_information.country,
                    r.delivery_information.post_box,
                    r.delivery_information.telephone,
                    r.delivery_information.fax
                ]
                if any(optional_attrs):
                    del_info.mailAddress = oseo.DeliveryAddressType()
                    del_info.mailAddress.firstName = self._n(
                            r.delivery_information.first_name)
                    del_info.mailAddress.lastName = self._n(
                            r.delivery_information.last_name)
                    del_info.mailAddress.companyRef = self._n(
                            r.delivery_information.company_ref)
                    del_info.mailAddress.postalAddress = pyxb.BIND()
                    del_info.mailAddress.postalAddress.streetAddress = self._n(
                            r.delivery_information.street_address)
                    del_info.mailAddress.postalAddress.city = self._n(
                            r.delivery_information.city)
                    del_info.mailAddress.postalAddress.state = self._n(
                            r.delivery_information.state)
                    del_info.mailAddress.postalAddress.postalCode = self._n(
                            r.delivery_information.postal_code)
                    del_info.mailAddress.postalAddress.country = self._n(
                            r.delivery_information.country)
                    del_info.mailAddress.postalAddress.postBox = self._n(
                            r.delivery_information.post_box)
                    del_info.mailAddress.telephoneNumber = self._n(
                            r.delivery_information.telephone)
                    del_info.mailAddress.facsimileTelephoneNumber = self._n(
                            r.delivery_information.fax)
                for oa in r.delivery_information.onlineaddress_set.all():
                    del_info.onlineAddress.append(
                            oseo.OnlineAddressType())
                    del_info.onlineAddress[-1].protocol = oa.protocol
                    del_info.onlineAddress[-1].serverAddress = oa.server_address
                    del_info.onlineAddress[-1].userName = self._n(
                            oa.user_name)
                    del_info.onlineAddress[-1].userPassword = self._n(
                            oa.user_password)
                    del_info.onlineAddress[-1].path = self._n(oa.path)
                om.deliveryInformation = del_info
            except models.DeliveryInformation.DoesNotExist:
                pass
            try:
                inv_add = oseo.DeliveryAddressType()
                inv_add.firstName = self._n(r.invoice_address.first_name)
                inv_add.lastName = self._n(r.invoice_address.last_name)
                inv_add.companyRef = self._n(r.invoice_address.company_ref)
                inv_add.postalAddress=pyxb.BIND()
                inv_add.postalAddress.streetAddress = self._n(
                        r.invoice_address.street_address)
                inv_add.postalAddress.city = self._n(r.invoice_address.city)
                inv_add.postalAddress.state = self._n(r.invoice_address.state)
                inv_add.postalAddress.postalCode = self._n(
                        r.invoice_address.postal_code)
                inv_add.postalAddress.country = self._n(
                        r.invoice_address.country)
                inv_add.postalAddress.postBox = self._n(
                        r.invoice_address.post_box)
                inv_add.telephoneNumber = self._n(
                        r.invoice_address.telephone)
                inv_add.facsimileTelephoneNumber = self._n(
                        r.invoice_address.fax)
                om.invoiceAddress = inv_add
            except models.InvoiceAddress.DoesNotExist:
                pass
            om.packaging = self._n(r.packaging)
            # add any 'option' elements
            om.deliveryOptions = self._get_delivery_options(r)
            om.priority = self._n(r.priority)
            if presentation == self.FULL_PRESENTATION:
                if r.order_type.name == models.Order.PRODUCT_ORDER:
                    batch = r.batches.get()
                    for oi in batch.order_items.all():
                        sit = oseo.CommonOrderStatusItemType()
                        # TODO - add the other optional elements
                        sit.itemId = str(oi.item_id)
                        # oi.identifier is guaranteed to be non empty for
                        # normal product orders
                        sit.productId = oi.identifier
                        sit.productOrderOptionsId = "Options for {} {}".format(
                            oi.collection.name, r.order_type.name)
                        sit.orderItemRemark = self._n(oi.remark)
                        sit.collectionId = self._n(oi.collection_id)
                        # add any 'option' elements that may be present
                        # add any 'sceneSelection' elements that may be present
                        sit.deliveryOptions = self._get_delivery_options(oi)
                        # add any 'payment' elements that may be present
                        # add any 'extension' elements that may be present
                        sit.orderItemStatusInfo = oseo.StatusType()
                        sit.orderItemStatusInfo.status = oi.status
                        sit.orderItemStatusInfo.additionalStatusInfo = \
                                self._n(oi.additional_status_info)
                        sit.orderItemStatusInfo.missionSpecificStatusInfo=\
                                self._n(oi.mission_specific_status_info)
                        om.orderItem.append(sit)
                else:
                    raise NotImplementedError
            response.orderMonitorSpecification.append(om)
        return response

    def _find_orders(self, request, user):
        """
        Find orders that match the request's filtering criteria
        """

        records = models.Order.objects.filter(user=user)
        if request.filteringCriteria.lastUpdate is not None:
            lu = request.filteringCriteria.lastUpdate
            records = records.filter(status_changed_on__gte=lu)
        if request.filteringCriteria.lastUpdateEnd is not None:
            # workaround for a bug in the oseo.xsd that does not
            # assign a dateTime type to the lastUpdateEnd element
            lue = request.filteringCriteria.lastUpdateEnd.toxml()
            m = re.search(r'\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}Z)?', lue)
            try:
                ts = dt.datetime.strptime(m.group(), '%Y-%m-%dT%H:%M:%SZ')
            except ValueError:
                ts = dt.datetime.strptime(m.group(), '%Y-%m-%d')
            records = records.filter(status_changed_on__lte=ts)
        if request.filteringCriteria.orderReference is not None:
            ref = request.filteringCriteria.orderReference
            records = records.filter(reference=ref)
        statuses = [s for s in request.filteringCriteria.orderStatus]
        if any(statuses):
            records = records.filter(status__in=statuses)
        return records

    def _get_delivery_options(self, db_item):
        """
        Return the delivery options for an input database item.

        :arg db_item: the database record model that has the delivery options
        :type db_item: pyoseo.models.CustomizableItem
        :return: A pyxb object with the delivery options
        """

        try:
            do = db_item.selected_delivery_option
            dot = oseo.DeliveryOptionsType()
            try:
                oda = do.option.onlinedataaccess
                dot.onlineDataAccess = pyxb.BIND()
                dot.onlineDataAccess.protocol = oda.protocol
            except models.OnlineDataAccess.DoesNotExist:
                try:
                    odd = do.option.onlinedatadelivery
                    dot.onlineDataDelivery = pyxb.BIND()
                    dot.onlineDataDelivery.protocol = odd.protocol
                except models.OnlineDataDelivery.DoesNotExist:
                    md = do.option.mediadelivery
                    dot.mediaDelivery = pyxb.BIND()
                    dot.mediaDelivery.packageMedium = md.package_medium
                    dot.mediaDelivery.shippingInstructions = self._n(
                        md.shipping_instructions)
            dot.numberOfCopies = self._n(do.copies)
            dot.productAnnotation = self._n(do.annotation)
            dot.specialInstructions = self._n(do.special_instructions)
        except models.SelectedDeliveryOption.DoesNotExist:
            dot = None
        return dot

