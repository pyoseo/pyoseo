import pyoseo
import errors

HTTP_GET = 'GET'
HTTP_POST = 'POST'

# TODO
# - deal with encodings by hooking up the _get_request_encoding()
# method and using the correct encoding when reading data and when
# parsing the xml text

def application(environ, start_response):
    method = environ['REQUEST_METHOD'].upper()
    c_type, c_parameters = _parse_content_type(environ)
    if method == HTTP_POST:
        try:
            request_xml = _read_post_data(environ)
            p = pyoseo.PyOSEO()
            response_body = p.process_request(request_xml)
            status = '200 OK'
            response_headers = _success_headers(response_body)
        except errors.NoRequestFoundError:
            status = '202 Accepted'
            response_body = 'No operation has been requested.'
            response_headers = _error_headers(response_body)
        except errors.InvalidRequestError:
            status = '400 Bad Request'
            response_body = 'Invalid request'
            response_headers = _error_headers(response_body)
    else:
        status = '405 Method Not Allowed'
        response_body = 'This server only allows HTTP POST methods.'
        response_headers = _error_headers(response_body)
    start_response(status, response_headers)
    return [response_body]


def _success_headers(response_body):
    response_headers = [
        ('Content-Type', 'application/xml'),
        ('Content-Length', str(len(response_body))),
    ]
    return response_headers

def _error_headers(response_body):
    response_headers = [
        ('Content-Type', 'text/plain'),
        ('Content-Length', str(len(response_body)))
    ]
    return response_headers

def _get_request_content_length(server_environ):
    try:
        content_length = int(server_environ.get('CONTENT_LENGTH', ''))
    except ValueError:
        content_length = 0
    return content_length

def _read_post_data(server_environ):
    content_length = _get_request_content_length(server_environ)
    request_body = ''
    if content_length == 0:
        raise errors.NoRequestFoundError
    else:
        request_body = server_environ['wsgi.input'].read(content_length)
    return request_body

def _get_request_encoding(server_environ):
    raise NotImplementedError

def _parse_content_type(server_environ):
    ctype = server_environ.get('CONTENT-TYPE', '')
    content_type, sep, parameters = ctype.partition(';')
    content_parameters = dict()
    for parameter in parameters.split(';'):
        key, sep, value = parameter.strip().partition('=')
        content_parameters[key] = value
    return content_type, content_parameters

