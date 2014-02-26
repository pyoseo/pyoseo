from jinja2 import Markup
from flask import url_for
from flask.ext.admin import Admin, BaseView, expose
from flask.ext.admin.model.form import InlineFormAdmin
from flask.ext.admin.contrib.sqla import ModelView

from pyoseo import app, db, models

class OptionChoiceInline(InlineFormAdmin):
    pass

class SelectedOptionInline(InlineFormAdmin):
    pass

class OptionVieW(ModelView):
    form_excluded_columns = ('option_type', 'selected_option',)
    inline_models = (
        OptionChoiceInline(models.OptionChoice),
    )

class CustomizableItemView(ModelView):
    column_display_pk = True
    inline_models = (
        SelectedOptionInline(models.SelectedOption),
    )

class OrderView(ModelView):
    column_exclude_list = (
        'additional_status_info', 'mission_specific_status_info',
        'packaging', 'priority', 'remark', 'item_type', 'created_on',
        'status_changed_on', 'completed_on',
    )
    #form_excluded_columns = ('invoice_address', 'delivery_information',)
    #column_formatters = dict(
    #    status_changed_on=lambda v, c, m, n:m.status_changed_on.strftime('%Y-%m-%d %H:%M:%S')
    #)
    column_display_pk = True

class DeliveryInformationView(ModelView):
    column_display_pk = True

class OnlineAddressView(ModelView):
    column_display_pk = True

#class ModerateSubscriptionView(BaseView):
#
#    @expose('/')
#    def index(self):
#        return self.render('index.html')
#
#class ModerateMassiveOrderView(BaseView):
#
#    @expose('/')
#    def index(self):
#        return self.render('index.html')

admin = Admin(app, name='pyoseo')

admin.add_view(OptionVieW(models.Option, db.session, category='Other models'))
admin.add_view(CustomizableItemView(models.CustomizableItem, db.session,
               category='Other models'))
admin.add_view(DeliveryInformationView(models.DeliveryInformation, db.session,
               category='Other models'))
admin.add_view(OnlineAddressView(models.OnlineAddress, db.session,
               category='Other models'))
admin.add_view(OrderView(models.Order, db.session))

# -------------------------------------------
#admin.add_view(UserView(models.User, db.session))
#admin.add_view(ModerateSubscriptionView(name='Moderate subscription requests',
#               category='Subscriptions'))
#admin.add_view(SubscriptionView(models.Subscription, db.session,
#               category='Subscriptions'))
#admin.add_view(ModerateMassiveOrderView(name='Moderate massive order requests',
#               category='Massive orders'))
#admin.add_view(MassiveOrderView(models.MassiveOrder, db.session,
#               category='Massive orders'))
#admin.add_view(NormalOrderView(models.NormalOrder, db.session,
#               name='Normal orders', category='Orders'))
#admin.add_view(SubscriptionOrderView(models.SubscriptionOrder, db.session,
#               name='Subscription orders', category='Orders'))
#admin.add_view(MassiveOrderOrderView(models.MassiveOrderOrder, db.session,
#               name='Massive order orders', category='Orders'))
#admin.add_view(OrderView(models.Order, db.session, name='All orders',
#               category='Orders'))
#admin.add_view(OrderItemView(models.OrderItem, db.session))
