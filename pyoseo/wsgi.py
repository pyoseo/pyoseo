import pyoseo

def application(environ, start_response):
    p = pyoseo.PyOSEO()
    status, response_headers, response_body = p.process_request(environ)
    start_response(status, response_headers)
    return [response_body]
