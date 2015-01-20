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
A default order processing module for PyOSEO. It does nothing, but serves as an
example of the API that PyOSEO expects to find on a real implementation
"""

import logging

logger = logging.getLogger('.'.join(('pyoseo', __name__)))


class FakeOrderProcessor(object):

    def __init__(self, **kwargs):
        pass

    @staticmethod
    def parse_option(name, value):
        """

        :param name:
        :param value:
        :return:
        """

        parsed_value = value.text
        logger.debug("name: {}".format(name))
        logger.debug("value: {}".format(value))
        logger.debug("parsed_value: {}".format(parsed_value))
        return parsed_value

    @staticmethod
    def process_item_online_access(identifier, order_id, user_name,
                                   packaging, options, delivery_options):
        """
        Process an item that has been ordered.

        According to the selected options, a single item can in fact result
        in multiple output files. For example, a multiband dataset may be
        split into its sub bands.

        :param identifier:
        :type identifier:
        :param order_id:
        :type order_id:
        :param user_name:
        :type user_name:
        :param packaging:
        :type packaging: bool
        :param options:
        :type options: dict()
        :param delivery_options:
        :type delivery_options: dict()
        :return: A list with the name of the processed item(s) and a
            string with additional details
        :rtype: ([string], string)
        """

        logger.debug("fake processing of an order item")
        logger.debug("arguments: {}".format(locals()))
        #file_name = None
        #details = "The item failed because this is a fake processor"
        file_name = "bogus_file"
        details = "Pretending to be a file"
        return [file_name], details
