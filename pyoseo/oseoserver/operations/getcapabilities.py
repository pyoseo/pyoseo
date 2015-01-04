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

from django.core.urlresolvers import reverse
from pyxb import BIND
import pyxb.bundles.opengis.oseo_1_0 as oseo
import pyxb.bundles.opengis.ows_2_0 as ows
import pyxb.bundles.opengis.swes_2_0 as swes

from oseoserver.operations.base import OseoOperation
import oseoserver.server as server

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
        # parse the GetCapabilities request
        # here we just provide a standard response
        caps = oseo.Capabilities(version=server.OseoServer.OSEO_VERSION)
        caps.ServiceIdentification = self._build_service_identification()
        caps.ServiceProvider = self._build_service_provider()
        caps.OperationsMetadata = self._build_operations_metadata()
        caps.Contents = self._build_contents()
        # caps.Notifications = swes.NotificationProducerMetadataPropertyType()
        return caps, status_code

    def _build_service_identification(self):
        return None  # not implemented yet

    def _build_service_provider(self):
        return None  # not implemented yet

    def _build_operations_metadata(self):
        op_meta = ows.OperationsMetadata()
        for op_name in server.OseoServer.OPERATION_CLASSES.keys():
            op = ows.Operation(name=op_name)
            op.DCP.append(BIND())
            op.DCP[0].HTTP = BIND()
            op.DCP[0].HTTP.Post.append(BIND())
            op.DCP[0].HTTP.Post[0].href = "http://{}{}".format(
                "localhost:8000",  # change this
                reverse("oseo_endpoint")
            )
            op_meta.Operation.append(op)
        return op_meta

    def _build_contents(self, user):
        contents = oseo.OrderingServiceContentsType(
            ProductOrders=BIND(supported=True),
            SubscriptionOrders=BIND(supported=True),
            ProgrammingOrders=BIND(supported=False),
            GetQuotationCapabilities=BIND(supported=False,
                                          synchronous=False,
                                          asynchronous=False,
                                          monitoring=False,
                                          off_line=False),
            SubmitCapabilities=BIND(
                asynchronous=False,
                maxNumberOfProducts=server.OseoServer.MAX_ORDER_ITEMS,
                globalDeliveryOptions=True,
                localDeliveryOptions=True,
                globalOrderOptions=True,
                localOrderOptions=True
            ),
            GetStatusCapabilities=BIND(supported=True,
                                       orderSearch=True,
                                       orderRetrieve=True,
                                       full=True),
            DescribeResultAccessCapabilities=BIND(supported=True),
            CancelCapabilities=BIND(supported=False,
                                    asynchronous=False),
        )
        for collection in user.oseo_group.collection_set.all():
            cc = oseo.CollectionCapability(
                collectionId=collection.collection_id
            )
            contents.SupportedCollection.append(cc)
        return contents

