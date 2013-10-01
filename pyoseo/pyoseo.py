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
import logging
import ConfigParser

import operations

class PyOSEO(object):
    '''
    The starting point for the PyOSEO server.
    '''

    def __init__(self):
        module_dir = os.path.dirname(os.path.realpath(__file__))
        settings_file = os.path.join(module_dir, 'settings.cfg')
        self._read_settings(settings_file)
        self.logger = logging.getLogger('.'.join((__name__,
                                        self.__class__.__name__)))

    def process_request(self, request_xml):
        '''
        Process an OSEO request.

        This method is the main entry point in the server.

        Inputs:

            request_xml - An XML string with the OSEO request to process.

        Returns:

        A string with the response body to send to the web server.
        '''

        self.logger.debug('About to parse the request')
        operation = operations.get_operation(request_xml)
        self.logger.info('Parsed the request')
        self.logger.info('About to process the request')
        response = operation.process()
        self.logger.info('Processed the request')
        return response

    def _read_settings(self, filename):
        config = ConfigParser.ConfigParser()
        with open(filename) as fh:
            config.readfp(fh)
        self.version = unicode(config.get('general', 'version', '1.0.0'))
        self.encoding = unicode(config.get('general', 'encoding', 'utf-8'))
