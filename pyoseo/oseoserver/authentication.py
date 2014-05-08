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

import logging

#import ldap

import oseoserver.errors

logger = logging.getLogger('.'.join(('pyoseo', __name__)))

class VitoAuthentication(object):

    _VITO_ATTRIBUTE = 'domain'
    _VITO_TOKEN = 'VITO'
    _VITO_PASSWORD = 'CCCC'
    _ns = {
        'soap': 'http://www.w3.org/2003/05/soap-envelope',
        'soap1.1': 'http://schemas.xmlsoap.org/soap/envelope/',
        'wsse': 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-' \
                'wssecurity-secext-1.0.xsd',
    }

    _LDAP_SERVER = 'eodldap.vgt.vito.be'
    _LDAP_PROTOCOL = 'ldaps'
    _LDAP_DN = 'cn=reader,ou=ldap_accounts,ou=gio,dc=eodata,dc=vito,dc=be'
    _LDAP_PASSWORD = 'WJfSB4Fb'
    _LDAP_TIMEOUT = 5.0 # seconds

    def authenticate_request(self, request_element, soap_version):
        '''
        :arg request_element: The full request object
        :type request_element: lxml.etree.Element
        :arg soap_version: The SOAP version in use. The OSEO specification
                           text states that SOAP 1.2 should be used. However,
                           the WSDL distributed with the specification uses
                           SOAP 1.1. This method supports both versions.
        :type soap_version: str
        :return: The user_name and password of the successfully authenticated
                 user
        :rtype: (str, str)
        '''

        if soap_version is None:
            raise errors.NonSoapRequestError('%s requires requests to use '
                                             'the SOAP protocol' %
                                             self.__class__.__name__)
        soap_ns_map = {
            '1.1': 'soap1.1',
            '1.2': 'soap',
        }
        soap_ns_key = soap_ns_map[soap_version]
        try:
            user, vito_token, vito_pass = self.get_identity_token(
                request_element,
                soap_ns_key
            )
            valid_request = self.validate_vito_identity(vito_token, vito_pass)
            if valid_request:
                user_name, password = self.get_user_data(user)
            else:
                raise Exception('Could not validate VITO identity')
        except Exception as err:
            logger.error(err)
            raise oseoserver.errors.OseoError(
                'AuthenticationFailed',
                'Invalid or missing identity information',
                locator='identity_token'
            )
        return user_name, password

    def get_identity_token(self, request_element, soap_namespace_key):
        token_path = '/%s:Envelope/%s:Header/wsse:Security/' \
                     'wsse:UsernameToken' % (soap_namespace_key,
                     soap_namespace_key)
        user_name_path = '/'.join((token_path, 'wsse:Username/text()'))
        password_path = '/'.join((token_path, 'wsse:Password'))
        password_type_path = '/'.join((password_path,
                                      '@%s' % self._VITO_ATTRIBUTE))
        password_text_path = '/'.join((password_path, 'text()'))
        user = request_element.xpath(user_name_path, namespaces=self._ns)[0]
        vito_token = request_element.xpath(password_type_path,
                                           namespaces=self._ns)[0]
        vito_pass = request_element.xpath(password_text_path,
                                          namespaces=self._ns)[0]
        return user, vito_token, vito_pass

    def validate_vito_identity(self, vito_token, vito_password):
        result = False
        if vito_token == self._VITO_TOKEN and \
                vito_password == self._VITO_PASSWORD:
            result = True
        return result

    def get_user_data(self, user_name):
        '''
        Access VITO's LDAP server and get user data

        :arg user_name: The username to authenticate
        :type user_name: str
        :return: two-value tuple with username and password
        :rtype: (str, str)
        '''

        return user_name, 'dummy_password' # for now
        #connection = ldap.initialize('://'.join((self._LDAP_PROTOCOL,
        #                             self._LDAP_SERVER)))
        #connection.set_option(ldap.OPT_TIMEOUT, self._LDAP_TIMEOUT)
        #connection.set_option(ldap.OPT_NETWORK_TIMEOUT, self._LDAP_TIMEOUT)
        #connection.bind_s(self._LDAP_DN, self._LDAP_PASSWORD,
        #                  ldap.AUTH_SIMPLE)
        ## rest of the authentication stuff

    # unused??
    #def _get_oseo_operation(self, request_element, soap_namespace_key):
    #    request_body = request_element.xpath(
    #        '/%s:Envelope/%s:Body/*[1]' % (soap_namespace_key,
    #                                       soap_namespace_key),
    #        namespaces=self._ns
    #    )[0]
    #    operation = request_body.tag.rpartition('}')[-1]
    #    return operation
