# Copyright 2015 Ricardo Garcia Silva
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
A default no authentication option for PyOSEO
"""

class NoAuthentication(object):

    def authenticate_request(self, user_name, password, **kwargs):
        """
        Authenticate the user

        :arg request_element: The full request object
        :type request_element: lxml.etree.Element
        :arg soap_version: The SOAP version in use
        :type soap_version: str or None
        :return: a boolean with the authentication result
        """

        return True

    def is_user(self, username, password, **kwargs):
        return True
