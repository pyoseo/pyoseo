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
import datetime as dt
import logging

from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings as django_settings
import pyxb.bundles.opengis.oseo_1_0 as oseo
import pytz
from lxml import etree

from oseoserver import models
from oseoserver import tasks
from oseoserver import errors
from oseoserver import utilities
from oseoserver.server import OseoServer
from oseoserver.operations.base import OseoOperation
import oseoserver.xml_schemas.pyoseo_schema as pyoseo_schema

logger = logging.getLogger('.'.join(('pyoseo', __name__)))


class Submit(OseoOperation):

    @transaction.atomic
    def __call__(self, request, user, user_password=None, **kwargs):
        """
        Implements the OSEO Submit operation.

        * save order details in the database
        * generate the appropriate response
        * if it is a normal order, send the task to celery
        * if it is a subscription or a massive order, send an email to admins

        :arg request: The instance with the request parameters
        :type request: pyxb.bundles.opengis.raw.oseo.GetStatusRequestType
        :arg user: User making the request
        :type user: oseoserver.models.OseoUser
        :arg user_password: Password of the user making the request
        :type user_password: str
        :return: The XML response object and the HTTP status code
        :rtype: tuple(str, int)
        """

        status_code = 200
        if request.orderSpecification is not None:
            order = self.process_order_specification(
                request.orderSpecification, user)
        else:
            raise errors.SubmitWithQuotationError('Submit with quotationId is '
                                                  'not implemented.')
        if order.status == models.CustomizableItem.SUBMITTED:
            self.dispatch_order(order)
        elif order.status == models.CustomizableItem.ACCEPTED:
            # this is where we notify the admin that an order is awaiting
            # moderation
            print("The order {} is awaiting moderation".format(order.id))
        response = oseo.SubmitAck(status='success')
        response.orderId = str(order.id)
        return response, status_code

    def process_order_specification(self, order_specification, user):
        """
        Handle submit requests that provide an order specification.

        :arg order_specification:
        :type order_specification:
        :arg user:
        :type user:

        :return:
        :rtype: models.Order
        """

        creation_date = dt.datetime.now(pytz.utc)
        order = models.Order(
            created_on=creation_date,
            status_changed_on=creation_date,
            remark=self._c(order_specification.orderRemark),
            reference=self._c(order_specification.orderReference),
            packaging=self._c(order_specification.packaging),
            priority=self._c(order_specification.priority)
        )
        order.user = user
        ia = order_specification.invoiceAddress
        if ia is not None:
            address = self.extract_invoice_address(ia)
            order.invoice_address = address
        order.order_type = self._get_order_type(order_specification)
        order.status = self._validate_order_type(order.order_type)
        # not very nice but we will deal with option groups some other day
        order.option_group = models.OptionGroup.objects.get(id=1)
        order.save()
        if order.status == models.CustomizableItem.FAILED:
            raise errors.InvalidOrderTypeError("Order of type {} is not "
                                               "supported".format(
                order.order_type))
        self.parse_order_delivery_method(order_specification, order)
        self.configure_delivery(order, user)
        order_options = self.extract_options(order_specification.option,
                                             order.customizableitem_ptr)
        if len(order_options) > 0:
            order.selected_options.add(*order_options)
            order.save()
        if order.order_type == models.OrderType.PRODUCT_ORDER:
            self.create_normal_order_batch(order_specification, order)
        return order

    def dispatch_order(self, order):
        """Dispatch an order for processing in the async queue."""
        if order.order_type == models.OrderType.PRODUCT_ORDER:
            tasks.process_normal_order.apply_async((order.id,))
        else:  # only normal PRODUCT_ORDERs are implemented
            raise NotImplementedError

    def extract_options(self, options, customizable_item):
        """
        Configure the options for the order and also for the order items

        It may be necessary to define a custom xsd file for pyoseo. This xsd
        is currently in the oseoserver/xml_schemas directory. PyXB can
        generate bindings for it by running the command:

        .. code:: bash

           pyxbgen pyoseo.xsd -m pyoseo_schema

        It can then be imported into python and used just like the rest of
        the OGC schemas.

        Alternatively we may not need to define custom xsd files and can
        probably get by just by creating the relevant swe base types. See the
        getoptions.py module for an example on how to create such an element
        with pyxb

        :param options: An iterable with the ParameterData pyxb objects
        :type options: pyxb.binding.content._PluralBinding
        :return:
        """

        model_options = []
        path = getattr(django_settings, "OSEOSERVER_OPTIONS_CLASS")
        for option in options:
            values = option.ParameterData.values
            # since values is an xsd:anyType, we will not do schema
            # validation on it
            values_tree = etree.fromstring(values.toxml(OseoServer._encoding))
            for value in values_tree:
                option_name = etree.QName(value).localname
                if self._option_enabled(option_name, customizable_item):
                    handler = utilities.import_class(path)
                    option_value = handler.parse_option(value)
                    if self._validate_option(option_name, option_value):
                        # FIXME - This is just a hack to make the options work
                        group_option = models.GroupOption.objects.filter(
                            option__name=option_name,
                            group=customizable_item.option_group
                        )[0]
                        sel_opt = models.SelectedOption(
                            group_option=group_option,
                            #customizable_item=customizable_item,
                            value=option_value
                        )
                        model_options.append(sel_opt)
                    else:
                        msg = ("The value '{}' is not valid for option "
                               "'{}'".format(option_value, option_name))
                        raise errors.InvalidOptionError(msg)
                else:
                    raise errors.InvalidOptionError(
                        "Option '{}' is not valid on this server".format(
                            option_name))
        return model_options

    def extract_invoice_address(self, invoice_address):
        address = models.InvoiceAddress(
            first_name=self._c(invoice_address.mailAddress.firstName),
            last_name=self._c(invoice_address.mailAddress.lastName),
            company_ref=self._c(invoice_address.mailAddress.companyRef),
            street_address=self._c(
                invoice_address.mailAddress.postalAddress.streetAddress),
            city=self._c(invoice_address.mailAddress.postalAddress.city),
            state=self._c(invoice_address.mailAddress.postalAddress.state),
            postal_code=self._c(
                invoice_address.mailAddress.postalAddress.postalCode),
            country=self._c(invoice_address.mailAddress.postalAddress.country),
            post_box=self._c(invoice_address.mailAddress.postalAddress.postBox),
            telephone=self._c(invoice_address.mailAddress.telephoneNumer),
            fax=self._c(invoice_address.mailAddress.facsimileTelephoneNumbe),
        )
        return address

    def create_normal_order_batch(self, order_specification, order):
        """
        Create the order item batch for a normal order.

        Normal orders are composed of a single batch with all of the ordered
        items inside it.

        :arg order_specification: the OSEO order specification
        :type order_specification: pyxb.bundles.opengis.oseo.OrderSpecification
        :arg order: the order record that is being created in the database
        :type order: oseoserver.models.Order
        """

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
            oi_options = self.extract_options(oi.option,
                                              order.customizableitem_ptr)
            if len(oi_options) > 0:
                order_item.selected_options.add(*oi_options)
                order_item.save()
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

    def parse_order_delivery_method(self, order_specification, order):
        """
        Validate and parse the requested delivery method for an order.

        One order can have one of three types of delivery:

        * online access

          This option means that the order will be available at our server
          for the user to download. We can use one of several protocols (HTTP,
          FTP, ...) as implementations become available.

          The available implementations are stored as records of the
          oseoserver.models.OnlineDataAccess model, but they can be restricted
          to certain OptionGroups and further restricted to certain Order
          types. This means that although the server may support online data
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
        """

        a = [d.delivery_option for d in
             order.order_type.deliveryoptionordertype_set.all()]
        b = [d.delivery_option for d in
             order.option_group.groupdeliveryoption_set.all()]
        available_delivery_options = [d.child_instance() for d in a if d in b]
        dop = order_specification.deliveryOptions
        if dop is not None:  # we can have any of the three options
            if dop.onlineDataAccess is not None:
                requested_type = models.OnlineDataAccess
            elif dop.onlineDataDelivery is not None:
                requested_type = models.OnlineDataDelivery
            else:
                requested_type = models.MediaDelivery
        else:  # we can have either online delivery or mail delivery
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

    # TODO - This method should be external to pyoseo
    def configure_delivery(self, order, user):
        """
        Perform delivery related operations.

        This method will determine the requested delivery protocol and
        perform the needed operations. For example, when an order defines
        online data access through the FTP protocol, this method ensures that
        the FTP account for the user is created.
        """

        create_ftp_account = False
        try:
            gdo = order.selected_delivery_option.group_delivery_option
            gdo_do = gdo.delivery_option
            requested_protocol = gdo_do.onlinedataaccess.protocol
            if requested_protocol == models.OnlineDataAccess.FTP:
                create_ftp_account = True
        except ObjectDoesNotExist:
            pass
        logger.debug('create_ftp_account: {}'.format(create_ftp_account))
        if create_ftp_account:
            user_name = user.user.username
            self._add_ftp_user(user_name)

    # TODO - This method should be external to pyoseo
    def _add_ftp_user(self, user):
        """
        Create a new FTP user.

        These FTP users are virtual and their creation relies on the ftp
        server being already correctly set up.

        :arg user: the name of the user that is to be added
        :type user: str
        """

        ftp_service_root = getattr(
            django_settings,
            'OSEOSERVER_ONLINE_DATA_ACCESS_FTP_PROTOCOL_ROOT_DIR'
        )
        user_home = os.path.join(ftp_service_root, user)
        try:
            os.makedirs(user_home)
            # python's equivalent to chmod 755 user_home
            os.chmod(user_home, stat.S_IRWXU | stat.S_IRGRP |
                     stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
        except OSError as err:
            if err.errno == 17:
                logger.debug('user home already exists')
                pass
            else:
                raise

    def _add_online_data_access_data(self, order, order_specification,
                                     available_options):
        """
        Validate the requested protocol and add the requested online access
        definition to the order being processed.

        :arg order:
        :type order: oseoserver.models.Order
        :arg order_specification:
        :type order_specification: pyxb.bundles.opengis.oseo.OrderSpecification
        :arg available_options:
        :type available_options: list
        """

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
        """
        :arg order:
        :type order: oseoserver.models.Order
        :arg order_specification:
        :type order_specification: pyxb.bundles.opengis.oseo.OrderSpecification
        :arg available_options:
        :type available_options: list
        """

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
            except (AttributeError, IndexError):
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
            raise errors.OnlineDataDeliveryInvalidProtocol(
                'The requested protocol is invalid')

    def _add_media_delivery_data(self, order, order_specification):
        """
        :arg order:
        :type order: oseoserver.models.Order
        :arg order_specification:
        :type order_specification: pyxb.bundles.opengis.oseo.OrderSpecification
        """

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
        """
        Create a database record with the input delivery options.

        :arg options: The oseo deliveryOptions
        :type options: pyxb.bundles.opengis.oseo.DeliveryOptionsType
        :arg order_type: The type of order being requested
        :type order_type: str
        :return: pyoseo.models.SelectedDeliveryOption
        """

        possibly_null = [
            options.onlineDataAccess,
            options.onlineDataDelivery,
            options.mediaDelivery.packageMedium if
                options.mediaDelivery is not None else None,
            options.mediaDelivery.shippingInstructions if
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
                    pass  # raise some sort of error
            elif options.onlineDataDelivery is not None:
                protocol = options.onlineDataDelivery.protocol
                if self._validate_online_data_delivery_protocol(protocol,
                                                                order_type):
                    odd = models.OnlineDataDelivery(protocol=protocol)
                    del_option.onlinedatadelivery = odd
                else:
                    pass  # raise some sort of error
            elif options.mediaDelivery is not None:
                medium = options.mediaDelivery.packageMedium
                if self._validate_media_delivery(medium, order_type):
                    md = models.MediaDelivery(package_medium=medium)
                    md.shipping_instructions = self._c(
                        options.mediaDelivery.shippingInstructions)
                    del_option.mediadelivery = md
                else:
                    pass  # raise some sort of error
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

    def _validate_order_type(self, requested_order_type):
        status = models.CustomizableItem.FAILED
        if self._order_type_enabled(requested_order_type):
            status = models.CustomizableItem.ACCEPTED
            if requested_order_type.automatic_approval:
                status = models.CustomizableItem.SUBMITTED
        return status

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

    def _validate_option(self, name, value):
        """Return a boolean indicating if the selected option is valid"""
        choices = [c.value for c in models.OptionChoice.objects.filter(
            option__name=name)]
        return True if value in choices or len(choices) == 0 else False
