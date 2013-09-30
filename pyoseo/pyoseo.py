'''
Testing this class can be done from the cli, using the example wsgi server and curl:

    curl --header "Content-Type: application/xml" --data @samples/oseo/1.0/SampleMessages/GetCapabilities.xml "http://localhost:8051"

Or with the python requests module:

    import requests
    with open('samples/SampleMessages/GetCapabilities.xml') as fh:
        xml_request = fh.read()
    response = requests.post('localhost:8051', data=xml_request)
'''

import os
import re
import xml.sax
import ConfigParser

import pyxb
import pyxb.bundles.opengis.oseo as oseo

import errors

class PyOSEO(object):
    '''
    The starting point for the PyOSEO server.
    '''

    def __init__(self):
        settings_file = os.path.join(module_dir, 'settings.cfg')
        self.settings = self._read_settings(settings_file)

    def process_request(self, request_xml):
        '''
        Process an OSEO request.

        This method is the main entry point in the server.

        Inputs:

            request_xml - An XML string with the OSEO request to process.

        Returns:

        A string with the response body to send to the web server.
        '''

        request = self._parse_oseo_request(request_xml)
        request_name = self._get_request_name(request_xml)
        processing_methods = {
            'GetCapabilities': self.process_get_capabilities,
            'GetOptions': self.process_get_options,
            'GetQuotation': self.process_get_quotation,
            'GetQuotationResponse': self.process_get_quotation_response,
            'Submit': self.process_submit,
            'SubmitResponse': self.process_submit_response,
            'GetStatus': self.process_get_status,
            'DescribeResultAccess': self.process_describe_result_access,
            'Cancel': self.process_cancel,
            'CancelResponse': self.process_cancel_response,
        }
        process_to_execute = processing_methods[request_name]
        response = process_to_execute(request)
        return response

    def process_get_capabilities(self, request):
        '''
        Inputs:

            request - a valid pyxb GetCapabilities object.
        '''

        response = ''
        capabilities = oseo.Capabilities()
        capabilities.version = self.version
        if capabilities.validateBinding():
            response = capabilities.toxml(encoding=self.encoding)
        return response

    def process_get_options(self, request):
        raise NotImplementedError

    def process_get_quotation(self, request):
        raise NotImplementedError

    def process_get_quotation_response(self, request):
        raise NotImplementedError

    def process_submit(self, request):
        raise NotImplementedError

    def process_submit_response(self, request):
        raise NotImplementedError

    def process_get_status(self, request):
        raise NotImplementedError

    def process_describe_result_access(self, request):
        raise NotImplementedError

    def process_cancel(self, request):
        raise NotImplementedError

    def process_cancel_response(self, request):
        raise NotImplementedError

    def _get_request_name(self, text_data):
        '''
        Extract the request name from the raw data.
        '''

        name = ''
        request_pattern = re.compile(r'^<(\w+) ')
        re_obj = request_pattern.search(text_data)
        if re_obj is not None:
            name = re_obj.group(1)
        return name

    def _parse_oseo_request(self, request_xml):
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

    def _read_settings(self, filename):
        config = ConfigParser.ConfigParser()
        with open(filename) as fh:
            config.readfp(fh)
        self.version = unicode(config.get('General', 'version', '1.0.0'))
        self.encoding = unicode(config.get('General', 'encoding', 'utf-8'))
