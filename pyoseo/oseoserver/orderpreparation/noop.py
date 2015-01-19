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

class FakeOrderProcessor(object):

    def parse_option(self, name, value):
        """

        :param name:
        :param value:
        :return:
        """

        parsed_value = value.text
        print("name: {}".format(name))
        print("value: {}".format(value))
        print("parsed_value: {}".format(parsed_value))
        return parsed_value

    def process_item_online_access(self, identifier, order_id, user_name,
                                   http_root):
        """

        :param identifier:
        :param order_id:
        :param user_name:
        :param http_root:
        :return:
        """

        return None
