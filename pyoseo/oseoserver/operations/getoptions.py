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
Implements the OSEO GetOptions operation
"""

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
import pyxb
import pyxb.bundles.opengis.oseo_1_0 as oseo
import pyxb.bundles.opengis.swe_2_0 as swe

from oseoserver import models
from oseoserver import errors
from oseoserver.operations.base import OseoOperation

class GetOptions(OseoOperation):

    def __call__(self, request, user, **kwargs):
        """
        Implements the OSEO GetOptions operation.


        :arg request: The instance with the request parameters
        :type request: pyxb.bundles.opengis.raw.oseo.OrderOptionsRequestType
        :arg user: User making the request
        :type user: oseoserver.models.OseoUser
        :return: The XML response object and the HTTP status code
        :rtype: tuple(str, int)

        Example for creating an option with pyxb:

        from lxml import etree
        import pyxb
        import pyxb.bundles.opengis.swe_2_0 as swe
        at = swe.AllowedTokens()
        at.value_.append('ATS_NL_0P')
        at.value_.append('ATS_TOA_1P')
        c = swe.Category(updatable=False)
        c.optional = True
        c.definition = 'http://www.opengis.net/def/parameter/ESA/1.0/productType'
        c.identifier = 'ProductType'
        c.description = 'Processing for ENVISAT ATS'
        c.constraint = pyxb.BIND()
        c.constraint.append(at)
        dr = swe.DataRecord()
        dr.field.append(pyxb.BIND())
        dr.field[0].name = 'ProductType'
        dr.field[0].append(c)
        print(etree.tostring(etree.fromstring(dr.toxml()), encoding='utf-8', pretty_print=True))
        """

        status_code = 200
        if any(request.identifier):  # product identifier query
            raise NotImplementedError
        elif request.collectionId is not None:  # product or collection query
            try:
                p = models.Product.objects.get(
                        collection_id=request.collectionId)
                response = oseo.GetOptionsResponse(status='success')
                # get the options that are available for the requested
                # collection and which available for each type of order
                # this includes options that are specific to each collection
                # as well as options that are applicable to every collection
                for ot in (models.OrderType.PRODUCT_ORDER,
                           models.OrderType.SUBSCRIPTION_ORDER):
                    available_options = self.get_applicable_options(
                        request.collectionId,
                        ot
                    )
                    av_delivery_opts = models.DeliveryOption.objects.filter(
                        deliveryoptionordertype__order_type__name=ot
                    )
                    for group in models.OptionGroup.objects.all():
                        order_opts = self._get_order_options(
                            group,
                            available_options,
                            av_delivery_opts,
                            ot
                        )
                        response.orderOptions.append(order_opts)
            except ObjectDoesNotExist:
                raise errors.OseoError('UnsupportedCollection',
                                       'Subscription not supported',
                                       locator=request.collectionId)
        elif request.taskingRequestId is not None:
            raise NotImplementedError
        return response, status_code

    def get_applicable_options(self, collection_id, request_type):

        options = models.Option.objects.filter(
            Q(product__collection_id=collection_id) |
            Q(product=None)
        ).filter(optionordertype__order_type__name=request_type)
        return options

    def _get_order_options(self, option_group, options, delivery_options,
                           order_type, order_item=None):
        """
        :arg option_group:
        :type option_group:
        :arg options:
        :type options: A list of models.Option objects
        :arg delivery_options:
        :type delivery_options: A list of models.DeliveryOption objects
        :arg order_type: The type of order, which can be one of the types
                         defined in the models.OrderType class
        :type order_type: string
        :arg order_item:
        :type order_item:
        :return: The pyxb oseo.CommonOrderOptionsType
        """

        c = oseo.CommonOrderOptionsType()
        c.productOrderOptionsId = option_group.name
        if order_item is not None:
            c.identifier = order_item.identifier
        c.description = self._n(option_group.description)
        c.orderType = order_type
        for option in options:
            dr = swe.DataRecord()
            dr.field.append(pyxb.BIND())
            dr.field[0].name = option.name
            cat = swe.Category(updatable=False)
            cat.optional = True
            #cat.definition = 'http://geoland2.meteo.pt/ordering/def/%s' % \
            #        option.name
            #cat.identifier = option.name
            #cat.description = self._n(option.description)
            choices = option.choices.all()
            if any(choices):
                cat.constraint = pyxb.BIND()
                at = swe.AllowedTokens()
                for choice in choices:
                    at.value_.append(choice.value)
                cat.constraint.append(at)
            dr.field[0].append(cat)
            c.option.append(pyxb.BIND())
            c.option[-1].AbstractDataComponent = dr
            #c.option[-1].grouping = 'teste'
        online_data_access_opts = [d for d in delivery_options if \
                hasattr(d, 'onlinedataaccess')]
        online_data_delivery_opts = [d for d in delivery_options if \
                hasattr(d, 'onlinedatadelivery')]
        media_delivery_opts = [d for d in delivery_options if \
                hasattr(d, 'mediadelivery')]
        if any(online_data_access_opts):
            c.productDeliveryOptions.append(pyxb.BIND())
            i = len(c.productDeliveryOptions) - 1
            c.productDeliveryOptions[i].onlineDataAccess = pyxb.BIND()
            for opt in online_data_access_opts:
                c.productDeliveryOptions[i].onlineDataAccess.protocol.append(
                        opt.onlinedataaccess.protocol)
        if any(online_data_delivery_opts):
            c.productDeliveryOptions.append(pyxb.BIND())
            i = len(c.productDeliveryOptions) - 1
            c.productDeliveryOptions[i].onlineDataDelivery = pyxb.BIND()
            for opt in online_data_delivery_opts:
                c.productDeliveryOptions[i].onlineDataDelivery.protocol.append(
                        opt.onlinedatadelivery.protocol)
        if any(media_delivery_opts):
            c.productDeliveryOptions.append(pyxb.BIND())
            i = len(c.productDeliveryOptions) - 1
            c.productDeliveryOptions[i].mediaDelivery = pyxb.BIND()
            for opt in media_delivery_opts:
                c.productDeliveryOptions[i].mediaDelivery.packageMedium.append(
                        opt.mediadelivery.package_medium)
        # add orderOptionInfoURL
        # add paymentOptions
        # add sceneSelecetionOptions
        return c
