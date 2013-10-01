import re
import xml.sax

import pyxb.bundles.opengis.oseo as oseo

import errors

def get_operation(request_xml):
    '''
    A factory to create the correct operation from a pyxb object.
    '''

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
    return operation(request_xml)

class OSEOOperation(object):

    operation = None

    def __init__(self, operation_xml=None):
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
            result = request_object
        return result

    def process(self):
        raise NotImplementedError


class GetCapabilities(OSEOOperation):

    def process(self):
        # create a Capabilities instance and populate it with correct values,
        # which are taken from the server's settings
        return self.operation.toxml(encoding='utf-8')
