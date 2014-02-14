from flask.ext.admin import Admin, BaseView, expose
from flask.ext.admin.contrib.sqla import ModelView

from pyoseo import app, db, models

class MyView(BaseView):

    @expose('/')
    def index(self):
        return self.render('index.html')

class UserView(ModelView):
    column_display_pk = True

class OrderView(ModelView):
    can_create = False
    can_edit = False
    can_delete = False

class SubscriptionOrderView(ModelView):
    column_exclude_list = ('order_type',)
    form_excluded_columns = ('order_type',)

class FastOrderView(ModelView):
    column_exclude_list = ('order_type',)
    form_excluded_columns = ('order_type',)

class CustomOrderView(ModelView):
    column_exclude_list = ('order_type',)
    form_excluded_columns = ('order_type',)

admin = Admin(app, name='pyoseo')
admin.add_view(MyView(name='hello 1', endpoint='test1', category='Test'))
admin.add_view(MyView(name='hello 2', endpoint='test2', category='Test'))
admin.add_view(UserView(models.User, db.session, endpoint='test3',
               category='Test'))
#admin.add_view(ModelView(models.Subscription, db.session))
#admin.add_view(OrderView(models.Order, db.session, category='Orders'))
#admin.add_view(FastOrderView(models.FastOrder, db.session,
#               name='Fast orders', category='Orders'))
#admin.add_view(SubscriptionOrderView(models.SubscriptionOrder, db.session,
#               name='Subscription orders', category='Orders'))
#admin.add_view(CustomOrderView(models.CustomOrder, db.session,
#               name='Custom orders', category='Orders'))
