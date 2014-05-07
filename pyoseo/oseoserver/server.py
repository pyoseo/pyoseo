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
import importlib

from django.conf import settings as django_settings
from lxml import etree
import pyxb.bundles.opengis.oseo as oseo
import pyxb.bundles.opengis.ows as ows_bindings

from oseoserver import errors

logger = logging.getLogger('.'.join(('pyoseo', __name__)))

class OseoServer(object):

    _oseo_version = '1.0.0'
    _encoding = 'utf-8'
    _namespaces = {
        'soap': 'http://www.w3.org/2003/05/soap-envelope',
        'soap1.1': 'http://schemas.xmlsoap.org/soap/envelope/',
        'wsse': 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-' \
                'wssecurity-secext-1.0.xsd',
        'ows': 'http://www.opengis.net/ows/2.0',
    }
    _exception_codes = {
            'AuthorizationFailed': 'client',
            'AuthenticationFailed': 'client',
            'InvalidOrderIdentifier': 'client',
            'UnsupportedCollection': 'client',
    }
    MASSIVE_ORDER_REFERENCE = 'Massive order'

    _operation_classes = {
        'GetStatusRequestType': 'oseoserver.operations.getstatus.' \
                                'GetStatus',
        'SubmitOrderRequestType': 'oseoserver.operations.submit.Submit',
        'DescribeResultAccessRequestType': 'oseoserver.operations.' \
                                           'describeresultaccess.' \
                                           'DescribeResultAccess',
        'OrderOptionsRequestType': 'oseoserver.operations.getoptions.' \
                                   'GetOptions',
    }

    def authenticate_request(self, request_element, operation, soap_version):
        '''
        Authenticate an OSEO request.

        Request authentication can be customized according to the 
        needs of each ordering server. This method plugs into that by
        trying to load an external authentication class.

        The python path to the authentication class must be defined in
        the django settings module, and use the name 
        'OSEOSERVER_AUTHENTICATION_CLASS'.

        Authentication classes must provide the method:

        authenticate_request(request_element, soap_version)

        This method must return a two-value tuple with the following:

        * a boolean indicating if authentication has been successfull
        * a string with either the name of the user that has been successfully
          authenticated or an error message specifying what went wrong with
          the authentication process

        :arg request_element: The full request object
        :type request_element: lxml.etree.Element
        :arg soap_version: The SOAP version in use
        :type soap_version: str or None
        :return: The username of the end user that is responsible for this 
                 request
        :rtype: str
        '''

        auth_class = getattr(
            django_settings, 'OSEOSERVER_AUTHENTICATION_CLASS', None)
        if auth_class is not None:
            try:
                module_path, sep, class_name = auth_class.rpartition('.')
                logger.debug('module_path: {}'.format(module_path))
                logger.debug('class_name: {}'.format(class_name))
                the_module = importlib.import_module(module_path)
                logger.debug('the_module: {}'.format(the_module))
                the_class = getattr(the_module, class_name)
                logger.debug('the_class: {}'.format(the_class))
                instance = the_class()
                logger.debug('instance: {}'.format(instance))
                auth = instance.authenticate_request(
                    request_element,
                    soap_version
                )
                logger.debug('auth: {}'.format(auth))
            except errors.OseoError as err:
                 # this error is handled by the calling process_request() method
                raise
            except Exception as err:
                # other errors are re-raised as InvalidSettings
                logger.error('exception class: {}'.format(err.__class__.__name__))
                logger.error('exception args: {}'.format(err.args))
                raise errors.InvalidSettingsError('Invalid authentication '
                                                  'class')
            if auth is not None:
                user_name, password = auth
                logger.info('User %s authenticated successfully' % 
                            user_name)
                try:
                    user = models.OseoUser.objects.get(
                        user__username=user_name)
                except ObjectDoesNotExist:
                    user = models.User.create_user(user_name)
            else:
                raise errors.OseoError(
                    'AuthorizationFailed',
                    'The client is not authorized to call the operation',
                    locator=operation
                )
        else:
            user_name = 'oseoserver_user'
            logger.warning('No authentication in use')
        return user_name

    def create_exception_report(self, code, text, soap_version, locator=None):
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

    def process_request(self, request_data):
        '''
        Entry point for the ordering service.

        This method receives the raw request data as a string and then parses
        it into a valid pyxb OSEO object. It will then send the request to the
        appropriate operation processing class.

        :arg request_data: The raw request data
        :type request_data: str
        :return: The response XML document, as a string, the HTTP status
                 code and a dictionary with HTTP headers to be set by the 
                 wsgi server
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
        try:
            schema_instance = self._parse_xml(data)
            operation = self._get_operation(schema_instance.__class__.__name__)
            user_name = self.authenticate_request(element, operation.NAME,
                                                  soap_version)
            response, status_code = operation(schema_instance, user_name)
            if soap_version is not None:
                result = self._wrap_soap(response, soap_version)
            else:
                result = response.toxml(encoding=self._encoding)
        except errors.OseoError as err:
            if err.code == 'AuthorizationFailed':
                status_code = 401
                # we should probably also adjust the response's headers to 
                # include a WWW-authenticate HTTP header as well
            else:
                status_code = 400
            result = self.create_exception_report(err.code, err.text,
                                                  soap_version,
                                                  locator=err.locator)
        except errors.NonSoapRequestError as err:
            status_code = 400
            result = err
        except errors.InvalidSettingsError as err:
            status_code = 500
            result = err
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

    def _get_operation(self, class_name):
        op = self._operation_classes[class_name]
        module_path, sep, class_name = op.rpartition('.')
        the_module = importlib.import_module(module_path)
        operation_class = getattr(the_module, class_name)
        operation = operation_class()
        return operation

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
        reason_msg = '%s exception was encountered' % soap_code.capitalize()
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
