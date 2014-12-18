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

class NonSoapRequestError(Exception):
    pass


class InvalidOrderError(Exception):
    pass


class InvalidOrderDeliveryMethodError(Exception):
    pass


class OnlineDataAccessInvalidProtocol(Exception):
    pass


class OnlineDataDeliveryInvalidProtocol(Exception):
    pass


class OperationNotImplementedError(Exception):
    pass


class SubmitWithQuotationError(Exception):
    pass


class OseoError(Exception):

    def __init__(self, code, text, locator=None):
        self.code = code
        self.text = text
        self.locator = locator


class InvalidSettingsError(Exception):
    pass


class AuthenticationError(Exception):
    pass

