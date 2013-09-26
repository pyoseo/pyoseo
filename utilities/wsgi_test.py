'''
A testing wsgi server, following the tutorial available at:

    http://webpython.codepoint.net/wsgi_environment_dictionary
'''

from wsgiref.simple_server import make_server
import sys
sys.path.append('/home/ricardo/dev/pyoseo') # find a clean way to import pyoseo

from pyoseo import wsgi

web_server = make_server(
    'localhost', # hostname
    8051, # port name to listen to
    wsgi.application # the wsgi application
)

web_server.handle_request()
