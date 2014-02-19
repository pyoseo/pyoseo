'''
'''

import logging

from lxml import etree
import pyxb.bundles.opengis.oseo as oseo
import pyxb.bundles.opengis.ows as ows_bindings
import sqlalchemy.orm.exc

from pyoseo import app, models

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
        'normal_order': 'PRODUCT_ORDER',
        'subscription_order': 'SUBSCRIPTION_ORDER',
        'massive_order_order': 'PRODUCT_ORDER',
    }

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
            records = []

        # This is wrong, the exceptionReport is not being generated properly...
        response = oseo.GetStatusResponse()
        response.status='success'
        for record in records:
            order_monitor = oseo.CommonOrderMonitorSpecification()
            order_monitor.orderType = self._db_order_type_map[
                                                       record.order_type]
            order_monitor.orderId = str(record.id)
            order_monitor.orderStatusInfo = oseo.StatusType(
                status=record.status,
                additionalStatusInfo=record.additional_status_info,
                missionSpecificStatusInfo=record.mission_specific_status_info
            )
            order_monitor.orderDateTime = record.status_changed_on
            order_monitor.orderReference = record.reference
            order_monitor.orderRemark = record.remark
            order_monitor.packaging = record.packaging
            order_monitor.priority = record.priority
            if request.presentation == 'full':
                raise NotImplementedError
            response.orderMonitorSpecification.append(order_monitor)
        if soap_version is not None:
            result = self._wrap_soap(response, soap_version)
        else:
            result = response.toxml(encoding=self._encoding)
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
        }
        operation = op_map[schema_instance.__class__.__name__]
        result, status_code = operation(schema_instance, soap_version)
        return result, status_code, response_headers

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
