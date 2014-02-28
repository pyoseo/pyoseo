from django.shortcuts import render
from django.http import HttpResponse, Http404
#from oseoserver import server

def oseo_endpoint(request):
    if request.method == 'POST':
        pass
        #s = server.OseoServer()
        #resp, status_code, headers = s.process_request(request.body)
        #response = HttpResponse(resp)
        #for k,v in headers.iteritems():
        #    response[k] = v
    else:
        raise Http404
    return response
