'''
'''

import logging

from lxml import etree
import pyxb.bundles.opengis.oseo as oseo
import pyxb.bundles.opengis.ows as ows_bindings
import sqlalchemy.orm.exc

from pyoseo import app, models

# TODO
# Implement the remaining Getstatus functinality
# Test it!

class OseoServer(object):

    _oseo_version = '1.0.0'
    _encoding = 'utf-8'
    _namespaces = {
        'soap': 'http://www.w3.org/2003/05/soap-envelope',
        'ows': 'http://www.opengis.net/ows/2.0',
    }
    _exception_codes = {
            'InvalidOrderIdentifier': 'client',
    }

    def get_status(self, request, is_soap):
        '''
        Implements the OSEO Getstatus operation.

        See section 14 of the OSEO specification for details on the
        Getstatus operation.

        GetStatus can be used in two ways:

        * Order search, when the request has the filteringCriteria element.
          Supports the folowing criteria:

            * lastUpdate
            * lastUpdateEnd
            * orderStatus
            * orderReference

        * Order retrieve, when the request has the orderId element

        GetStatus results can be presented in two ways:

        * brief
        * full

        The OSEO specification reccomends brief be used with order search
        and full with order retrieve, but this is not mandatory

        The response to a GetStatus request shall return:

        * all the order parameters specified in the previous Submit operation
        * Plus the status of the specified order

        The response to a Getstatus with brief presentation shall return
        overall order onitoring information but not any information on specific
        order items

        The response to a GetStatus with full presentation should return all
        the information returned by the brief presentation plus the status
        information of every order item

        The response to a GetStatus shall return the order date and time

        The response shall include the order type (PRODUCT_ORDER,
        SUBSCRIPTION_ORDER, TASKING_ORDER)


        :arg request: The instance with the request parameters
        :type request: pyxb.bundles.opengis.raw.oseo.GetStatusRequestType
        :arg is_soap: Should the response be wrapped in a SOAP envelop?
        :type is_soap: bool
        :return: The XML response object and the HTTP status code
        :rtype: tuple(str, int)
        '''

        status_code = 200
        if request.orderId is not None: # 'order retrieve' type of request
            try:
                record = models.Order.query.filter_by(
                    id=int(request.orderId)).one()
                if request.presentation == 'full':
                    raise NotImplementedError
                response = oseo.GetStatusResponse(
                    status='success',
                    orderMonitorSpecification=[
                        oseo.CommonOrderMonitorSpecification(
                            orderId=str(record.id),
                            orderType='PRODUCT_ORDER',
                            orderStatusInfo=oseo.StatusType(
                                status=record.status
                            )
                        )
                    ]
                )
                if is_soap:
                    result = self._wrap_soap(response)
                else:
                    result = response.toxml(encoding=self._encoding)
            except sqlalchemy.orm.exc.NoResultFound:
                result = self._create_exception_report(
                    'InvalidOrderIdentifier',
                    'Invalid value for order',
                    is_soap,
                    locator=request.orderId
                )
                status_code = 400
        else: # 'order search' type of request
            raise NotImplementedError
        return result, status_code

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
        if self._is_soap(element):
            app.logger.debug('SOAP request')
            is_soap = True
            data = self._get_soap_data(element)
            # SOAP 1.2, as defined in the OSEO specification
            response_headers['Content-Type'] = 'application/soap+xml'
        else:
            app.logger.debug('Non SOAP request')
            is_soap = False
            data = element
            response_headers['Content-Type'] = 'application/xml'
        schema_instance = self._parse_xml(data)
        op_map = {
            'GetStatusRequestType': self.get_status,
        }
        operation = op_map[schema_instance.__class__.__name__]
        result, status_code = operation(schema_instance, is_soap)
        return result, status_code, response_headers

    def _is_soap(self, request_element):
        '''
        :arg request_element: the raw input request
        :type request_data: lxml.etree.Element instance
        '''

        ns, tag = request_element.tag.split('}')
        ns = ns[1:]
        result = False
        if tag == 'Envelope' and ns == self._namespaces['soap']:
            result = True
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

    def _create_exception_report(self, code, text, soap, locator=None):
        '''
        :arg code: OSEO exception code. Can be any of the defined
        exceptionCode values in the OSEO and OWS Common specifications.
        :type code: str
        :arg text: Text to display in the exception report
        :type text: str
        :arg soap: Should the exception report be wrapped in a SOAP envelop?
        :type soap: bool
        :arg locator: value to display in the 'locator' field
        :type locator: str
        :return: pyxb.bundles.opengis.raw.ows.ExceptionReport
        '''

        exception = ows_bindings.Exception(exceptionCode=code)
        if locator is not None:
            exception.locator = locator
        exception.append(text)
        exception_report = ows_bindings.ExceptionReport(
                version=self._oseo_version)
        exception_report.append(exception)
        if soap:
            soap_code = self._exception_codes[code]
            result = self._wrap_soap_fault(exception_report, soap_code)
        else:
            result = exception_report.toxml(encoding=self._encoding)
        return result

    def _get_soap_data(self, element):
        '''
        :arg element: The full request object
        :type element: lxml.etree.Element
        :return: The contents of the soap:Body element.
        :rtype: lxml.etree.Element
        '''

        xml_element = element.xpath('/soap:Envelope/soap:Body/*[1]',
                                     namespaces=self._namespaces)
        return xml_element[0]

    def _wrap_soap(self, response):
        '''
        :arg response: the XML response
        :type response: str
        '''

        raise NotImplementedError

    def _wrap_soap_fault(self, exception_report, soap_code):
        '''
        :arg exception_report: XML string with the previously generated
        exception report
        :type exception_report: str
        :arg soap_code: Can be either 'server' or 'client'
        '''

        soap_env_ns = self._namespaces.copy()
        soap_env = etree.Element('{%s}Envelope' % self._namespaces['soap'],
                                 nsmap=soap_env_ns)
        soap_body = etree.SubElement(soap_env, '{%s}Body' % \
                                     self._namespaces['soap'])
        soap_fault = etree.SubElement(soap_body, '{%s}Fault' % \
                                      self._namespaces['soap'])
        fault_code = etree.SubElement(soap_fault, '{%s}Code' % \
                                      self._namespaces['soap'])
        code_value = etree.SubElement(fault_code, '{%s}Value' % \
                                      self._namespaces['soap'])
        code_value.text = 'soap: %s' % soap_code
        fault_reason = etree.SubElement(soap_fault, '{%s}Reason' % \
                                        self._namespaces['soap'])
        reason_text = etree.SubElement(fault_reason, '{%s}Text' % \
                                       self._namespaces['soap'])
        reason_text.text = '%s exception was encoutered' % \
                           soap_code.capitalize()
        fault_detail = etree.SubElement(soap_fault, '{%s}Detail' % \
                                        self._namespaces['soap'])
        exception_string = exception_report.toxml(encoding=self._encoding)
        exception_string = exception_string.encode(self._encoding)
        exception_element = etree.fromstring(exception_string)
        fault_detail.append(exception_element)
        return etree.tostring(soap_env, encoding=self._encoding,
                              pretty_print=True)
