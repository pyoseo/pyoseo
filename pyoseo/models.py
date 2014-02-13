'''
Database models for pyoseo.
'''

from pyoseo import db

class User(db.Model):
    id = db.Column(db.Integer, db.Sequence('user_id_seq'), primary_key=True)
    name = db.Column(db.String(50), nullable=False, index=True, unique=True)
    e_mail = db.Column(db.String(50), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return self.name

class Subscription(db.Model):
    id = db.Column(db.Integer, db.Sequence('user_id_seq'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('subscription',
                           lazy='joined'))
    state = db.Column(db.Enum('PENDING', 'QUEUED', 'PROCESSING', 'PROCESSED'),
                      nullable=False)
    approved = db.Column(db.Boolean(), nullable=False)
    created_on = db.Column(db.DateTime(), nullable=False)
    delivery_method = db.Column(db.Enum('HTTP', 'FTP_PULL', 'FTP_PUSH'),
                                nullable=False)
    notification_type = db.Column(db.Enum('E_MAIL', 'OTHER'), nullable=False)

    def __repr__(self):
        return '<%r %r>' % (self.__class__.__name__, self.id)

class Order(db.Model):
    id = db.Column(db.Integer, db.Sequence('user_id_seq'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('order', lazy='joined'))
    state = db.Column(db.Enum('PENDING', 'QUEUED', 'PROCESSING', 'PROCESSED'),
                      nullable=False)
    created_on = db.Column(db.DateTime(), nullable=False)
    completed_on = db.Column(db.DateTime())
    order_type = db.Column(db.String(50), nullable=False)
    __mapper_args__ = {
        'polymorphic_on': order_type,
        'polymorphic_identity': 'order'
    }

    def __repr__(self):
        return '<%r %r>' % (self.__class__.__name__, self.id)

class MassiveOrder(db.Model):
    id = db.Column(db.Integer, db.Sequence('user_id_seq'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('massiveorder',
                           lazy='joined'))
    product_name = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return '<%r %r>' % (self.__class__.__name__, self.id)

class SubscriptionOrder(Order):
    __mapper_args__ = {'polymorphic_identity': 'susbcription_order'}
    id = db.Column(db.Integer, db.ForeignKey('order.id'), primary_key=True)

    def __repr__(self):
        return '<%r %r>' % (self.__class__.__name__, self.id)

class FastOrder(Order):
    __mapper_args__ = {'polymorphic_identity': 'fast_order'}
    id = db.Column(db.Integer, db.ForeignKey('order.id'), primary_key=True)

    def __repr__(self):
        return '<%r %r>' % (self.__class__.__name__, self.id)
