import re
import logging
import xml.sax

import pyxb.bundles.opengis.oseo as oseo

import errors

module_logger = logging.getLogger(__name__)

def get_operation(request_xml, server=None):
    '''
    A factory to create the correct operation from a pyxb object.
    '''

    global module_logger
    request_name = ''
    request_pattern = re.compile(r'^<(\w+) ')
    re_obj = request_pattern.search(request_xml)
    if re_obj is not None:
        request_name = re_obj.group(1)
    operations = {
        'GetCapabilities': GetCapabilities,
        #'GetOptions': GetOptions,
        #'GetQuotation': GetQuotation,
        #'GetQuotationResponse': GetQuotationResponse,
        #'Submit': Submit,
        #'SubmitResponse': SubmitResponse,
        #'GetStatus': GetStatus,
        #'DescribeResultAccess': DescribeResultAccess,
        #'Cancel': Cancel,
        #'CancelResponse': CancelResponse,
    }
    operation = operations[request_name]
    module_logger.debug('operation: %s' % operation.__name__)
    return operation(request_xml, server)

class OSEOOperation(object):

    operation = None
    server = None

    def __init__(self, operation_xml=None, server=None):
        self.logger = logging.getLogger('.'.join((__name__,
                                        self.__class__.__name__)))
        self.server = server
        if operation_xml is not None:
            self.operation = self._parse_xml(operation_xml)

    def _parse_xml(self, request_xml):
        '''
        Parse the request body as a valid OSEO request.
        '''

        try:
            request_object = oseo.CreateFromDocument(request_xml)
        except pyxb.UnrecognizedDOMRootNodeError:
            raise errors.InvalidRequestError('Unrecognized OSEO request')
        except pyxb.AttributeChangeError:
            raise errors.InvalidRequestError('Unrecognized service name')
        except xml.sax.SAXParseException:
            raise errors.InvalidRequestError('Invalid syntax')
        except:
            # some other validation error
            raise
        result = None
        if request_object.validateBinding():
            self.logger.info('request was successfully parsed')
            result = request_object
        return result

    def validate(self):
        raise NotImplementedError

    def process(self):
        raise NotImplementedError


class GetCapabilities(OSEOOperation):

    def validate(self):
        valid_request = False
        # check various parameters of the request to make sure
        # they match server capabilities
        valid_version = self._validate_accept_versions()
        if valid_version:
            valid_request = True
        return valid_request

    def _validate_accept_versions(self):
        '''
        Validate the AcceptVersions parameter.

        This parameter is optional, so in case it is not present the
        request is still considered valid.
        '''

        validates = False
        if self.operation.AcceptVersions is not None:
            request_accept_versions = [v.value for v in \
                self.operation.AcceptVersions.orderedContent()]
            self.logger.debug('request_accept_versions: %s' % \
                              request_accept_versions)
            self.logger.debug('server version: %s' % self.server.version)
            if self.server.version in request_accept_versions:
                validates = True
        else:
            validates = True
        return validates

    def process(self):
        capabilities = oseo.Capabilities()
        capabilities.version = self.server.version
        return capabilities.toxml(encoding=self.server.encoding)
