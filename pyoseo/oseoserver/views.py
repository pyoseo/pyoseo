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


def show_item_2(request, oseo_file_path):
    pass

# TODO: Account for files which are not ACTIVE anymore
def show_item(request, user_name, order_id, item_id, item_file_name):
    """
    Return the already available order item

    The order item download count will be incremented and its status
    set to DOWNLOADED.
    """

    order_id = int(order_id)
    try:
        oseo_file = models.OseoFile.objects.get(order_item=item_id,
                                                name=item_file_name)
        order_item = oseo_file.order_item
    except ObjectDoesNotExist:
        raise Http404
    orders_root_dir = getattr(
        django_settings,
        'OSEOSERVER_ONLINE_DATA_ACCESS_HTTP_PROTOCOL_ROOT_DIR',
        None
    )
    if orders_root_dir is None:
        raise Exception
    item_path = os.path.join(orders_root_dir, user_name,
                             'order_{:02d}'.format(order_id),
                             item_file_name)
    print('item_path: %s' % item_path)
    if os.path.isfile(item_path):
        if item_file_name.endswith('tar.bz2'):
            ct = 'application/x-tar'
        elif item_file_name.endswith('.bz2'):
            ct = 'application/x-bzip2'
        response = HttpResponse(FileWrapper(open(item_path)),
                                content_type=ct)
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(
            item_file_name)
        oseo_file.downloads += 1
        oseo_file.save()
        if all([f.downloads > 0 for f in order_item.files.all()]):
            order_item.status = models.CustomizableItem.DOWNLOADED
            order_item.save()
    else:
        raise Http404
    return response
