from flask import request, make_response

from pyoseo import app
from pyoseo.oseoserver import OseoServer

@app.route('/oseo', methods=['POST',])
def oseo_endpoint():
    '''
    Endpoint for the ordering server.
    '''

    server = OseoServer()
    resp, status_code, headers = server.process_request(request.data)
    response = make_response(resp, status_code)
    for k, v in headers.iteritems():
        response.headers[k] = v
    return response
