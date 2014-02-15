from jinja2 import Markup
from flask import url_for
from flask.ext.admin import Admin, BaseView, expose
from flask.ext.admin.model.form import InlineFormAdmin
from flask.ext.admin.contrib.sqla import ModelView

from pyoseo import app, db, models

class OrderItemInline(InlineFormAdmin):
    pass

class OrderOptionInline(InlineFormAdmin):
    pass

class OrderItemOptionInline(InlineFormAdmin):
    pass

class OrderItemInformationInline(InlineFormAdmin):
    pass

class ModerateSubscriptionView(BaseView):

    @expose('/')
    def index(self):
        return self.render('index.html')

class ModerateMassiveOrderView(BaseView):

    @expose('/')
    def index(self):
        return self.render('index.html')

class UserView(ModelView):
    column_display_pk = True

class OrderView(ModelView):
    column_descriptions = {
        'creation_date': 'Date and time of creation of the order.',
        'completion_date': 'Date and time of completion of the order.',
        'order_type': 'Type of order. It can be one of normal_order, ' \
                      'subscription_order or massive_order_order.',
        'state': 'Order\'s state. It can be one of PENDING, PROCESSING, ' \
                 'FINISHED',
    }
    column_display_pk = True
    can_create = False
    can_edit = False
    can_delete = False

    #def _order_type_formatter(view, context, model, name):
    #    endpoint_base = model.order_type.replace('_', '')
    #    url = url_for('%sview.edit_view' % endpoint_base, id=model.id)
    #    html = '<a href="%s">%s</a>' % (url, model.order_type)
    #    return Markup(html)

    #column_formatters = {
    #    'order_type': _order_type_formatter
    #}

class SubscriptionView(ModelView):
    column_display_pk = True

class MassiveOrderView(ModelView):
    column_display_pk = True

class SubscriptionOrderView(ModelView):
    column_display_pk = True
    column_exclude_list = ('order_type',)
    form_excluded_columns = ('order_type',)
    inline_models = (
        OrderOptionInline(models.OrderOption),
        OrderItemInline(models.OrderItem),
    )

class NormalOrderView(ModelView):
    column_display_pk = True
    column_exclude_list = ('order_type',)
    form_excluded_columns = ('order_type',)
    inline_models = (
        OrderOptionInline(models.OrderOption),
        OrderItemInline(models.OrderItem),
    )
    form_widget_args = {
        #'user': {'disabled': True,},
        #'state': {'disabled': True,},
        #'creation_date': {'disabled': True,},
        #'completion_date': {'disabled': True,},
        'order_option': {'disabled': True,},
        'order_item': {'disabled': True,},
    }

class MassiveOrderOrderView(ModelView):
    column_display_pk = True
    column_exclude_list = ('order_type',)
    form_excluded_columns = ('order_type',)
    inline_models = (
        OrderOptionInline(models.OrderOption),
        OrderItemInline(models.OrderItem),
    )

class OrderItemView(ModelView):
    column_list = ('catalog_id', 'order', 'order_item_information',
                   'order_item_option')
    column_display_all_relations = True
    inline_models = (
        OrderItemOptionInline(models.OrderItemOption),
        OrderItemInformationInline(models.OrderItemInformation),
    )

    def _order_formatter(view, context, model, name):
        if model.order is not None:
            endpoint_base = model.order.order_type.replace('_', '')
            url = url_for('%sview.edit_view' % endpoint_base,
                          id=model.order.id)
            html = '<a href="%s">%s</a>' % (url, model.order.id)
        else:
            html = ''
        return Markup(html)

    column_formatters = {
        'order': _order_formatter,
    }

class ItemCustomizationOptionView(ModelView):
    column_display_pk = True
    column_exclude_list = ('option_type',)
    form_excluded_columns = ('option_type',)


admin = Admin(app, name='pyoseo')
admin.add_view(UserView(models.User, db.session))
admin.add_view(ModerateSubscriptionView(name='Moderate subscription requests',
               category='Subscriptions'))
admin.add_view(SubscriptionView(models.Subscription, db.session,
               category='Subscriptions'))
admin.add_view(ModerateMassiveOrderView(name='Moderate massive order requests',
               category='Massive orders'))
admin.add_view(MassiveOrderView(models.MassiveOrder, db.session,
               category='Massive orders'))
admin.add_view(NormalOrderView(models.NormalOrder, db.session,
               name='Normal orders', category='Orders'))
admin.add_view(SubscriptionOrderView(models.SubscriptionOrder, db.session,
               name='Subscription orders', category='Orders'))
admin.add_view(MassiveOrderOrderView(models.MassiveOrderOrder, db.session,
               name='Massive order orders', category='Orders'))
admin.add_view(OrderView(models.Order, db.session, name='All orders',
               category='Orders'))
admin.add_view(OrderItemView(models.OrderItem, db.session))
