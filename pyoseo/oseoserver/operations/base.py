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

"""
Base classes for the OSEO operations
"""

from django.core.exceptions import ObjectDoesNotExist
import pyxb
import pyxb.bundles.opengis.oseo_1_0 as oseo

from oseoserver import models

class OseoOperation(object):
    """
    This is the base class for OSEO operations.

    It should not be instantiated directly
    """

    def _user_is_authorized(self, user, order):
        """
        Test if a user is allowed to check on the status of an order
        """

        result = False
        if order.user == user:
            result = True
        return result

    def _c(self, value):
        """
        Convert between a None and an empty string.

        This function translates pyxb's empty elements, which are stored as
        None into django's empty values, which are stored as an empty string.
        """

        return '' if value is None else str(value)

    def _n(self, value):
        """
        Convert between an empty string and a None

        This function is translates django's empty elements, which are stored
        as empty strings into pyxb empty elements, which are stored as None.
        """

        return None if value == '' else value
