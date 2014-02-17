from flask import request, make_response

from pyoseo import app, errors
from pyoseo.oseoserver import OseoServer

@app.route('/oseo', methods=['POST',])
def oseo_endpoint():
    '''
    Endpoint for the ordering server.
    '''

    server = OseoServer()
    server_response, status_code, headers = server.parse_request(request.data)
    response = make_response(server_response, status_code)
    for k, v in headers.iteritems():
        response.headers[k] = v
    return response
