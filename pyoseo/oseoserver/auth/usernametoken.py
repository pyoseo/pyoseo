# Copyright 2015 Ricardo Garcia Silva
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

"""
WSSE UsernameToken profile v1.0 authentication class for PyOSEO
"""


class UsernameTokenAuthentication(object):

    SOAP_NAMESPACES = {
        'soap': 'http://www.w3.org/2003/05/soap-envelope',
        'soap1.1': 'http://schemas.xmlsoap.org/soap/envelope/',
        'wsse': 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-'
                'wssecurity-secext-1.0.xsd',
    }

    def get_details(self, request_element, soap_version):
        """

        :arg request_element:
        :type request_element: lxml.element
        :arg soap_version:
        :type soap_version: string
        :return:
        :rtype: (string, string, dict)
        """

        soap_ns_map = {
            '1.1': 'soap1.1',
            '1.2': 'soap',
            }
        soap_ns_key = soap_ns_map[soap_version]

        token_path = ('/{0}:Envelope/{0}:Header/wsse:Security/'
                      'wsse:UsernameToken'.format(soap_ns_key))
        user_name_path = '/'.join((token_path, 'wsse:Username/text()'))
        user = request_element.xpath(user_name_path,
                                     namespaces=self.SOAP_NAMESPACES)[0]
        password_path = '/'.join((token_path, 'wsse:Password'))
        password_element = request_element.xpath(
            password_path,
            namespaces=self.SOAP_NAMESPACES
        )[0]
        password = password_element.text
        password_attributes = password_element.attrib
        return user, password, password_attributes
