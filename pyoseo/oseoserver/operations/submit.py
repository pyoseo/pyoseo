# Copyright 2014 Ricardo Garcia Silva
#
# Licensed under the Apache License, Version 2.0 (the "License");
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
Implements the OSEO Submit operation
"""

import os
import stat
import logging

from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings as django_settings
from pyxb import BIND
import pyxb.bundles.opengis.oseo_1_0 as oseo
import pyxb.bundles.opengis.csw_2_0_2 as csw
import pyxb.bundles.opengis.iso19139.v20070417.gmd as gmd
import pyxb.bundles.opengis.iso19139.v20070417.gco as gco
from lxml import etree
import requests

from oseoserver import models
from oseoserver import errors
from oseoserver import utilities
from oseoserver.server import OseoServer
from oseoserver.operations.base import OseoOperation

logger = logging.getLogger('.'.join(('pyoseo', __name__)))


class Submit(OseoOperation):

    @transaction.atomic
    def __call__(self, request, user):
        """
        Implements the OSEO Submit operation.

        :arg request: The instance with the request parameters
        :type request: pyxb.bundles.opengis.raw.oseo.GetStatusRequestType
        :arg user: User making the request
        :type user: oseoserver.models.OseoUser
        :return: The XML response object and the HTTP status code
        :rtype: tuple(str, int)
        """

        status_code = 200
        status_notification = self.validate_status_notification(request)
        if request.orderSpecification is not None:
            order_spec = self.process_order_specification(
                request.orderSpecification, user)
        else:
            raise errors.SubmitWithQuotationError('Submit with quotationId is '
                                                  'not implemented.')
        default_status = models.Order.SUBMITTED
        additional_status_info = ("Order is awaiting approval")
        if order_spec["order_type"].automatic_approval:
            default_status = models.Order.ACCEPTED
            additional_status_info = ("Order is placed in processing queue")
        order = self.create_order(order_spec, user, status_notification,
                                  default_status, additional_status_info)
        response = oseo.SubmitAck(status='success')
        response.orderId = str(order.id)
        response.orderReference = self._n(order.reference)
        return response, status_code, {"order": order}

    def process_order_specification(self, order_specification, user):
        """
        Validate and extract the order specification from the request

        :arg order_specification:
        :type order_specification:
        :arg user:
        :type user:

        :return:
        :rtype: dict
        """

        spec = {
            "order_type": self._get_order_type(order_specification),
            "order_item": [],
        }
        if len(order_specification.orderItem) > models.Order.MAX_ORDER_ITEMS:
            raise errors.InvalidOrderError(
                "Maximum number of order items is {}".format(
                    models.Order.MAX_ORDER_ITEMS)
            )
        for oi in order_specification.orderItem:
            item = self.validate_order_item(oi, spec["order_type"],
                                            user)
            spec["order_item"].append(item)
        spec["requested_order_configurations"] = []
        for col in set([i["collection"] for i in spec["order_item"]]):
            order_config = self._get_order_configuration(
                col, spec["order_type"])
            spec["requested_order_configurations"].append(order_config)
        spec["order_reference"] = self._c(order_specification.orderReference)
        spec["order_remark"] = self._c(order_specification.orderRemark)
        spec["packaging"] = self._validate_packaging(
            order_specification.packaging)
        spec["priority"] = self._c(order_specification.priority)
        spec["delivery_information"] = self.get_delivery_information(
            order_specification.deliveryInformation)
        spec["invoice_address"] = self.get_invoice_address(
            order_specification.invoiceAddress)
        try:
            spec["option"] = self._validate_global_options(
                order_specification,
                spec["order_type"],
                spec["requested_order_configurations"]
            )
            spec["delivery_options"] = self._validate_global_delivery_options(
                order_specification, spec["requested_order_configurations"])
        except errors.InvalidOptionError as e:
            raise errors.InvalidGlobalOptionError(e.option, e.order_config)
        except errors.InvalidOptionValueError as e:
            raise errors.InvalidGlobalOptionValueError(e.option, e.value,
                                                       e.order_config)
        except errors.InvalidDeliveryOptionError as e:
            logger.debug(e)
            raise errors.InvalidGlobalDeliveryOptionError()
        return spec

    def create_order(self, order_spec, user, status_notification, status,
                     additional_status_info):
        """
        Persist the order specification in the database.

        :param order_spec:
        :param user:
        :param status_notification:
        :param status:
        :return:
        """

        general_params = {
            "order_type": order_spec["order_type"],
            "status": status,
            "additional_status_info": additional_status_info,
            "remark": order_spec["order_remark"],
            "user": user,
            "reference": order_spec["order_reference"],
            "packaging": order_spec["packaging"],
            "priority": order_spec["priority"],
            "status_notification": status_notification,
        }
        if order_spec["order_type"].name == models.Order.PRODUCT_ORDER:
            order = models.ProductOrder(**general_params)
        elif order_spec["order_type"].name == models.Order.MASSIVE_ORDER:
            order = models.MassiveOrder(**general_params)
        elif order_spec["order_type"].name == models.Order.SUBSCRIPTION_ORDER:
            order = models.SubscriptionOrder(**general_params)
        else:
            order = models.TaskingOrder(**general_params)
        order.save()
        if order_spec["invoice_address"] is not None:
            invoice = models.InvoiceAddress()
            order.invoice_address = invoice
        # TODO Implement the code for when orders do have invoice address
        if order_spec["delivery_information"] is not None:
            delivery_info = models.DeliveryInformation()
            order.delivery_information = delivery_info
        # TODO Implement the code for when orders do have delivery information
        for k, v in order_spec["option"].iteritems():
            option = models.Option.objects.get(name=k)
            order.selected_options.add(models.SelectedOption(option=option,
                                                             value=v))
        delivery = order_spec["delivery_options"]
        if delivery is not None:
            copies = 1 if delivery["copies"] is None else delivery["copies"]
            sdo = models.SelectedDeliveryOption(
                customizable_item=order,
                annotation=delivery["annotation"],
                copies=copies,
                special_instructions=delivery["special_instructions"],
                option=delivery["type"]
            )
            sdo.save()
        order.save()
        if order.order_type.name == models.Order.PRODUCT_ORDER:
            batch = order.create_batch(order.status,
                                       *order_spec["order_item"])
        return order

    def get_delivery_information(self, requested_delivery_info):
        if requested_delivery_info is not None:
            info = dict()
            requested_mail_info = requested_delivery_info.mailAddress
            requested_online_info = requested_delivery_info.onlineAddress
            if requested_mail_info is not None:
                info["mail_address"] = self._get_delivery_address(
                    requested_mail_info)
            if len(requested_online_info) > 0:
                info["online_address"] = []
                for online_address in requested_online_info:
                    info["online_address"].append({
                        "protocol": self._c(online_address.protocol),
                        "server_address": self._c(
                            online_address.serverAddress),
                        "user_name": self._c(online_address.userName),
                        "user_password": self._c(online_address.userPassword),
                        "path": self._c(online_address.path),
                    })
        else:
            info = None
        return info

    def get_invoice_address(self, requested_invoice_address):
        if requested_invoice_address is not None:
            invoice = self._get_delivery_address(requested_invoice_address)
        else:
            invoice = None
        return invoice

    def _get_delivery_address(self, delivery_address_type):
        address = {
            "first_name": self._c(delivery_address_type.firstName),
            "last_name": self._c(delivery_address_type.lastName),
            "company_ref": self._c(delivery_address_type.companyRef),
            "telephone_number": self._c(
                delivery_address_type.telephoneNumber),
            "facsimile_telephone_number": self._c(
                delivery_address_type.facsimileTelephoneNumber),
        }
        postal_address = delivery_address_type.postalAddress
        if postal_address is not None:
            address["postal_address"] = {
                "street_address": self._c(
                    postal_address.streetAddress),
                "city": self._c(postal_address.city),
                "state": self._c(postal_address.state),
                "postal_code": self._c(postal_address.postalCode),
                "country": self._c(postal_address.country),
                "post_box": self._c(postal_address.postBox),
                }
        return address

    def get_collection_id(self, item_id, user_group):
        """
        Search all of the defined catalogue endpoints and determine
        the collection for the specified item.

        This method is used when the requested order item does not provide the
        optional 'collectionId' element.

        :param item_id: The identifier of the requested item in the CSW
            catalogue
        :type item_id: string
        :param user_group: The group to which the user making the request
            belongs
        :type user_group: models.OseoGroup
        :return:
        """

        request_headers = {
            "Content-Type": "application/xml"
        }
        ns = {
            "gmd": gmd.Namespace.uri(),
            "gco": gco.Namespace.uri(),
            }
        req = csw.GetRecordById(
            service="CSW",
            version="2.0.2",
            ElementSetName="summary",
            outputSchema=ns["gmd"],
            Id=[BIND(item_id)]
        )
        query_path = ("gmd:MD_Metadata/gmd:parentIdentifier/"
                      "gco:CharacterString/text()")
        collections = models.Collection.objects.filter(
            authorized_groups=user_group)
        endpoints = list(set([c.catalogue_endpoint for c in collections]))
        collection_id = None
        current = 0
        while collection_id is None and current < len(endpoints):
            url = endpoints[current]
            response = requests.post(url, data=req.toxml(),
                                     headers=request_headers)
            if response.status_code != 200:
                continue
            r = etree.fromstring(response.text.encode(OseoServer.ENCODING))
            id_container = r.xpath(query_path, namespaces=ns)
            collection_id = id_container[0] if len(id_container) == 1 else None
            current += 1
        return collection_id

    def validate_order_item(self, requested_item, order_type, user):
        """

        :param requested_item: The pyxb instance with the requested item
        :type requested_item: oseo.CommonOrderItemType
        :param order_type: The order type in use
        :type order_type: models.OrderType
        :param user: the user that has placed the order
        :type user: models.OseoUser
        :return:
        """

        item = {
            "item_id": requested_item.itemId,
            "product_order_options_id": self._c(
                requested_item.productOrderOptionsId),
            "order_item_remark": self._c(requested_item.orderItemRemark)
        }
        if order_type.name in (models.Order.PRODUCT_ORDER,
                               models.Order.MASSIVE_ORDER):
            identifier, collection = self._validate_product_order_item(
                requested_item, user)
            item["identifier"] = identifier
        elif order_type.name == models.Order.SUBSCRIPTION_ORDER:
            collection = self._validate_subscription_order_item(
                requested_item, user)
        else:  # TASKING_ORDER
            tasking_id, collection = self._validate_tasking_order_item(
                requested_item, user)
            item["tasking_id"] = tasking_id
        item["collection"] = collection
        order_config = self._get_order_configuration(collection, order_type)
        item["option"] = self._validate_requested_options(
            requested_item,
            order_type,
            order_config
        )
        item["delivery_options"] = self._validate_delivery_options(
            requested_item, order_config)
        item["scene_selection"] = dict()  # not implemented yet
        item["payment"] = None  # not implemented yet
        # extensions to the CommonOrderItemType are not implemented yet
        return item

    def _validate_product_order_item(self, requested_item, user):
        identifier = self._c(requested_item.productId.identifier)
        col_id = requested_item.productId.collectionId
        if col_id is None:
            col_id = self.get_collection_id(identifier,
                                            user.oseo_group)
        collection = self._validate_requested_collection(col_id,
                                                         user.oseo_group)
        return identifier, collection

    def _validate_subscription_order_item(self, requested_item, user):
        col_id = requested_item.subscriptionId.collectionId
        collection = self._validate_requested_collection(col_id,
                                                         user.oseo_group)
        return collection

    def _validate_tasking_order_item(self, requested_item, user):
        tasking_id = requested_item.taskingRequestId
        # TODO: find a way to retrieve the collection
        # TODO: validate the tasking_id
        collection = None
        return tasking_id, collection

    def _get_order_configuration(self, collection, order_type):
        """

        :param collection:
        :param order_type:
        :type order_type: models.OrderType
        :return:
        """

        logger.info("collection: {}".format(collection))
        if order_type.name == models.Order.PRODUCT_ORDER:
            config = collection.productorderconfiguration
        elif order_type.name == models.Order.MASSIVE_ORDER:
            config = collection.massiveorderconfiguration
        elif order_type.name == models.Order.SUBSCRIPTION_ORDER:
            config = collection.subscriptionorderconfiguration
        else:  # tasking order
            config = collection.taskingorderconfiguration
        if not config.enabled:
            raise errors.InvalidCollectionError(collection.name,
                                                order_type.name)
        return config

    def _validate_requested_collection(self, collection_id, group):
        try:
            collection = models.Collection.objects.get(
                collection_id=collection_id)
            if not collection.allows_group(group):
                raise errors.UnAuthorizedOrder(
                    "user's group is not authorized to order {} "
                    "products".format(collection.name)
                )
        except models.Collection.DoesNotExist:
            raise errors.InvalidCollectionError(
                "Collection {} does not exist".format(collection_id))
        return collection

    def _validate_requested_options(self, requested_item, order_type,
                                    order_config):
        """

        :param requested_item:
        :type requested_item:
        :param order_type:
        :type order_type: models.OrderType
        :param order_config:
        :type order_config:
        :return:
        """

        valid_options = dict()
        for option in requested_item.option:
            values = option.ParameterData.values
            encoding = option.ParameterData.encoding
            # since values is an xsd:anyType, we will not do schema
            # validation on it
            values_tree = etree.fromstring(values.toxml(OseoServer.ENCODING))
            for value in values_tree:
                option_name = etree.QName(value).localname
                option_value = self._validate_selected_option(
                    option_name, value, order_type, order_config)
                valid_options[option_name] = option_value
        return valid_options

    def _validate_global_options(self, requested_order_spec,
                                 order_type,
                                 ordered_order_configs):
        for order_config in ordered_order_configs:
            options = self._validate_requested_options(requested_order_spec,
                                                       order_type,
                                                       order_config)
        return options

    def _validate_selected_option(self, name, value, order_type, order_config):
        """
        Validate a selected option choice.

        The validation process first tries to extract the option's value as
        a simple text and matches it with the available choices for the
        option. If a match cannot be made, the collection's custom processing
        class is instantiated and used to parse the option into a text based
        format. This parsed value is again matched against the available
        choices.

        :param name: The name of the option
        :type name: string
        :param value:
        :type value:
        :param order_type:
        :type order_type:
        :param order_config:
        :type order_config:
        :return:
        :rtype:
        """

        logger_type = "pyoseo"
        try:
            option = order_config.options.get(name=name)
            choices = [c.value for c in option.choices.all()]
            if len(choices) > 0:
                naive_value = value.text
                if naive_value in choices:
                    result = naive_value
                else:
                    processing_class, params = utilities.get_custom_code(
                        order_type,
                        models.ItemProcessor.PROCESSING_PARSE_OPTION
                    )
                    handler = utilities.import_class(processing_class,
                                                     logger_type=logger_type)
                    parsed_value = handler.parse_option(name, value, **params)
                    if parsed_value in choices:
                        result = parsed_value
                    else:
                        raise errors.InvalidOptionValueError(name,
                                                             parsed_value,
                                                             order_config)
            else:
                processing_class, params = utilities.get_custom_code(
                    order_type,
                    models.ItemProcessor.PROCESSING_PARSE_OPTION
                )
                handler = utilities.import_class(processing_class,
                                                 logger_type=logger_type)
                result = handler.parse_option(name, value, **params)
        except models.Option.DoesNotExist:
            raise errors.InvalidOptionError(name, order_config)
        except errors.InvalidOptionValueError:
            raise
        except Exception as e:
            raise errors.CustomOptionParsingError(*e.args)
        return result

    def _validate_delivery_options(self, requested_item, order_config):
        """
        Validate the requested delivery options for an item.

        The input requested_item can be an order or an order item

        :param requested_item: oseo.Order or oseo.OrderItem
        :param order_config: models.rderConfiguration
        :return: The requested delivery options
        :rtype: dict()
        """

        delivery = None
        dop = requested_item.deliveryOptions
        if dop is not None:
            delivery = dict()
            try:
                if dop.onlineDataAccess is not None:
                    p = dop.onlineDataAccess.protocol
                    delivery["type"] = order_config.delivery_options.get(
                        onlinedataaccess__protocol=p)
                elif dop.onlineDataDelivery is not None:
                    p = dop.onlineDataAccess.protocol
                    delivery["type"] = order_config.delivery_options.get(
                        onlinedatadelivery__protocol=p)
                else:
                    p = dop.mediaDelivery.packageMedium,
                    s = dop.mediaDelivery.shippingInstructions,
                    delivery["type"] = order_config.delivery_options.get(
                        mediadelivery__package_medium=p,
                        mediadelivery__shipping_instructions=s)
            except models.DeliveryOption.DoesNotExist:
                raise errors.InvalidDeliveryOptionError()
            copies = dop.numberOfCopies
            delivery["copies"] = int(copies) if copies is not None else copies
            delivery["annotation"] = self._c(dop.productAnnotation)
            delivery["special_instructions"] = self._c(dop.specialInstructions)
        return delivery

    def _validate_global_delivery_options(self, requested_order_spec,
                                          ordered_order_configs):
        """
        Validate global order delivery options.

        PyOSEO only accepts global options that are valid for each of the
        order items contained in the order. As such, the requested
        delivery options must be valid according to all of order
        configurations of the ordered collections.

        :param requested_order_spec:
        :param ordered_order_configs:
        :return:
        """

        for order_config in ordered_order_configs:
            delivery_options = self._validate_delivery_options(
                requested_order_spec, order_config)
        return delivery_options

    def _get_order_type(self, order_specification):
        """
        Return the order type for the input order specification.

        Usually the order type can be extracted directly from the order
        specification, as the OSEO standard defines only PRODUCT ORDER,
        SUBSCRIPTION ORDER and TASKING ORDER. We are adding a fourth type,
        MASSIVE ORDER, which is based on the existence of a special reference
        on orders of type PRODUCT ORDER.

        :param order_specification:
        :type order_specification: oseo.Submit
        :return:
        :rtype: models.OrderType
        """

        order_type = models.OrderType.objects.get(
            name=order_specification.orderType)
        if order_type.name == "PRODUCT_ORDER":
            ref = self._c(order_specification.orderReference)
            massive_reference = getattr(
                django_settings,
                'OSEOSERVER_MASSIVE_ORDER_REFERENCE',
                None
            )
            if massive_reference is not None and ref == massive_reference:
                order_type = models.OrderType.objects.get(
                    name="MASSIVE_ORDER")
        if not order_type.enabled:
            raise errors.InvalidOrderTypeError(order_type.name)
        return order_type

    def validate_status_notification(self, request):
        """
        Check that the requested status notification is supported.

        :param request:
        :return:
        """

        if request.statusNotification != models.Order.NONE:
            raise NotImplementedError('Status notifications are '
                                      'not supported')
        return request.statusNotification

    def _validate_packaging(self, requested_packaging):
        packaging = self._c(requested_packaging)
        choices = [c[0] for c in models.Order.PACKAGING_CHOICES]
        if packaging != "" and packaging not in choices:
            raise errors.InvalidPackagingError(packaging)
        return packaging
