import os

from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.core.servers.basehttp import FileWrapper
from django.core.exceptions import ObjectDoesNotExist

from oseoserver import server
from oseoserver import models

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

def show_item(request, username, order_id, item_file_name):
    '''
    Return the already available order item

    The order item download count will be incremented and its status
    set to DOWNLOADED.
    '''

    try:
        order_item = models.OrderItem.get(file_name=item_file_name)
    except ObjectDoesNotExist:
        raise Http404
    orders_root_dir = '/var/www' # find a nice way to set this value
    item_path = os.path.join(orders_root_dir, username, order_id,
                             item_file_name)
    if os.path.isfile(item_path):
        if item_file_name.endswith('tar.bz2'):
            ct = 'application/x-tar'
        elif item_file_name.endswith('.bz2'):
            ct = 'application/x-bzip2'
        response = HttpResponse(FileWrapper(open(item_path)),
                                content_type=ct)
        response['Content-Disposition'] = 'attachment; filename="%s"' % \
            item_file_name
        order_item.downloads += 1
        order_item.status = models.CustomizableItem.DOWNLOADED
        order_item.save()
    else:
        raise Http404
    return response
