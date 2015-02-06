import os
import datetime as dt

from django.conf import settings as django_settings
from django.shortcuts import render
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.core.servers.basehttp import FileWrapper
from django.core.exceptions import ObjectDoesNotExist

import server
import models


@csrf_exempt
def oseo_endpoint(request):
    """
    Django's endpoint to pyoseo.

    This view receives the HTTP request from the webserver's WSGI handler.
    It is responsible for validating that a POST request was received,
    instantiating :class:`oseoserver.server.OseoServer` and handing it
    the request. It then returns the response back to the web server.
    """

    if request.method == 'POST':
        s = server.OseoServer()
        resp, status_code, headers = s.process_request(request.body)
        response = HttpResponse(resp)
        for k,v in headers.iteritems():
            response[k] = v
    else:
        response = HttpResponseForbidden()
    return response
