from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from oseoserver import server

@csrf_exempt
def oseo_endpoint(request):
    if request.method == 'POST':
        s = server.OseoServer()
        resp, status_code, headers = s.process_request(request.body)
        response = HttpResponse(resp)
        for k,v in headers.iteritems():
            response[k] = v
    else:
        raise Http404
    return response
