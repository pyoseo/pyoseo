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
Base classes for the OSEO operations
"""

from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings as django_settings
import pyxb
import pyxb.bundles.opengis.oseo_1_0 as oseo
import pyxb.bundles.opengis.csw_2_0_2 as csw

from oseoserver import models
from oseoserver import server

class OseoOperation(object):
    """
    This is the base class for OSEO operations.

    It should not be instantiated directly
    """

    NAME = None  # to be reimplemented in child classes

    def _get_collection_id(self, item_id, user_group):
        """
        Search all of the defined catalogue endpoints and determine
        the collection for the specified item.

        :param item_id:
        :type item_id: string
        :param user_group:
        :type user_group: models.OseoGroup
        :return:
        """

        endpoints = set([c.catalogue_endpoint for c in
                        models.Collection.objects.filter(
                        authorized_groups=user_group)])
        get_records_by_id_request = csw.GetRecordById(
            service="CSW",
            version="2.0.2",
            ElementSetName="summary",
            outputSchema=server.OseoServer._namespaces["gmd"]
        )
        get_records_by_id_request.Id.append(pyxb.BIND(item_id))
        for url in endpoints:
            pass


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
                oda = do.group_delivery_option.delivery_option.onlinedataaccess
                dot.onlineDataAccess = pyxb.BIND()
                dot.onlineDataAccess.protocol = oda.protocol
            except ObjectDoesNotExist:
                try:
                    odd = do.group_delivery_option.delivery_option.onlinedatadelivery
                    dot.onlineDataDelivery = pyxb.BIND()
                    dot.onlineDataDelivery.protocol = odd.protocol
                except ObjectDoesNotExist:
                    md = do.group_delivery_option.delivery_option.mediadelivery
                    dot.mediaDelivery = pyxb.BIND()
                    dot.mediaDelivery.packageMedium = md.package_medium
                    dot.mediaDelivery.shippingInstructions = self._n(
                            md.shipping_instructions)
            dot.numberOfCopies = self._n(do.copies)
            dot.productAnnotation = self._n(do.annotation)
            dot.specialInstructions = self._n(do.special_instructions)
        except ObjectDoesNotExist:
            dot = None
        return dot

    def _order_type_enabled(self, order_type):
        """
        Return a boolean indicating if the specified order type is enabled in
        the settings.
        """
        order_type_enabled = models.OrderType.objects.filter(name=order_type)
        return True if len(order_type_enabled) > 0 else False

    def _option_enabled(self, option, customizable_item):
        """
        Return a boolean indicating if the specified option is enabled.
        """

        result = False
        for group_option in customizable_item.option_group.groupoption_set.all():
            op = group_option.option
            if op.name == option:
                for op_order_type in op.optionordertype_set.all():
                    try:
                        t = customizable_item.order.order_type
                    except customizable_item.DoesNotExist:
                        # the input customizable_item is probably an order item
                        t = customizable_item.orderitem.batch.order.order_type
                    if op_order_type.order_type == t:
                        result = True
        return result

    def _c(self, value):
        """
        Convert between a None and an empty string.

        This function translates pyxb's empty elements, which are stored as
        None into django's empty values, which are stored as an empty string.
        """

        return '' if value is None else str(value)

    def _n(self, value):
        """
        Convert between an empty string and a None

        This function is translates django's empty elements, which are stored
        as empty strings into pyxb empty elements, which are stored as None.
        """

        return None if value == '' else value
