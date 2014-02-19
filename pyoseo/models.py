'''
Database models for pyoseo.
'''

from pyoseo import db

# as defined in the OSEO specification
PROCESSING_STATES = ['Submitted', 'Accepted', 'InProduction', 'Suspended',
                     'Cancelled', 'Completed', 'Failed', 'Terminated',
                     'Downloaded',]
# as defined in the OSEO specification
PRIORITIES = ['STANDARD', 'FAST_TRACK']

class User(db.Model):
    id = db.Column(db.Integer, db.Sequence('user_id_seq'), primary_key=True)
    admin = db.Column(db.Boolean(), nullable=False)
    name = db.Column(db.String(50), nullable=False, index=True, unique=True)
    e_mail = db.Column(db.String(50), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return self.name

class Subscription(db.Model):
    id = db.Column(db.Integer, db.Sequence('subscription_id_seq'),
                  primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('subscription',
                           lazy='joined'))
    approved = db.Column(db.Boolean(), default=False, nullable=False)
    active = db.Column(db.Boolean(), default=False, nullable=False)
    created_on = db.Column(db.DateTime(), nullable=False)

    def __repr__(self):
        return '%r' % self.id

class MassiveOrder(db.Model):
    id = db.Column(db.Integer, db.Sequence('massive_order_id_seq'),
                  primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('MassiveOrder',
                           lazy='joined'))
    approved = db.Column(db.Boolean(), default=False, nullable=False)
    status = db.Column(db.Enum(*PROCESSING_STATES),
                       nullable=False)
    created_on = db.Column(db.DateTime(), nullable=False)
    completion_date = db.Column(db.DateTime())

    def __repr__(self):
        return '%r' % self.id

class Order(db.Model):
    id = db.Column(db.Integer, db.Sequence('order_id_seq'), primary_key=True)
    #delivery_information_id
    #invoice_address_id
    #delivery_options_id
    status = db.Column(db.Enum(*PROCESSING_STATES), nullable=False)
    additional_status_info = db.Column(db.Text(4000), doc='StatusType/'
                                       'additionalStatusInfo, as defined in '
                                       'the OSEO spec, section 7.3.13')
    mission_specific_status_info = db.Column(
        db.Text(4000),
        doc='StatusType/missionSpecificStatusInfo, as defined in '
            'the OSEO spec, section 7.3.13'
    )
    created_on = db.Column(db.DateTime(), nullable=False)
    completed_on = db.Column(db.DateTime())
    status_changed_on = db.Column(db.DateTime(), nullable=False)
    reference = db.Column(db.String(30), doc='orderReference, as defined in '
                          'the OSEO spec, section 7.3.7')
    remark = db.Column(db.Text(4000), doc='orderRemark, as defined in '
                          'the OSEO spec, section 7.3.7')
    packaging = db.Column(db.Enum('bzip2'), doc='packaging, as defined in '
                          'the OSEO spec, section 7.3.7')
    priority = db.Column(db.Enum(*PRIORITIES), doc='priority, '
                         'as defined in the OSEO spec, section 7.3.7')
    order_type = db.Column(db.String(50), nullable=False)
    __mapper_args__ = {
        'polymorphic_on': order_type,
        'polymorphic_identity': 'order'
    }

    def __repr__(self):
        return '%r' % self.id

class NormalOrder(Order):
    __mapper_args__ = {'polymorphic_identity': 'normal_order'}
    id = db.Column(db.Integer, db.ForeignKey('order.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('normal_order',
                           lazy='joined'))

class SubscriptionOrder(Order):
    __mapper_args__ = {'polymorphic_identity': 'subscription_order'}
    id = db.Column(db.Integer, db.ForeignKey('order.id'), primary_key=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscription.id'))
    subscription = db.relationship('Subscription', backref=db.backref(
                                   'subscription_order', lazy='joined'))

class MassiveOrderOrder(Order):
    __mapper_args__ = {'polymorphic_identity': 'massive_order_order'}
    id = db.Column(db.Integer, db.ForeignKey('order.id'), primary_key=True)
    massive_order_id = db.Column(db.Integer, db.ForeignKey('massive_order.id'))
    massive_order = db.relationship('MassiveOrder', backref=db.backref(
                                    'massive_order_order', lazy='joined'))

class OrderItem(db.Model):
    id = db.Column(db.Integer, db.Sequence('order_item_id_seq'),
                   primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    order = db.relationship('Order', backref=db.backref('order_items',
                            lazy='joined'))
    catalog_id = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return self.catalog_id

class SubscriptionOption(db.Model):
    __mapper_args__ = {
        'polymorphic_identity': 'subscription_option',
    }
    id = db.Column(db.Integer, db.Sequence('subscription_option_id_seq'),
                   primary_key=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscription.id'))
    subscription = db.relationship('Subscription', backref=db.backref(
                                   'subscription_option', lazy='joined'))
    name = db.Column(db.String(50), nullable=False)
    value = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return '%r: %r' % (self.name, self.value)

class MassiveOrderOption(db.Model):
    __mapper_args__ = {
        'polymorphic_identity': 'massive_order_option',
    }
    id = db.Column(db.Integer, db.Sequence('massive_order_option_id_seq'),
                   primary_key=True)
    massive_order_id = db.Column(db.Integer,
                                 db.ForeignKey('massive_order.id'))
    massive_order = db.relationship('MassiveOrder', backref=db.backref(
                                   'massive_order_option', lazy='joined'))
    name = db.Column(db.String(50), nullable=False)
    value = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return '%r: %r' % (self.name, self.value)

class OrderOption(db.Model):
    __mapper_args__ = {
        'polymorphic_identity': 'order_option',
    }
    id = db.Column(db.Integer, db.Sequence('order_option_id_seq'),
                   primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    order = db.relationship('Order', backref=db.backref(
                            'order_option', lazy='joined'))
    name = db.Column(db.String(50), nullable=False)
    value = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return '%r: %r' % (self.name, self.value)

class OrderItemOption(db.Model):
    id = db.Column(db.Integer, db.Sequence('order_item_option_id_seq'),
                   primary_key=True)
    order_item_id = db.Column(db.Integer, db.ForeignKey('order_item.id'))
    order_item = db.relationship('OrderItem', backref=db.backref(
                                 'order_item_option', lazy='joined'))
    name = db.Column(db.String(50), nullable=False)
    value = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return '%r: %r' % (self.name, self.value)

class OrderItemInformation(db.Model):
    id = db.Column(db.Integer, db.Sequence('order_item_information_id_seq'),
                   primary_key=True)
    order_item_id = db.Column(db.Integer, db.ForeignKey('order_item.id'))
    order_item = db.relationship('OrderItem', backref=db.backref(
                                 'order_item_information', lazy='joined'))
    name = db.Column(db.String(50), nullable=False)
    value = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return '%r: %r' % (self.name, self.value)
