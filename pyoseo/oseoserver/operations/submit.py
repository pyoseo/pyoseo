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
Implements the OSEO Submit operation
'''

import datetime as dt
import logging

from django.db import transaction
from django.conf import settings as django_settings
import pyxb.bundles.opengis.oseo as oseo

from oseoserver import models
from oseoserver import tasks
from oseoserver.operations.base import OseoOperation

logger = logging.getLogger('.'.join(('pyoseo', __name__)))

class Submit(OseoOperation):
    NAME = 'Submit'

    @transaction.atomic
    def __call__(self, request, user_name):
        '''
        Implements the OSEO Submit operation.

        * save order details in the database
        * generate the appropriate response
        * if it is a normal order, send the task to celery
        * if it is a subscription or a massive order, send an email to admins

        :arg request: The instance with the request parameters
        :type request: pyxb.bundles.opengis.raw.oseo.GetStatusRequestType
        :arg user_name: User making the request
        :type user_name: str
        :return: The XML response object and the HTTP status code
        :rtype: tuple(str, int)
        '''

        status_code = 200
        if request.orderSpecification is not None:
            # order specification type of Submit
            ord_spec = request.orderSpecification
            creation_date = dt.datetime.utcnow()
            order = models.Order(
                created_on=creation_date,
                status_changed_on=creation_date,
                remark=self._c(ord_spec.orderRemark),
                reference=self._c(ord_spec.orderReference),
                packaging=self._c(ord_spec.packaging),
                priority=self._c(ord_spec.priority)
            )
            if ord_spec.orderType == models.OrderType.PRODUCT_ORDER:
                ref = self._c(ord_spec.orderReference)
                massive_order_reference = getattr(
                    django_settings,
                    'OSEOSERVER_MASSIVE_ORDER_REFERENCE',
                    None
                )

                if massive_order_reference is not None and \
                        ref == massive_order_reference:
                    order.order_type = models.OrderType.objects.get(
                            name=models.OrderType.MASSIVE_ORDER)
                    order.status = models.CustomizableItem.SUBMITTED
                else:
                    order.order_type = models.OrderType.objects.get(
                            name=models.OrderType.PRODUCT_ORDER)
                    order.status = models.CustomizableItem.ACCEPTED
            order.user = models.User.objects.get(id=1) # for testing purposes only
            #  not very nice but we will deal with option groups some other day
            order.option_group = models.OptionGroup.objects.get(id=1)
            order.save()
            self.parse_order_delivery_method(ord_spec, order)
            # add options
            if ord_spec.invoiceAddress is not None:
                ia = ord_spec.invoiceAddress
                order.invoice_address = models.InvoiceAddress(
                    first_name=self._c(ia.mailAddress.firstName),
                    last_name=self._c(ia.mailAddress.lastName),
                    company_ref=self._c(ia.mailAddress.companyRef),
                    street_address=self._c(
                        ia.mailAddress.postalAddress.streetAddress),
                    city=self._c(ia.mailAddress.postalAddress.city),
                    state=self._c(ia.mailAddress.postalAddress.state),
                    postal_code=self._c(
                        ia.mailAddress.postalAddress.postalCode),
                    country=self._c(ia.mailAddress.postalAddress.country),
                    post_box=self._c(ia.mailAddress.postalAddress.postBox),
                    telephone=self._c(ia.mailAddress.telephoneNumer),
                    fax=self._c(ia.mailAddress.facsimileTelephoneNumbe),
                )
            if order.order_type.name == models.OrderType.PRODUCT_ORDER:
                self.create_normal_order_batch(ord_spec, order)
                tasks.process_normal_order(order.id)
            elif order.order_type.name == models.OrderType.SUBSCRIPTION_ORDER:
                # do not create any batch yet
                # batches will be created on demand, whenever new products
                # come out of the processing lines
                raise errors.SubmitSubscriptionError('Submission of '
                                                     'subscription orders is '
                                                     'not implemented')
            elif order.order_type.name == models.OrderType.MASSIVE_ORDER:
                self.create_massive_order_batches()
        else:
            raise errors.SubmitWithQuotationError('Submit with quotationId is '
                                                  'not implemented.')
        response = oseo.SubmitAck(status='success')
        response.orderId = str(order.id)
        return response, status_code

    def create_normal_order_batch(self, order_specification, order):
        '''
        Create the order item batch for a normal order.

        Normal orders are composed of a single batch with all of the ordered
        items inside it.

        :arg order_specification: the OSEO order specification
        :type order_specification: pyxb.bundles.opengis.oseo.OrderSpecification
        :arg order: the order record that is being created in the database
        :type order: oseoserver.models.Order
        '''

        batch = models.Batch(order=order)
        batch.save()
        for oi in order_specification.orderItem:
            order_item = models.OrderItem(
                item_id=oi.itemId,
                status=models.CustomizableItem.ACCEPTED,
                created_on=order.created_on,
                status_changed_on=order.created_on,
                remark=self._c(oi.orderItemRemark),
                option_group=order.option_group
            )
            # add order_item options
            # add order_item scene selection
            if oi.deliveryOptions is not None:
                d_opts = self._set_delivery_options(
                    oi.deliveryOptions,
                    order.order_type.name
                )
                order_item.deliveryoption = d_opts
            # add order_item payment
            order_item.identifier = self._c(oi.productId.identifier)
            order_item.collection_id = self._c(oi.productId.collectionId)
            batch.order_items.add(order_item)
            order_item.save()
        order.save()

    def create_massive_order_batches(self):
        '''
        break the order down into multiple batches
        '''

        raise errors.SubmitMassiveOrderError('Submission of massive orders is '
                                             'not implemented')

    def parse_order_delivery_method(self, order_specification, order):
        '''
        Validate and parse the requested delivery method for an order.

        One order can have one of three types of delivery:

        * online access

          This option means that the order will be available at our server
          for the user to download. We can use one of several protocols (HTTP,
          FTP, ...) as implementations become available.

          The available implementations are stored as records of the
          oseoserver.models.OnlineDataAccess model, but they can be restricted
          to certain OptionGroups and further restricted to certain Order
          types. This means that altough the server may support online data 
          access with the FTP protocol, it is possible to restrict it so that
          it is only available for orders of type 'SUBSCRIPTION_ORDER' and
          only if the orders belong to the 'pyoseo options' option group.

        * online delivery

          This option means that we will actively deliver the ordered items to
          some server specified by the user, using a specific protocol (such as
          FTP) and with credentials supplied by the user

        * mail delivery

          This option means that we will deliver a physical medium to the user,
          which will be shipped by normal mail, according to the user specified
          instructions and address.

        :arg order_specification: the OSEO order specification
        :type order_specification: pyxb.bundles.opengis.oseo.OrderSpecification
        :arg order: the order record that is being created in the database
        :type order: oseoserver.models.Order
        '''

        a = [d.delivery_option for d in \
                order.order_type.deliveryoptionordertype_set.all()]
        b = [d.delivery_option for d in \
                order.option_group.groupdeliveryoption_set.all()]
        available_delivery_options = [d.child_instance() for d in a if d in b]
        dop = order_specification.deliveryOptions
        if dop is not None: # we can have any of the three options
            if dop.onlineDataAccess is not None:
                requested_type = models.OnlineDataAccess
            elif dop.onlineDataDelivery is not None:
                requested_type = models.OnlineDataDelivery
            else:
                requested_type = models.MediaDelivery
        else: # we can have either online delivery or mail delivery
            delivery_information = order_specification.deliveryInformation
            if delivery_information is not None:
                if any(list(delivery_information.onlineAddress)):
                    requested_type = models.OnlineDataDelivery
                elif order_specification.mailAddress is not None:
                    requested_type = models.MediaDelivery
                else:
                    raise errors.InvalidOrderDeliveryMethodError(
                        'No valid delivery method found'
                    )
            else:
                raise errors.InvalidOrderDeliveryMethodError(
                    'No valid delivery method found'
                )
        if requested_type in [a.__class__ for a in available_delivery_options]:
            # the requested delivery method is allowed for this order
            if requested_type == models.OnlineDataAccess:
                self._add_online_data_access_data(order, order_specification,
                                                  available_delivery_options)
            elif requested_type == models.OnlineDataDelivery:
                self._add_online_data_access_data(order, order_specification,
                                                  available_delivery_options)
            else:
                self._add_media_delivery_data(order, order_specification)
        else:
            raise errors.InvalidOrderDeliveryMethodError(
                'The chosen delivery method is not allowed'
            )

    def _add_online_data_access_data(self, order, order_specification,
                                     available_options):
        '''
        Validate the requested protocol and add the requested online access
        definition to the order being processed.

        :arg order:
        :type order: oseoserver.models.Order
        :arg order_specification:
        :type order_specification: pyxb.bundles.opengis.oseo.OrderSpecification
        :arg available_options:
        :type available_options: list
        '''

        delivery_options = order_specification.deliveryOptions
        protocols = [i.protocol for i in available_options if isinstance(i,
                     models.OnlineDataAccess)]
        req_protocol = self._c(delivery_options.onlineDataAccess.protocol)
        if req_protocol in protocols:
            sdo = self._create_selected_delivery_option(delivery_options)
            logger.debug('sdo: %s' % sdo)
            del_opt = models.OnlineDataAccess.objects.get(
                                                protocol=req_protocol)
            option_group = order.option_group
            logger.debug('del_opt: %s' % del_opt)
            logger.debug('type(del_opt): %s' % type(del_opt))
            logger.debug('option_group: %s' % option_group)
            logger.debug('type(option_group): %s' % type(option_group))
            gdo = models.GroupDeliveryOption.objects.get(
                option_group=option_group,
                delivery_option=del_opt
            )
            sdo.group_delivery_option = gdo
            order.selected_delivery_option = sdo
            sdo.save()
            order.save()
        else:
            # the requested protocol is not allowed
            raise errors.OnlineDataAccessInvalidProtocol('The requested '
                                                         'protocol is invalid')

    def _add_online_data_delivery_data(self, order, order_specification,
                                       available_options):
        '''
        :arg order:
        :type order: oseoserver.models.Order
        :arg order_specification:
        :type order_specification: pyxb.bundles.opengis.oseo.OrderSpecification
        :arg available_options:
        :type available_options: list
        '''

        delivery_options = order_specification.deliveryOptions
        if delivery_options is not None:
            sdo = self._create_selected_delivery_option(delivery_options)
            req_protocol = self._c(delivery_options.onlineDataDelivery.protocol)
        else:
            sdo = models.SelectedDeliveryOption()
            try:
                # fall back to the protocol defined in the deliveryInformation 
                # section, if there is one
                d = order_specification.deliveryInformation
                oa = d.onlineAddress[0]
                req_protocol = self._c(oa.protocol)
            except AttributeError, IndexError:
                raise errors.InvalidOrderDeliveryMethodError(
                    'The requested order delivery method is not valid'
                )
        protocols = [i.protocol for i in available_options if isinstance(i,
                     models.OnlineDataDelivery)]
        if req_protocol in protocols:
            ordered_delivery_info = order_specification.deliveryInformation
            if ordered_delivery_info is not None:
                delivery_info = models.DeliveryInformation()
                order.delivery_information = delivery_info
                delivery_info.save()
                for online_address in ordered_delivery_info.onlineAddress:
                    oa = models.OnlineAddress(
                        protocol=self._c(online_address.protocol),
                        server_address=self._c(online_address.serverAddress),
                        user_name=self._c(online_address.userName),
                        user_password=self._c(online_address.userPassword),
                        path=self._c(online_address.path)
                    )
                    oa.delivery_information = delivery_info
                    oa.save()
            else:
                raise errors.InvalidOrderDeliveryMethodError(
                    'The delivery method is not correctly specified'
                )
            del_opt = models.OnlineDataDelivery(protocol=req_protocol)
            option_group = order.option_group
            gdo = models.GroupDeliveryOption.objects.get(
                option_group=option_group,
                delivery_option=del_opt
            )
            sdo.group_delivery_option = gdo
            order.selected_delivery_option = sdo
            order.save()
        else:
            raise errors.OnlineDataDeliveryInvalidProtocol('The requested '
                                                         'protocol is invalid')

    def _add_media_delivery_data(self, order, order_specification):
        '''
        :arg order:
        :type order: oseoserver.models.Order
        :arg order_specification:
        :type order_specification: pyxb.bundles.opengis.oseo.OrderSpecification
        '''

        ordered_delivery_info = order_specification.deliveryInformation
        if ordered_delivery_info is not None:
            address = ordered_delivery_info.mailAddress
            delivery_info = models.DeliveryInformation(
                first_name=self._c(address.firstName),
                last_name=self._c(address.lastName),
                company_ref=self._c(address.companyRef),
                street_address=self._c(address.postalAddress.streetAddress),
                city=self._c(address.postalAddress.city),
                state=self._c(address.postalAddress.state),
                postal_code=self._c(address.postalAddress.postalCode),
                country=self._c(address.postalAddress.country),
                post_box=self._c(address.postalAddress.postBox),
                telephone=self._c(address.telephoneNumber),
                fax=self._c(address.facsimileTelephoneNumber)
            )
            order.delivery_information = delivery_info
            delivery_info.save()

            delivery_options = order_specification.deliveryOptions
            if delivery_options is not None:
                sdo = self._create_selected_delivery_option(delivery_options)
                package_medium = self._c(
                        delivery_options.mediaDelivery.packageMedium)
                shipping_instructions = self._c(
                        delivery_options.mediaDelivery.shippingInstructions)
            else:
                sdo = models.SelectedDeliveryOption()
                package_medium = ''
                shipping_instructions = ''
            del_opt = models.MediaDelivery(
                package_medium=package_medium,
                shipping_instructions=shipping_instructions
            )
            option_group = order.option_group
            gdo = models.GroupDeliveryOption.objects.get(
                option_group=option_group,
                delivery_option=del_opt
            )
            sdo.group_delivery_option = gdo
            order.selected_delivery_option = sdo
            order.save()
        else:
            raise errors.InvalidOrderDeliveryMethodError(
                'The delivery method is not correctly specified'
            )

    def _create_selected_delivery_option(self, delivery_options):
        sdo = models.SelectedDeliveryOption(
            copies=delivery_options.numberOfCopies,
            annotation=self._c(delivery_options.productAnnotation),
            special_instructions=self._c(delivery_options.specialInstructions),
        )
        return sdo

    def _set_delivery_options(self, options, order_type):
        '''
        Create a database record with the input delivery options.

        :arg options: The oseo deliveryOptions
        :type options: pyxb.bundles.opengis.oseo.DeliveryOptionsType
        :arg order_type: The type of order being requested
        :type order_type: str
        :return: pyoseo.models.SelectedDeliveryOption
        '''

        possibly_null = [
            options.onlineDataAccess,
            options.onlineDataDelivery,
            options.mediaDelivery.packageMedium if \
                    options.mediaDelivery is not None else None,
            options.mediaDelivery.shippingInstructions if \
                    options.mediaDelivery is not None else None,
            options.numberOfCopies,
            options.productAnnotation,
            options.specialInstructions]
        if any(possibly_null):
            try:
                num_copies = options.numberOfCopies
            except TypeError:
                num_copies = None
            del_option = models.SelectedDeliveryOption(
                copies=num_copies,
                annotation=self._c(options.productAnnotation),
                special_instructions=self._c(options.specialInstructions)
            )
            if options.onlineDataAccess is not None:
                protocol = options.onlineDataAccess.protocol
                if self._validate_online_data_access_protocol(protocol,
                        order_type):
                    oda = models.OnlineDataAccess(protocol=protocol)
                    del_option.onlinedataaccess = oda
                else:
                    pass # raise some sort of error
            elif options.onlineDataDelivery is not None:
                protocol = options.onlineDataDelivery.protocol
                if self._validate_online_data_delivery_protocol(protocol,
                        order_type):
                    odd = models.OnlineDataDelivery(protocol=protocol)
                    del_option.onlinedatadelivery = odd
                else:
                    pass # raise some sort of error
            elif options.mediaDelivery is not None:
                medium = options.mediaDelivery.packageMedium
                if self._validate_media_delivery(medium, order_type):
                    md = models.MediaDelivery(package_medium=medium)
                    md.shipping_instructions = self._c(
                            options.mediaDelivery.shippingInstructions)
                    del_option.mediadelivery = md
                else:
                    pass # raise some sort of error
        else:
            del_option = None
        return del_option

    def _validate_online_data_access_protocol(self, protocol, order_type):
        available_protocols = []
        for dot in models.DeliveryOptionOrderType.objects.all():
            if hasattr(dot.delivery_option, 'onlinedataaccess') and \
                    dot.order_type.name == order_type:
                p = dot.delivery_option.onlinedataaccess.protocol
                available_protocols.append(p)
        result = False
        if protocol in available_protocols:
            result = True
        return result

    def _validate_online_data_delivery_protocol(self, protocol, order_type):
        available_protocols = []
        for dot in models.DeliveryOptionOrderType.objects.all():
            if hasattr(dot.delivery_option, 'onlinedatadelivery') and \
                    dot.order_type.name == order_type:
                p = dot.delivery_option.onlinedatadelivery.protocol
                available_protocols.append(p)
        result = False
        if protocol in available_protocols:
            result = True
        return result

    def _validate_media_delivery(self, package_medium, order_type):
        available_media = []
        for dot in models.DeliveryOptionOrderType.objects.all():
            if hasattr(dot.delivery_option, 'mediadelivery') and \
                    dot.order_type.name == order_type:
                m = dot.delivery_option.mediadelivery.package_medium
                available_media.append(m)
        result = False
        if package_medium in available_media:
            result = True
        return result
