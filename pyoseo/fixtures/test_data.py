'''
Some test data for pyoseo's database

A example query that joins two tables:

    pyoseo.db.session.query(pyoseo.models.Order).join(
        pyoseo.models.User).filter(
            pyoseo.models.User.name!='ricardogsilva').all()
'''

from random import randint
import datetime as dt
import uuid

import pyoseo

def main():
    ric = pyoseo.models.User(admin=True, name='ricardogsilva',
                             e_mail='ricardo.silva@mail.pt',
                             full_name='Ricardo Garcia Silva',
                             password='1234')
    john = pyoseo.models.User(admin=False, name='johndoe',
                              e_mail='john.doe@mail.pt',
                              full_name='John Doey Doe',
                              password='5678')
    pyoseo.db.session.add_all([ric, john])
    for i in xrange(10):
        delta = dt.timedelta(hours=i)
        owner = ric if randint(0, 1) else john
        order = pyoseo.models.Order(user=owner, status='Submitted',
                                    created_on=dt.datetime.now()+delta,
                                    status_changed_on=dt.datetime.now()+delta,
                                    reference='Some random stuff about this '
                                    'order', order_type='product_order')
        batch = pyoseo.models.Batch(order=order, status=order.status)
        for i in xrange(10):
            oi = pyoseo.models.OrderItem(batch=batch,
                                         catalog_id=str(uuid.uuid1()),
                                         status=order.status)
            pyoseo.db.session.add(oi)
        pyoseo.db.session.add_all([order, batch])
    pyoseo.db.session.commit()

if __name__ == '__main__':
    main()
