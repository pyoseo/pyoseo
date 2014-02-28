'''
- Assuming that massive orders will come with some special reference


Creating the ParameterData element:

* create an appropriate XML Schema Definition file (xsd)
* generate pyxb bindings for the XML schema with:

  pyxbgen --schema-location=pyoseo.xsd --module=pyoseo_schema

* in ipython
  
  import pyxb.binding.datatypes as xsd
  import pyxb.bundles.opengis.oseo as oseo
  import pysoeo_schema

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

from lxml import etree
import pyxb
import pyxb.bundles.opengis.oseo as oseo
import pyxb.bundles.opengis.ows as ows_bindings
import sqlalchemy.orm.exc

#from pyoseo import app, db, models, tasks
from oseoserver import models

# TODO
# Implement the remaining Getstatus functionality
# Test it!

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
    }
    _db_order_type_map = {
        'product_order': 'PRODUCT_ORDER',
        'subscription': 'SUBSCRIPTION_ORDER',
        'massive_order': 'PRODUCT_ORDER',
    }
    MASSIVE_ORDER_REFERENCE = 'Massive order'

    def get_options(self, request, soap_version):
        '''
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

        raise NotImplementedError

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
        order_id = '1'
        if request.orderSpecification is not None:
            ord_spec = request.orderSpecification
            # order specification type of Submit

            creation_date = dt.datetime.utcnow()
            order = models.Order(
                status='Submitted',
                remark=ord_spec.orderRemark,
                created_on=creation_date,
                status_changed_on=creation_date,
                reference=ord_spec.orderReference,
                packaging=ord_spec.packaging,
                priority=ord_spec.priority
            )
            if ord_spec.orderType == 'PRODUCT_ORDER':
                if order.reference != self.MASSIVE_ORDER_REFERENCE:
                    order.order_type = 'product_order'
                else:
                    order.order_type = 'massive_order'
            elif ord_spec.orderType == 'SUBSCRIPTION_ORDER':
                order.order_type = 'subscription'
            else:
                raise NotImplementedError
            if ord_spec.deliveryInformation is not None:
                di = ord_spec.deliveryInformation
                del_info = models.DeliveryInformation()
                if di.mailAddress is not None:
                    del_info.first_name = di.mailAddress.firstName
                    del_info.last_name = di.mailAddress.lastName
                    del_info.company_ref = di.mailAddress.companyRef
                    del_info.street_address = di.mailAddress.streetAddress
                    del_info.city = di.mailAddress.city
                    del_info.state = di.mailAddress.state
                    del_info.postal_code = di.mailAddress.postalCode
                    del_info.country = di.mailAddress.country
                    del_info.post_box = di.mailAddress.post_box
                    del_info.telephone_number = di.mailAddress.telephoneNumber
                    del_info.fax = di.mailAddress.facsimileTelephoneNumber
                for oa in di.onlineAddress:
                    del_info.online_addresses.append(
                        models.OnlineAddress(
                            protocol=oa.protocol,
                            server_address=oa.serverAddress,
                            user_name=oa.userName,
                            user_password=oa.userPassword,
                            path=oa.path
                        )
                    )
                order.delivery_information = del_info
            if ord_spec.invoiceAddress is not None:
                ia = ord_spec.invoiceAddress
                order.invoice_address = models.InvoiceAddress(
                    first_name=ia.mailAddress.firstName,
                    last_name=ia.mailAddress.lastName,
                    company_ref=ia.mailAddress.companyRef,
                    street_address=ia.mailAddress.postalAddress.streetAddress,
                    city=ia.mailAddress.postalAddress.city,
                    state=ia.mailAddress.postalAddress.state,
                    postal_code=ia.mailAddress.postalAddress.postalCode,
                    country=ia.mailAddress.postalAddress.country,
                    post_box=ia.mailAddress.postalAddress.postBox,
                    telephone=ia.mailAddress.telephoneNumer,
                    fax=ia.mailAddress.facsimileTelephoneNumber
                )
            # add options
            if ord_spec.deliveryOptions is not None:
                order.delivery_options = self._set_delivery_options(
                                                    ord_spec.deliveryOptions)
            if order.order_type == 'product_order':
                # create a single batch with all of the defined order items
                batch = models.Batch(status=order.status)
                for oi in ord_spec.orderItem:
                    order_item = models.OrderItem(
                        item_id=oi.itemId,
                        status=batch.status,
                        created_on=creation_date,
                        status_changed_on=creation_date,
                        remark=oi.orderItemRemark,
                        product_order_options_id=oi.productOrderOptionsId,
                    )
                    # add order_item options
                    # add order_item scene selection
                    if oi.deliveryOptions is not None:
                        order_item.delivery_options = self._set_delivery_options(
                                                            oi.deliveryOptions)
                    # add order_item payment
                    order_item.identifier = oi.productId.identifier
                    order_item.collection_id = oi.productId.collectionId
                    batch.order_items.append(order_item)
                order.batches.append(batch)
            elif order.order_type == 'subscription':
                # do not create any batch yet, as there are no order items
                raise NotImplementedError
            elif order.order_type == 'massive_order':
                # break the order down into multiple batches
                raise NotImplementedError
        else:
            # quotation type of submit
            raise NotImplementedError
        order.user = models.User.query.filter_by(id=1).one()
        db.session.add(order)
        db.session.commit()
        tasks.process_order.delay(order.id)
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
                record = models.Order.query.filter_by(
                    id=int(request.orderId)).one()
                records.append(record)
            except sqlalchemy.orm.exc.NoResultFound:
                result = self._create_exception_report(
                    'InvalidOrderIdentifier',
                    'Invalid value for order',
                    soap_version,
                    locator=request.orderId
                )
                status_code = 400
        else: # 'order search' type of request
            query = models.Order.query
            if request.filteringCriteria.lastUpdate is not None:
                lu = request.filteringCriteria.lastUpdate
                query = query.filter(models.Order.status_changed_on >= lu)
            if request.filteringCriteria.lastUpdateEnd is not None:
                # workaround for a bug in the oseo.xsd that does not
                # assign a dateTime type to the lastUpdateEnd element
                lue = request.filteringCriteria.lastUpdateEnd.toxml()
                m = re.search(r'\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}Z)?', lue)
                try:
                    ts = dt.datetime.strptime(m.group(), '%Y-%m-%dT%H:%M:%SZ')
                except ValueError:
                    ts = dt.datetime.strptime(m.group(), '%Y-%m-%d')
                query = query.filter(models.Order.status_changed_on <= ts)
            if request.filteringCriteria.orderReference is not None:
                ref = request.filteringCriteria.orderReference
                query = query.filter(models.Order.reference == ref)
            statuses = [s for s in request.filteringCriteria.orderStatus]
            if any(statuses):
                query = query.filter(models.Order.status.in_(statuses))
            records = query.all()
        if result is None:
            response = self._generate_get_status_response(records, request)
            if soap_version is not None:
                result = self._wrap_soap(response, soap_version)
            else:
                result = response.toxml(encoding=self._encoding)
        return result, status_code

    def _generate_get_status_response(self, records, request):
        '''
        '''
        response = oseo.GetStatusResponse()
        response.status='success'
        for r in records:
            om = oseo.CommonOrderMonitorSpecification()
            om.orderType = self._db_order_type_map[r.order_type]
            om.orderId = str(r.id)
            om.orderStatusInfo = oseo.StatusType(
                status=r.status,
                additionalStatusInfo=r.additional_status_info,
                missionSpecificStatusInfo=r.mission_specific_status_info
            )
            om.orderDateTime = r.status_changed_on
            om.orderReference = r.reference
            om.orderRemark = r.remark
            if r.delivery_information is not None:
                om.deliveryInformation = oseo.DeliveryInformationType()
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
                    om.deliveryInformation.mailAddress = \
                            oseo.DeliveryAddressType()
                    om.deliveryInformation.mailAddress.firstName = \
                            r.delivery_information.first_name
                    om.deliveryInformation.mailAddress.lastName = \
                            r.delivery_information.last_name
                    om.deliveryInformation.mailAddress.companyRef= \
                            r.delivery_information.company_ref
                    om.deliveryInformation.mailAddress.postalAddress=pyxb.BIND()
                    om.deliveryInformation.mailAddress.postalAddress.streetAddress=\
                            r.delivery_information.street_address
                    om.deliveryInformation.mailAddress.postalAddress.city=\
                            r.delivery_information.city
                    om.deliveryInformation.mailAddress.postalAddress.state=\
                            r.delivery_information.state
                    om.deliveryInformation.mailAddress.postalAddress.postalCode=\
                            r.delivery_information.postal_code
                    om.deliveryInformation.mailAddress.postalAddress.country=\
                            r.delivery_information.country
                    om.deliveryInformation.mailAddress.postalAddress.postBox=\
                            r.delivery_information.post_box
                    om.deliveryInformation.mailAddress.telephoneNumber = \
                            r.delivery_information.telephone_number
                    om.deliveryInformation.mailAddress.facsimileTelephoneNumber = \
                            r.delivery_information.fax
                for oa in r.delivery_information.online_addresses:
                    om.deliveryInformation.onlineAddress.append(
                            oseo.OnlineAddressType())
                    om.deliveryInformation.onlineAddress[-1].protocol = \
                            oa.protocol
                    om.deliveryInformation.onlineAddress[-1].serverAddress = \
                            oa.server_address
                    om.deliveryInformation.onlineAddress[-1].userName = \
                            oa.user_name
                    om.deliveryInformation.onlineAddress[-1].userPassword = \
                            oa.user_password
                    om.deliveryInformation.onlineAddress[-1].path = oa.path
            if r.invoice_address is not None:
                om.invoiceAddress = oseo.DeliveryAddressType()
                om.invoiceAddress.firstName = r.invoice_address.first_name
                om.invoiceAddress.lastName = r.invoice_address.last_name
                om.invoiceAddress.companyRef = r.invoice_address.company_ref
                om.invoiceAddress.postalAddress=pyxb.BIND()
                om.invoiceAddress.postalAddress.streetAddress=\
                        r.invoice_address.street_address
                om.invoiceAddress.postalAddress.city=\
                        r.invoice_address.city
                om.invoiceAddress.postalAddress.state=\
                        r.invoice_address.state
                om.invoiceAddress.postalAddress.postalCode=\
                        r.invoice_address.postal_code
                om.invoiceAddress.postalAddress.country=\
                        r.invoice_address.country
                om.invoiceAddress.postalAddress.postBox=\
                        r.invoice_address.post_box
                om.invoiceAddress.telephoneNumber = \
                        r.invoice_address.telephone_number
                om.invoiceAddress.facsimileTelephoneNumber = \
                        r.invoice_address.fax
            om.packaging = r.packaging
            # add any 'option' elements
            if r.delivery_options is not None:
                om.deliveryOptions = self._get_delivery_options(r)
            om.priority = r.priority
            if request.presentation == 'full':
                if r.order_type == 'product_order':
                    for batch in r.batches:
                        for oi in batch.order_items:
                            sit = oseo.CommonOrderStatusItemType()
                            # TODO
                            # add the other optional elements
                            sit.itemId = str(oi.id)
                            sit.productId = oi.identifier
                            if oi.product_order_options_id is not None:
                                sit.productOrderOptionsId = \
                                        oi.product_order_options_id
                            if oi.remark is not None:
                                sit.orderItemRemark = oi.remark
                            if oi.collection_id is not None:
                                sit.collectionId = oi.collection_id
                            # add any 'option' elements that may be present
                            # add any 'sceneSelection' elements that may be present
                            if oi.delivery_options is not None:
                                sit.deliveryOptions = self._get_delivery_options(oi)
                            # add any 'payment' elements that may be present
                            # add any 'extension' elements that may be present
                            sit.orderItemStatusInfo = oseo.StatusType()
                            sit.orderItemStatusInfo.status = oi.status
                            if oi.additional_status_info is not None:
                                sit.orderItemStatusInfo.additionalStatusInfo =\
                                        oi.additional_status_info
                            if oi.mission_specific_status_info is not None:
                                sit.orderItemStatusInfo.missionSpecificStatusInfo=\
                                        oi.mission_specific_status_info
                            om.orderItem.append(sit)
                else:
                    raise NotImplementedError
            response.orderMonitorSpecification.append(om)
        return response

    def process_request(self, request_data):
        '''
        :arg request_data: The raw request data, as was captured by Flask
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
                app.logger.debug('SOAP 1.2 request')
                response_headers['Content-Type'] = 'application/soap+xml'
            else:
                app.logger.debug('SOAP 1.1 request')
                response_headers['Content-Type'] = 'text/xml'
        else:
            app.logger.debug('Non SOAP request')
            data = element
            response_headers['Content-Type'] = 'application/xml'
        schema_instance = self._parse_xml(data)
        op_map = {
            'GetStatusRequestType': self.get_status,
            'SubmitOrderRequestType': self.submit,
        }
        operation = op_map[schema_instance.__class__.__name__]
        result, status_code = operation(schema_instance, soap_version)
        return result, status_code, response_headers

    def _set_delivery_options(self, options):
        '''
        Create a database record with the input delivery options.

        :arg options: The oseo deliveryOptions
        :type delivery_options: pyxb.bundles.opengis.oseo.DeliveryOptionsType
        :return: pyoseo.models.DeliveryOption
        '''

        oda = options.onlineDataAccess
        odd = options.onlineDataDelivery
        md = options.mediaDelivery
        result = models.DeliveryOption(
            online_data_access_protocol=oda.protocol if oda else None,
            online_data_delivery_protocol=odd.protocol if odd else None,
            media_delivery_package_medium=\
                    options.mediaDelivery.packageMedium if md else None,
            media_delivery_shipping_instructions=\
                    options.mediaDelivery.shippingInstructions if md else None,
            number_of_copies=options.numberOfCopies,
            annotation=options.productAnnotation,
            special_instructions=options.specialInstructions
        )
        return result

    def _get_delivery_options(self, db_item):
        '''
        Return the delivery options for an input database item.

        :arg db_item: the database record model that has the delivery options
        :type db_item: pyoseo.models.CustomizableItem
        :return: A pyxb object with the delivery options
        '''

        do = db_item.delivery_options
        dot = oseo.DeliveryOptionsType()
        if do.online_data_access_protocol is not None:
            dot.onlineDataAccess = pyxb.BIND()
            dot.onlineDataAccess.protocol = do.online_data_access_protocol
        elif do.online_data_delivery_protocol is not None:
            dot.onlineDataDelivery = pyxb.BIND()
            dot.onlineDataDelivery.protocol = do.online_data_delivery_protocol
        elif do.media_delivery_package_medium is not None:
            dot.mediaDelivery = pyxb.BIND()
            dot.mediaDelivery.packageMedium = do.media_delivery_package_medium
            if do.media_delivery_shipping_instructions is not None:
                dot.mediaDelivery.shippingInstructions = \
                        do.media_delivery_shipping_instructions
        if do.number_of_copies is not None:
            dot.numberOfCopies = do.number_of_copies
        if do.annotation is not None:
            dot.productAnnotation = do.annotation
        if do.special_instructions is not None:
            dot.specialInstructions = do.special_instructions
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
