'''
Module docstring goes here.

Testing this class can be done from the cli, using the example wsgi server and curl:

    curl --header "Content-Type: application/xml" --data @samples/oseo/1.0/SampleMessages/GetCapabilities.xml "http://localhost:8051"
'''

import errors

class PyOSEO(object):
    '''
    The starting point for the PyOSEO server.
    '''

    HTTP_GET = 'GET'
    HTTP_POST = 'POST'

    def process_request(self, server_environ):

        # sample code
        # Sorting and stringifying the environment key, value pairs
        #response_body = ['%s: %s' % (key, value)
        #                for key, value in sorted(server_environ.items())]
        #response_body = '\n'.join(response_body)

        #status = '200 OK'
        #response_headers = [('Content-Type', 'text/plain'),
        #            ('Content-Length', str(len(response_body)))]
        # end of sample code

        c_type, c_parameters = self._parse_content_type(
            server_environ.get('CONTENT_TYPE', ''))
        method = server_environ['REQUEST_METHOD'].upper()
        if method == self.HTTP_GET:
            self._process_get_request(server_environ)
        elif method == self.HTTP_POST:
            response_body = self._process_post_request(server_environ)
        else:
            raise errors.IncorrectHTTPMethod
        #response_body = ''
        status = '200 OK'
        response_headers = [('Content-Type', 'text/plain'),
                    ('Content-Length', str(len(response_body)))]
        return status, response_headers, response_body

    def _process_get_request(self, server_environ):
        input_query = server_environ.get('QUERY_STRING', '')
        if input_query != '':
            raise NotImplementedError
        else:
            raise errors.NoQueryStringFoundError

    def _process_post_request(self, server_environ):
        input_query = server_environ.get('wsgi.input')
        if input_query is None:
            raise errors.NoQueryStringFoundError
        else:
            c_length = self._get_request_content_length(server_environ)
            # request_body must be a valid OSEO xml file
            request_body = server_environ['wsgi.input']
            response_body = input_query.read(c_length)
        return response_body

    def _parse_content_type(self, ctype):
        content_type, sep, parameters = ctype.partition(';')
        content_parameters = dict()
        for parameter in parameters.split(';'):
            key, sep, value = parameter.strip().partition('=')
            content_parameters[key] = value
        return content_type, content_parameters

    def _get_request_content_length(self, server_environ):
        try:
            content_length = int(server_environ.get('CONTENT_LENGTH', ''))
        except:
            content_length = 0
        return content_length
