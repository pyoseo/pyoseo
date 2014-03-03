import datetime as dt

from django.shortcuts import render
from django.http import HttpResponse, Http404

import giosystemcore.settings
import giosystemcore.files

def get_product(request, product, timeslot, tile='GLOBE'):
    timeslot = dt.datetime.strptime(timeslot, '%Y%m%d%H%M')
    response = HttpResponse('view get_product\ntile: %s' % tile)
    return response

def get_quicklook(request, product, year, month, day, hour, minute):
    pass

def get_wms(request, product):
    pass

