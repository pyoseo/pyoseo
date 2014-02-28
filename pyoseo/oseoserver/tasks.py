'''
Celery tasks for pyoseo

Example code for retrieving a CSW record once we know its catalog id:

from lxml import etree
import requests
import pyxb.bundles.opengis.csw_2_0_2 as csw

req = csw.GetRecordsById(service='CSW', version='2.0.2')
req.elementSetName = 'brief'
req.Id.append('3b584f68-8e05-11e3-b102-0019995d2a58')
response = requests.post(
    'http://geoland2.meteo.pt/geonetwork/srv/eng/csw',
    data=req.toxml(),
    headers={'Content-Type': 'application/xml'}
)
nsmap = {
    'csw': 'http://www.opengis.net/cat/csw/2.0.2'
    'dc': 'http://purl.org/dc/elements/1.1/'
    'ows': 'http://www.opengis.net/ows'
}
resp = etree.fromstring(response.text.encode(response.encoding))
item_title = resp.xpath('csw:BriefRecord/dc:title/text()', namespaces=nsmap)
'''

import time

from django.core.exceptions import ObjectDoesNotExist
import pyxb.bundles.opengis.csw_2_0_2 as csw
from celery import shared_task
from lxml import etree
import requests

from oseoserver import models

@shared_task()
def process_order(order_id):
    '''
    Process a normal order.

    * get order details from the database
    * fetch the products from giosystem
    * apply any customization options
    * update the database whenever an order/item changes status
    * if needed, send notifications on order/item status changes
    * send the ordered items to the appropriate destination

    :arg order_id: The id of the order in the pyoseo database
    :type order_id: int
    '''

    catalog_url = 'http://geoland2.meteo.pt/geonetwork/srv/eng/csw'
    nsmap = {
        'csw': 'http://www.opengis.net/cat/csw/2.0.2',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'ows': 'http://www.opengis.net/ows',
    }
    sleep_time = 30
    print('About to process order with id: %s' % order_id)
    ids = []
    try:
        order = models.Order.objects.get(id=order_id)
        for batch in order.batch_set.all():
            for order_item in batch.orderitem_set.all():
                ids.append(order_item.identifier)
        req = csw.GetRecordById(
            service='CSW',
            version='2.0.2',
            ElementSetName = 'brief'
        )
        for id in ids:
            req.Id.append(id)
        response = requests.post(catalog_url, data=req.toxml(),
                                 headers={'Content-Type': 'application/xml'})
        resp = etree.fromstring(response.text.encode(response.encoding))
        item_titles = resp.xpath('csw:BriefRecord/dc:title/text()',
                                 namespaces=nsmap)
        print('order_items:')
        for item in item_titles:
            print(item)
        print('sleeping now for %i seconds...' % sleep_time)
        time.sleep(sleep_time)
        print('Done processing!')
    except ObjectDoesNotExist:
        print('could not find order')
