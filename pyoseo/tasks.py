'''
Celery tasks for pyoseo
'''

import time

import sqlalchemy.orm.exc

from pyoseo import app, celery_app, models

@celery_app.task
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

    sleep_time = 30
    print('About to process order with id: %s' % order_id)
    try:
        order_record = models.Order.query.filter_by(id=order_id).one()
        print('found order')
        print('sleeping now for %i seconds...' % sleep_time)
        time.sleep(sleep_time)
        print('Done processing!')
    except sqlalchemy.orm.exc.NoResultFound:
        print('could not find order')
