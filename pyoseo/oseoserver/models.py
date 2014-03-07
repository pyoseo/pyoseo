import datetime as dt

from django.db import models
from django.db.models import signals
from django.core.exceptions import ObjectDoesNotExist

class User(models.Model):
    admin = models.BooleanField(default=False, help_text='Will this user '
                                'be able to moderate order requests?')
    name = models.CharField(max_length=50, help_text='user name')
    e_mail = models.EmailField(max_length=254, help_text='e-mail', blank=True)
    full_name = models.CharField(max_length=255, blank=True,
                                help_text='Full name of the user')
    password = models.CharField(max_length=50, help_text='password',
                                blank=True)

    def __unicode__(self):
        return self.name

class CustomizableItem(models.Model):
    SUBMITTED = 'Submitted'
    ACCEPTED = 'Accepted'
    IN_PRODUCTION = 'InProduction'
    SUSPENDED = 'Suspended'
    CANCELLED = 'Cancelled'
    COMPLETED = 'Completed'
    FAILED = 'Failed'
    TERMINATED = 'Terminated'
    DOWNLOADED = 'Downloaded'
    STATUS_CHOICES = (
        (SUBMITTED, SUBMITTED),
        (ACCEPTED, ACCEPTED),
        (IN_PRODUCTION, IN_PRODUCTION),
        (SUSPENDED, SUSPENDED),
        (CANCELLED, CANCELLED),
        (COMPLETED, COMPLETED),
        (FAILED, FAILED),
        (TERMINATED, TERMINATED),
        (DOWNLOADED, DOWNLOADED),
    )

    status = models.CharField(max_length=50, choices=STATUS_CHOICES,
                              default=SUBMITTED, help_text='initial status')
    additional_status_info = models.TextField(help_text='Additional '
                                              'information about the status',
                                              blank=True)
    mission_specific_status_info = models.TextField(help_text='Additional '
                                              'information about the status '
                                              'that is specific to the '
                                              'mission', blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    status_changed_on = models.DateTimeField(editable=False, blank=True, null=True)
    remark = models.TextField(help_text='Some specific remark about the item',
                              blank=True)

    def __unicode__(self):
        try:
            instance = Order.objects.get(id=self.id)
        except ObjectDoesNotExist:
            instance = OrderItem.objects.get(id=self.id)
        return instance.__unicode__()

class OrderType(models.Model):

    PRODUCT_ORDER = 'PRODUCT_ORDER'
    SUBSCRIPTION_ORDER = 'SUBSCRIPTION_ORDER'
    MASSIVE_ORDER = 'MASSIVE_ORDER'
    ORDER_TYPE_CHOICES = (
        (PRODUCT_ORDER, PRODUCT_ORDER),
        (MASSIVE_ORDER, MASSIVE_ORDER),
        (SUBSCRIPTION_ORDER, SUBSCRIPTION_ORDER),
    )

    name = models.CharField(max_length=30, default=PRODUCT_ORDER,
                            choices=ORDER_TYPE_CHOICES, unique=True)

    def __unicode__(self):
        return self.name

class Order(CustomizableItem):
    BZIP2 = 'bzip2'
    PACKAGING_CHOICES = (
        (BZIP2, BZIP2),
    )
    STANDARD = 'STANDARD'
    FAST_TRACK = 'FAST_TRACK'
    PRIORITY_CHOICES = ((STANDARD, STANDARD), (FAST_TRACK, FAST_TRACK))
    user = models.ForeignKey('User', related_name='orders')
    order_type = models.ForeignKey('OrderType', related_name='orders')
    completed_on = models.DateTimeField(null=True, blank=True)
    reference = models.CharField(max_length=30, help_text='Some specific '
                                 'reference about this order', blank=True)
    packaging = models.CharField(max_length=30, choices=PACKAGING_CHOICES,
                                 blank=True)
    priority = models.CharField(max_length=30, choices=PRIORITY_CHOICES,
                                blank=True)
    approved = models.BooleanField(default=False, help_text='Is this order '
                                   'eligible for being processed?')

    def __unicode__(self):
        return '%s(%i)' % (self.order_type.name, self.id)

class Batch(models.Model):
    order = models.ForeignKey('Order')

    def status(self):
        order = {
            CustomizableItem.SUBMITTED: 0,
            CustomizableItem.ACCEPTED: 1,
            CustomizableItem.IN_PRODUCTION: 2,
            CustomizableItem.SUSPENDED: 3,
            CustomizableItem.CANCELLED: 4,
            CustomizableItem.COMPLETED: 5,
            CustomizableItem.FAILED: 6,
            CustomizableItem.TERMINATED: 7,
            CustomizableItem.DOWNLOADED: 8,
        }
        item_statuses = set([oi.status for oi in self.order_items.all()])
        status = list(item_statuses)[0]
        for st in item_statuses:
            if order[st] < order[status]:
                status = st
        return status

    class Meta:
        verbose_name_plural = 'batches'

    def __unicode__(self):
        return str(self.id)


class OrderItem(CustomizableItem):
    batch = models.ForeignKey('Batch', related_name='order_items')
    item_id = models.CharField(max_length=30, help_text='Id for the item in '
                               'the order request')
    product_order_options_id = models.CharField(max_length=50, help_text='Id '
                                                'for the order options group',
                                                blank=True)
    identifier = models.CharField(max_length=255, help_text='identifier for '
                                  'this order item. It is the product Id in '
                                  'the catalog', blank=True)
    collection_id = models.CharField(max_length=255, help_text='identifier for '
                                  'the collection. It is the id of the '
                                  'collection in the catalog', blank=True)
    
    def __unicode__(self):
        return str(self.item_id)

class DeliveryOption(models.Model):
    EACH_READY = 'As each product is ready'
    ALL_READY = 'Once all products are ready'
    OTHER = 'other'
    SHIPPING_CHOICES = (
        (EACH_READY, EACH_READY),
        (ALL_READY, ALL_READY),
        (OTHER, OTHER),
    )
    customizable_item = models.OneToOneField('CustomizableItem',
                                             related_name='delivery_options')
    online_data_access_protocol = models.CharField(max_length=50, blank=True)
    online_data_delivery_protocol = models.CharField(max_length=50, blank=True)
    media_delivery_package_medium = models.CharField(max_length=50, blank=True)
    media_delivery_shipping_instructions = models.CharField(
        max_length=50,
        blank=True,
        choices=SHIPPING_CHOICES
    )
    number_of_copies = models.PositiveSmallIntegerField(null=True, blank=True)
    annotation = models.TextField(blank=True)
    special_instructions = models.TextField(blank=True)

class DeliveryAddress(models.Model):
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    company_ref = models.CharField(max_length=50, blank=True)
    street_address = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=50, blank=True)
    state = models.CharField(max_length=50, blank=True)
    postal_code = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=50, blank=True)
    post_box = models.CharField(max_length=50, blank=True)
    telephone = models.CharField(max_length=50, blank=True)
    fax = models.CharField(max_length=50, blank=True)

class DeliveryInformation(DeliveryAddress):
    order = models.OneToOneField('Order', related_name='delivery_information')

class OnlineAddress(models.Model):
    FTP = 'ftp'
    SFTP = 'sftp'
    FTPS = 'ftps'
    PROTOCOL_CHOICES = (
        (FTP, FTP),
        (SFTP, SFTP),
        (FTPS, FTPS),
    )
    delivery_information = models.ForeignKey('DeliveryInformation')
    protocol = models.CharField(max_length=20, default=FTP,
                                choices=PROTOCOL_CHOICES)
    server_address = models.CharField(max_length=255)
    user_name = models.CharField(max_length=50, blank=True)
    user_password = models.CharField(max_length=50, blank=True)
    path = models.CharField(max_length=1024, blank=True)

    class Meta:
        verbose_name_plural = 'online addresses'

class InvoiceAddress(DeliveryAddress):
    order = models.OneToOneField('Order', related_name='invoice_address')

    class Meta:
        verbose_name_plural = 'invoice addresses'


class Product(models.Model):
    short_name = models.CharField(max_length=50, unique=True)
    collection_id = models.CharField(max_length=255, unique=True)

    def __unicode__(self):
        return self.short_name

class OptionGroup(models.Model):
    name = models.CharField(max_length=40, help_text='Id for the group of '
                            'options')
    description = models.CharField(max_length=255, help_text='Description of '
                                   'the order option group', blank=True)

    def __unicode__(self):
        return self.name

class Option(models.Model):
    name = models.CharField(max_length=100)
    product = models.ForeignKey('Product', null=True, blank=True)
    order_types = models.ManyToManyField('OrderType')
    group = models.ForeignKey('OptionGroup', related_name='options')
    type = models.CharField(max_length=50, help_text='The datatype of '
                             'this option')

    def available_choices(self):
        return ', '.join([c.value for c in self.choices.all()])

    def __unicode__(self):
        if self.product is not None:
            result = '%s(%s)' % (self.name, self.product.short_name)
        else:
            result = self.name
        return result

class OptionChoice(models.Model):
    option = models.ForeignKey('Option', related_name='choices')
    value = models.CharField(max_length=255, help_text='Value for this option')

    def __unicode__(self):
        return self.value

class SelectedOption(models.Model):
    option = models.ForeignKey('Option')
    customizable_item = models.ForeignKey('CustomizableItem',
                                          related_name='selected_options')
    value = models.CharField(max_length=255, help_text='Value for this option')

    def __unicode__(self):
        return self.value

# signal handlers

def get_old_status_callback(sender, **kwargs):
    instance = kwargs['instance']
    instance.old_status = instance.status

def update_status_changed_on_callback(sender, **kwargs):
    instance = kwargs['instance']
    if instance.status_changed_on is None or \
            instance.status != instance.old_status:
        instance.status_changed_on = dt.datetime.utcnow()

signals.post_init.connect(
    get_old_status_callback,
    Order,
    weak=False,
    dispatch_uid='id_for_get_old_status_order'
)
signals.post_init.connect(
    get_old_status_callback,
    OrderItem,
    weak=False,
    dispatch_uid='id_for_get_old_status_order_item'
)
signals.pre_save.connect(
    update_status_changed_on_callback,
    Order,
    weak=False,
    dispatch_uid='id_for_update_status_changed_on_order'
)
signals.pre_save.connect(
    update_status_changed_on_callback,
    OrderItem,
    weak=False,
    dispatch_uid='id_for_update_status_changed_on_order_item'
)
