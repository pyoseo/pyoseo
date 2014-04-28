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
Authentication and authorization classes for pyoseo.

This functionality is implemented as a separate module in order to allow
different authentication methods to be used by the oseoserver.server.OseoServer
class.

The only requirement is that the authentication class have an 
authenticate_request() method, which is called by the server to authenticate 
and authorize a request.
'''

import oseoserver.errors

class VitoAuthentication(object):

    _VITO_ATTRIBUTE = 'type'
    _VITO_TOKEN = 'BBBB#VITO'
    _ns = {
        'soap': 'http://www.w3.org/2003/05/soap-envelope',
        'soap1.1': 'http://schemas.xmlsoap.org/soap/envelope/',
        'wsse': 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-' \
                'wssecurity-secext-1.0.xsd',
    }

    def authenticate_request(self, request_element, soap_version):
        '''
        :arg request_element: The full request object
        :type request_element: lxml.etree.Element
        :arg soap_version: The SOAP version in use. The OSEO specification
                           text states that SOAP 1.2 should be used. However,
                           the WSDL distributed with the specification uses
                           SOAP 1.1. This method supports both versions.
        :type soap_version: str
        :return: A two-value tuple indicating if the authentication has been
                 successfull and the username of the authenticated end user.
        :rtype: (bool, str)
        '''

        if soap_version is None:
            raise errors.NonSoapRequestError('%s requires requests to use '
                                             'the SOAP protocol' %
                                             self.__class__.__name__)
        soap_ns_map = {
            '1.1': 'soap1.1',
            '1.2': 'soap',
        }
        print('soap_version: {}'.format(soap_version))
        soap_ns_key = soap_ns_map[soap_version]
        print('soap_ns_key: {}'.format(soap_ns_key))
        auth_data = self._get_auth_data(request_element, soap_ns_key)
        print('auth_data[vito_token]: %s' % auth_data['vito_token'])
        if auth_data['vito_token'] == self._VITO_TOKEN:
            result = (True, auth_data['user_name'])
        else:
            result = (False, 'Unauthorized user')
            #operation = self._get_oseo_operation(request_element, soap_ns_key)
            #raise oseoserver.errors.OseoError(
            #    'AuthorizationFailed',
            #    'The client is not authorized to call the operation',
            #    locator=operation
            #)
        return result

    def _get_auth_data(self, request_element, soap_namespace_key):
        token_path = '/%s:Envelope/%s:Header/wsse:Security/' \
                     'wsse:UsernameToken' % (soap_namespace_key,
                     soap_namespace_key)
        user_name_path = '/'.join((token_path, 'wsse:Username/text()'))
        password_path = '/'.join((token_path, 'wsse:Password'))
        password_type_path = '/'.join((password_path,
                                      '@%s' % self._VITO_ATTRIBUTE))
        password_text_path = '/'.join((password_path, 'text()'))
        result = {
            'user_name': request_element.xpath(user_name_path,
                                              namespaces=self._ns)[0],
            'vito_token': request_element.xpath(password_type_path,
                                                namespaces=self._ns)[0],
            'password': request_element.xpath(password_text_path,
                                              namespaces=self._ns)[0],
        }
        return result

    def _get_oseo_operation(self, request_element, soap_namespace_key):
        request_body = request_element.xpath(
            '/%s:Envelope/%s:Body/*[1]' % (soap_namespace_key,
                                           soap_namespace_key),
            namespaces=self._ns
        )[0]
        operation = request_body.tag.rpartition('}')[-1]
        return operation
