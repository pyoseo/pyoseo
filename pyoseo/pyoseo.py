'''
Testing this class can be done from the cli, using the example wsgi server and curl:

    curl --header "Content-Type: application/xml" --data @samples/oseo/1.0/SampleMessages/GetCapabilities.xml "http://localhost:8051"
'''

import errors

class PyOSEO(object):
    '''
    The starting point for the PyOSEO server.
    '''


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
        return request_xml # work in progress...

    def _parse_oseo_request(self, request_xml):
        '''
        Parse the request body as a valid OSEO request.
        '''

        # TODO:
        # - finish this method
        request = None
        validates = True
        if not validates:
            raise errors.InvalidRequestError
        return request
