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
Custom exception classes for oseoserver
"""

class PyOseoError(Exception):
    pass

class ServerError(PyOseoError):
    """
    Used for errors which are related to server-side operations
    """

    pass


class UnAuthorizedOrder(PyOseoError):
    pass


class NonSoapRequestError(PyOseoError):
    pass


class InvalidOrderError(PyOseoError):
    pass


class InvalidOptionError(PyOseoError):

    def __init__(self, option, order_config):
        self.option = option
        self.order_config = order_config

    def __str__(self):
        order_type = self.order_config.__class__.__name__.lower()
        collection = self.order_config.collection.name
        return "{} of collection {} does not support option {}".format(
            order_type, collection, self.option)


class InvalidGlobalOptionError(InvalidOptionError):

    pass


class InvalidOptionValueError(PyOseoError):

    def __init__(self, option, value, order_config):
        self.option = option
        self.value = value
        self.order_config = order_config

    def __str__(self):
        return "Value {} is not supported for option {}".format(self.value,
                                                                self.option)

class InvalidGlobalOptionValueError(InvalidOptionValueError):

    pass


class InvalidDeliveryOptionError(PyOseoError):
    pass


class InvalidGlobalDeliveryOptionError(PyOseoError):
    pass


class InvalidOrderDeliveryMethodError(PyOseoError):
    pass


class InvalidCollectionError(PyOseoError):
    pass


class OnlineDataAccessInvalidProtocol(PyOseoError):
    pass


class OnlineDataDeliveryInvalidProtocol(PyOseoError):
    pass


class OperationNotImplementedError(PyOseoError):
    pass


class SubmitWithQuotationError(PyOseoError):
    pass


class OseoError(PyOseoError):

    def __init__(self, code, text, locator=None):
        self.code = code
        self.text = text
        self.locator = locator


class InvalidSettingsError(PyOseoError):
    pass


class AuthenticationError(PyOseoError):
    pass

