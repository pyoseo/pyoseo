# Copyright 2014 Ricardo Garcia Silva
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
Implements the OSEO GetCapabilities operation
"""

import logging

import pyxb.bundles.opengis.oseo_1_0 as oseo

from oseoserver.operations.base import OseoOperation

logger = logging.getLogger('.'.join(('pyoseo', __name__)))


class GetCapabilities(OseoOperation):

    def __call__(self, request, user, **kwargs):
        """
        Implements the OSEO GetCapabilities operation.

        :param request:
        :param user:
        :param user_password:
        :param kwargs:
        :return:
        """

        status_code = 200
        response = oseo.Capabilities()
        return response, status_code
