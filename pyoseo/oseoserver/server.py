'''
- Assuming that massive orders will come with some special reference


Creating the ParameterData element:

* create an appropriate XML Schema Definition file (xsd)
* generate pyxb bindings for the XML schema with:

  pyxbgen --schema-location=pyoseo.xsd --module=pyoseo_schema

* in ipython
  
  import pyxb.binding.datatypes as xsd
  import pyxb.bundles.opengis.oseo as oseo
  import pyoseo_schema

  pd = oseo.ParameterData()
  pd.encoding = 'XMLEncoding'
  pd.values = xsd.anyType()
  pd.values.append(pyoseo_schema.fileFormat('o valor'))
  pd.values.append(pyoseo_schema.projection('a projeccao'))
  pd.toxml()


'''

import logging
import re
import datetime as dt

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.conf import settings as django_settings
from lxml import etree
import pyxb
import pyxb.bundles.opengis.oseo as oseo
import pyxb.bundles.opengis.swe_2_0 as swe
import pyxb.bundles.opengis.ows as ows_bindings

from oseoserver import models, tasks

logger = logging.getLogger('.'.join(('pyoseo', __name__)))

class OseoServer(object):

    _oseo_version = '1.0.0'
    _encoding = 'utf-8'
    _namespaces = {
        'soap': 'http://www.w3.org/2003/05/soap-envelope',
        'soap1.1': 'http://schemas.xmlsoap.org/soap/envelope/',
        'ows': 'http://www.opengis.net/ows/2.0',
    }
    _exception_codes = {
            'InvalidOrderIdentifier': 'client',
            'UnsupportedCollection': 'client',
    }
    MASSIVE_ORDER_REFERENCE = 'Massive order'

    def process_request(self, request_data):
        '''
        Entry point for the server.

        This method receives the raw request data as a string and then parses
        it into a valid pyxb OSEO object. It will then send the request to the
        appropriate method according to the requested OSEO operation.

        :arg request_data: The raw request data
        :type request_data: str
        :return: The response XML document, as a string, the HTTP status
        code and a dictionary with HTTP headers to be set by the wsgi server
        :rtype: tuple(str, int, dict)
        '''

        element = etree.fromstring(request_data)
        response_headers = dict()
        soap_version = self._is_soap(element)
        if soap_version is not None:
            data = self._get_soap_data(element, soap_version)
            if soap_version == '1.2':
                logger.debug('SOAP 1.2 request')
                response_headers['Content-Type'] = 'application/soap+xml'
            else:
                logger.debug('SOAP 1.1 request')
                response_headers['Content-Type'] = 'text/xml'
        else:
            logger.debug('Non SOAP request')
            data = element
            response_headers['Content-Type'] = 'application/xml'
        schema_instance = self._parse_xml(data)
        op_map = {
            'GetStatusRequestType': self.get_status,
            'SubmitOrderRequestType': self.submit,
            'OrderOptionsRequestType': self.get_options,
        }
        operation = op_map[schema_instance.__class__.__name__]
        result, status_code = operation(schema_instance, soap_version)
        return result, status_code, response_headers

    def get_options(self, request, soap_version):
        '''
        Implements the OSEO GetOptions operation.


        :arg request: The instance with the request parameters
        :type request: pyxb.bundles.opengis.raw.oseo.OrderOptionsRequestType
        :arg soap_version: Version of the SOAP protocol in use
        :type soap_version: str or None
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
        '''

        status_code = 200
        result = None
        if any(request.identifier): # product identifier query
            for id in request.identifier:
                raise NotImplementedError
        elif request.collectionId is not None: # product or collection query
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
                    available_options = models.Option.objects.filter(
                        Q(product__collection_id=request.collectionId) | \
                        Q(product=None)
                    ).filter(optionordertype__order_type__name=ot)
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
                result = self._create_exception_report(
                    'UnsupportedCollection',
                    'Subscription not supported',
                    soap_version,
                    locator=request.collectionId
                )
                status_code = 400
        elif request.taskingRequestId is not None:
            raise NotImplementedError
        if result is None:
            if soap_version is not None:
                result = self._wrap_soap(response, soap_version)
            else:
                result = response.toxml(encoding=self._encoding)
        return result, status_code

    def _get_order_options(self, option_group, options, delivery_options,
                           order_type, order_item=None):
        '''
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
        '''

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

    def submit(self, request, soap_version):
        '''
        Implements the OSEO Submit operation.

        * save order details in the database
        * generate the appropriate response
        * if it is a normal order, send the task to celery
        * if it is a subscription or a massive order, send an email to admins

        :arg request: The instance with the request parameters
        :type request: pyxb.bundles.opengis.raw.oseo.GetStatusRequestType
        :arg soap_version: Version of the SOAP protocol in use
        :type soap_version: str or None
        :return: The XML response object and the HTTP status code
        :rtype: tuple(str, int)
        '''

        status_code = 200
        if request.orderSpecification is not None:
            # order specification type of Submit
            ord_spec = request.orderSpecification
            creation_date = dt.datetime.utcnow()
            order = models.Order(
                status='Submitted',
                created_on=creation_date,
                status_changed_on=creation_date,
                remark=self._c(ord_spec.orderRemark),
                reference=self._c(ord_spec.orderReference),
                packaging=self._c(ord_spec.packaging),
                priority=self._c(ord_spec.priority)
            )

            if ord_spec.orderType == models.OrderType.PRODUCT_ORDER:
                ref = self._c(ord_spec.orderReference)
                if ref == self.MASSIVE_ORDER_REFERENCE:
                    order.order_type = models.OrderType.objects.get(
                            name=models.OrderType.MASSIVE_ORDER)
                    order.approved = False
                else:
                    order.order_type = models.OrderType.objects.get(
                            name=models.OrderType.PRODUCT_ORDER)
                    order.approved = True
            order.user = models.User.objects.get(id=1) # for testing purposes only
            order.save()
            if ord_spec.deliveryInformation is not None:
                di = ord_spec.deliveryInformation
                del_info = models.DeliveryInformation()
                if di.mailAddress is not None:
                    del_info.first_name = self._c(di.mailAddress.firstName)
                    del_info.last_name = self._c(di.mailAddress.lastName)
                    del_info.company_ref = self._c(di.mailAddress.companyRef)
                    del_info.street_address = self._c(
                            di.mailAddress.streetAddress)
                    del_info.city = self._c(di.mailAddress.city)
                    del_info.state = self._c(di.mailAddress.state)
                    del_info.postal_code = self._c(di.mailAddress.postalCode)
                    del_info.country = self._c(di.mailAddress.country)
                    del_info.post_box = self._c(di.mailAddress.post_box)
                    del_info.telephone_number = self._c(
                            di.mailAddress.telephoneNumber)
                    del_info.fax = self._c(
                            di.mailAddress.facsimileTelephoneNumber)
                del_info.save()
                for oa in di.onlineAddress:
                    del_info.onlineaddress_set.add(
                        models.OnlineAddress(
                            protocol=oa.protocol,
                            server_address=oa.serverAddress,
                            user_name=self._c(oa.userName),
                            user_password=self._c(oa.userPassword),
                            path=self._c(oa.path)
                        )
                    )
                order.delivery_information = del_info
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
            # add options
            if ord_spec.deliveryOptions is not None:
                d_opts = self._set_delivery_options(
                    ord_spec.deliveryOptions,
                    order.order_type.name
                )
                order.deliveryoption = d_opts
            order.save()
            if order.order_type.name == models.OrderType.PRODUCT_ORDER:
                # create a single batch with all of the defined order items
                batch = models.Batch(order=order)
                batch.save()
                for oi in ord_spec.orderItem:
                    order_item = models.OrderItem(
                        item_id=oi.itemId,
                        status=batch.status,
                        created_on=creation_date,
                        status_changed_on=creation_date,
                        remark=self._c(oi.orderItemRemark),
                        # this is probabbly not needed here
                        product_order_options_id=self._c(
                            oi.productOrderOptionsId),
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
                    batch.orderitem_set.add(order_item)
                    order_item.save()
                #order.batch_set.add(batch)
            elif order.order_type.name == 'subscription':
                # do not create any batch yet, as there are no order items
                raise NotImplementedError
            elif order.order_type.name == 'massive_order':
                # break the order down into multiple batches
                raise NotImplementedError
        else:
            # quotation type of submit
            raise NotImplementedError
        #tasks.process_order.delay(order.id)
        response = oseo.SubmitAck(status='success')
        response.orderId = str(order.id)
        if soap_version is not None:
            result = self._wrap_soap(response, soap_version)
        else:
            result = response.toxml(encoding=self._encoding)
        return result, status_code

    def get_status(self, request, soap_version):
        '''
        Implements the OSEO Getstatus operation.

        See section 14 of the OSEO specification for details on the
        Getstatus operation.

        :arg request: The instance with the request parameters
        :type request: pyxb.bundles.opengis.raw.oseo.GetStatusRequestType
        :arg soap_version: Version of the SOAP protocol in use
        :type soap_version: str or None
        :return: The XML response object and the HTTP status code
        :rtype: tuple(str, int)
        '''

        status_code = 200
        records = []
        result = None
        if request.orderId is not None: # 'order retrieve' type of request
            try:
                records = models.Order.objects.filter(id=int(request.orderId))
            except ObjectDoesNotExist:
                result = self._create_exception_report(
                    'InvalidOrderIdentifier',
                    'Invalid value for order',
                    soap_version,
                    locator=request.orderId
                )
                status_code = 400
        else: # 'order search' type of request
            records = models.Order.objects

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
        if result is None:
            response = self._generate_get_status_response(records,
                                                          request.presentation)
            if soap_version is not None:
                result = self._wrap_soap(response, soap_version)
            else:
                result = response.toxml(encoding=self._encoding)
        return result, status_code

    def _generate_get_status_response(self, records, presentation):
        '''
        :arg records:
        :type records: either a one element list with a pyoseo.models.Order
                       or a django queryset, that will be evaluated to an
                       list of pyoseo.models.Order while iterating.
        :arg presentation:
        :type presentation: str
        '''

        response = oseo.GetStatusResponse()
        response.status='success'
        for r in records:
            om = oseo.CommonOrderMonitorSpecification()
            if r.order_type.name in(models.OrderType.PRODUCT_ORDER,
                    models.OrderType.MASSIVE_ORDER):
                om.orderType = models.OrderType.PRODUCT_ORDER
            elif r.order_type.name == models.OrderType.SUBSCRIPTION_ORDER:
                om.orderType = models.Order.SUBSCRIPTION_ORDER
            om.orderId = str(r.id)
            om.orderStatusInfo = oseo.StatusType(
                status=r.status,
                additionalStatusInfo=self._n(r.additional_status_info),
                missionSpecificStatusInfo=self._n(
                    r.mission_specific_status_info)
            )
            om.orderDateTime = r.status_changed_on
            om.orderReference = self._n(r.reference)
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
                    r.delivery_information.telephone_number,
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
            except ObjectDoesNotExist:
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
            except ObjectDoesNotExist:
                pass
            om.packaging = self._n(r.packaging)
            # add any 'option' elements
            om.deliveryOptions = self._get_delivery_options(r)
            om.priority = self._n(r.priority)
            if presentation == 'full':
                if r.order_type.name == models.OrderType.PRODUCT_ORDER:
                    for batch in r.batches.all():
                        for oi in batch.order_items.all():
                            sit = oseo.CommonOrderStatusItemType()
                            # TODO
                            # add the other optional elements
                            sit.itemId = str(oi.id)
                            # oi.identifier is guaranteed to be non empty for
                            # normal product orders
                            sit.productId = oi.identifier
                            sit.productOrderOptionsId = oi.option_group.name
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

    def _set_delivery_options(self, options, order_type):
        '''
        Create a database record with the input delivery options.

        :arg options: The oseo deliveryOptions
        :type options: pyxb.bundles.opengis.oseo.DeliveryOptionsType
        :arg order_type: The type of order being requested
        :type order_type: str
        :return: pyoseo.models.SelectedDeliveryOption
        '''

        possibly_null = [options.onlineDataAccess, options.onlineDataDelivery,
                         options.mediaDelivery.packageMedium,
                         options.mediaDelivery.shippingInstructions,
                         options.numberOfCopies, options.productAnnotation,
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
        for dot in models.DeliveryOptionsType.objects.all():
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
        for dot in models.DeliveryOptionsType.objects.all():
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
        for dot in models.DeliveryOptionsType.objects.all():
            if hasattr(dot.delivery_option, 'mediadelivery') and \
                    dot.order_type.name == order_type:
                m = dot.delivery_option.mediadelivery.package_medium
                available_media.append(m)
        result = False
        if package_medium in available_media:
            result = True
        return result

    def _get_delivery_options(self, db_item):
        '''
        Return the delivery options for an input database item.

        :arg db_item: the database record model that has the delivery options
        :type db_item: pyoseo.models.CustomizableItem
        :return: A pyxb object with the delivery options
        '''

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

    def _is_soap(self, request_element):
        '''
        Look for SOAP requests.

        Although the OSEO spec states that SOAP v1.2 is to be used, pyoseo
        accepts both SOAP v1.1 and SOAP v1.2

        :arg request_element: the raw input request
        :type request_data: lxml.etree.Element instance
        '''

        ns, tag = request_element.tag.split('}')
        ns = ns[1:]
        result = None
        if tag == 'Envelope':
            if ns == self._namespaces['soap']:
                result = '1.2'
            elif ns == self._namespaces['soap1.1']:
                result = '1.1'
        return result

    def _parse_xml(self, xml):
        '''
        :arg xml: the XML element with the request
        :xml type: lxml.etree.Element
        :return: The instance generated by pyxb
        '''

        document = etree.tostring(xml, encoding=self._encoding,
                                  pretty_print=True)
        oseo_request = oseo.CreateFromDocument(document)
        return oseo_request

    def _create_exception_report(self, code, text, soap_version, locator=None):
        '''
        :arg code: OSEO exception code. Can be any of the defined
        exceptionCode values in the OSEO and OWS Common specifications.
        :type code: str
        :arg text: Text to display in the exception report
        :type text: str
        :arg soap_version: Version of the SOAP protocol to use, if any
        :type soap_version: str or None
        :arg locator: value to display in the 'locator' field
        :type locator: str
        :return: A string with the XML exception report
        '''

        exception = ows_bindings.Exception(exceptionCode=code)
        if locator is not None:
            exception.locator = locator
        exception.append(text)
        exception_report = ows_bindings.ExceptionReport(
                version=self._oseo_version)
        exception_report.append(exception)
        if soap_version is not None:
            soap_code = self._exception_codes[code]
            result = self._wrap_soap_fault(exception_report, soap_code,
                                           soap_version)
        else:
            result = exception_report.toxml(encoding=self._encoding)
        return result

    def _get_soap_data(self, element, soap_version):
        '''
        :arg element: The full request object
        :type element: lxml.etree.Element
        :arg soap_version: The SOAP version in use
        :type soap_version: str
        :return: The contents of the soap:Body element.
        :rtype: lxml.etree.Element
        '''

        if soap_version == '1.2':
            path = '/soap:Envelope/soap:Body/*[1]'
        else:
            path = '/soap1.1:Envelope/soap1.1:Body/*[1]'
        xml_element = element.xpath(path, namespaces=self._namespaces)
        return xml_element[0]

    def _wrap_soap(self, response, soap_version):
        '''
        :arg response: the pyxb instance with the previously generated response
        :type response: pyxb.bundles.opengis.oseo
        :arg soap_version: The SOAP version in use
        :type soap_version: str
        :return: A string with the XML response
        '''

        soap_env_ns = {
            'ows': self._namespaces['ows'],
        }
        if soap_version == '1.2':
            soap_env_ns['soap'] = self._namespaces['soap']
        else:
            soap_env_ns['soap'] = self._namespaces['soap1.1']
        soap_env = etree.Element('{%s}Envelope' % soap_env_ns['soap'],
                                 nsmap=soap_env_ns)
        soap_body = etree.SubElement(soap_env, '{%s}Body' % \
                                     soap_env_ns['soap'])

        response_string = response.toxml(encoding=self._encoding)
        response_string = response_string.encode(self._encoding)
        response_element = etree.fromstring(response_string)
        soap_body.append(response_element)
        return etree.tostring(soap_env, encoding=self._encoding,
                              pretty_print=True)

    def _wrap_soap_fault(self, exception_report, soap_code, soap_version):
        '''
        :arg exception_report: The pyxb instance with the previously generated
                               exception report
        :type exception_report: pyxb.bundles.opengis.ows.ExceptionReport
        :arg soap_code: Can be either 'server' or 'client'
        :type soap_code: str
        :arg soap_version: The SOAP version in use
        :type soap_version: str
        '''

        code_msg = 'soap:%s' % soap_code.capitalize()
        reason_msg = '%s exception was encoutered' % soap_code.capitalize()
        exception_string = exception_report.toxml(encoding=self._encoding)
        exception_string = exception_string.encode(self._encoding)
        exception_element = etree.fromstring(exception_string)
        soap_env_ns = {
            'ows': self._namespaces['ows'],
        }
        if soap_version == '1.2':
            soap_env_ns['soap'] = self._namespaces['soap']
        else:
            soap_env_ns['soap'] = self._namespaces['soap1.1']
        soap_env = etree.Element('{%s}Envelope' % soap_env_ns['soap'],
                                 nsmap=soap_env_ns)
        soap_body = etree.SubElement(soap_env, '{%s}Body' % \
                                     soap_env_ns['soap'])
        soap_fault = etree.SubElement(soap_body, '{%s}Fault' % \
                                      soap_env_ns['soap'])
        if soap_version == '1.2':
            fault_code = etree.SubElement(soap_fault, '{%s}Code' % \
                                          soap_env_ns['soap'])
            code_value = etree.SubElement(fault_code, '{%s}Value' % \
                                          soap_env_ns['soap'])
            code_value.text = code_msg
            fault_reason = etree.SubElement(soap_fault, '{%s}Reason' % \
                                            soap_env_ns['soap'])
            reason_text = etree.SubElement(fault_reason, '{%s}Text' % \
                                           soap_env_ns['soap'])
            reason_text.text = reason_msg
            fault_detail = etree.SubElement(soap_fault, '{%s}Detail' % \
                                            soap_env_ns['soap'])
            fault_detail.append(exception_element)
        else:
            fault_code = etree.SubElement(soap_fault, 'faultcode')
            fault_code.text = code_msg
            fault_string = etree.SubElement(soap_fault, 'faultstring')
            fault_string.text = reason_msg
            fault_actor = etree.SubElement(soap_fault, 'faultactor')
            fault_actor.text = ''
            detail = etree.SubElement(soap_fault, 'detail')
            detail.append(exception_element)
        return etree.tostring(soap_env, encoding=self._encoding,
                              pretty_print=True)

    def _c(self, value):
        '''
        Convert between a None and an empty string.

        This function translates pyxb's empty elements, which are stored as
        None into django's empty values, which are stored as an empty string.
        '''
        return '' if value is None else str(value)

    def _n(self, value):
        '''
        Convert between an empty string and a None

        This function is translates django's empty elements, which are stored
        as empty strings into pyxb empty elements, which are stored as None.
        '''
        return None if value == '' else value
