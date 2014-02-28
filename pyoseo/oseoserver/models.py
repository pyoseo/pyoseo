from django.db import models

class Product(models.Model):
    short_name = models.CharField(max_length=50, unique=True)

    def __unicode__(self):
        return self.name

class Option(models.Model):
    name = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=50, help_text='The datatype of '
                             'this option')

    def __unicode__(self):
        return self.name

class ProductOption(Option):
    product = models.ForeignKey('Product')

class OptionChoice(models.Model):
    option = models.ForeignKey('Option')
    value = models.CharField(max_length=255, help_text='Value for this option')

    def __unicode__(self):
        return self.value

class SelectedOption(models.Model):
    option = models.ForeignKey('Option')
    customizable_item = models.ForeignKey('CustomizableItem')
    value = models.CharField(max_length=255, help_text='Value for this option')

    def __unicode__(self):
        return self.value

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
    status_changed_on = models.DateTimeField()
    remark = models.TextField(help_text='Some specific remark about the item',
                              blank=True)

class Order(CustomizableItem):
    BZIP2 = 'bzip2'
    PACKAGING_CHOICES = (
        (BZIP2, BZIP2),
    )
    STANDARD = 'STANDARD'
    FAST_TRACK = 'FAST_TRACK'
    PRIORITY_CHOICES = ((STANDARD, STANDARD), (FAST_TRACK, FAST_TRACK))
    PRODUCT_ORDER = 'PRODUCT_ORDER'
    SUBSCRIPTION_ORDER = 'SUBSCRIPTION_ORDER'
    MASSIVE_ORDER = 'MASSIVE_ORDER'
    ORDER_TYPE_CHOICES = (
        (PRODUCT_ORDER, PRODUCT_ORDER),
        (MASSIVE_ORDER, MASSIVE_ORDER),
        (SUBSCRIPTION_ORDER, SUBSCRIPTION_ORDER),
    )
    user = models.ForeignKey('User', related_name='orders')
    completed_on = models.DateTimeField(null=True, blank=True)
    reference = models.CharField(max_length=30, help_text='Some specific '
                                 'reference about this order', blank=True)
    packaging = models.CharField(max_length=30, choices=PACKAGING_CHOICES,
                                 blank=True)
    priority = models.CharField(max_length=30, choices=PRIORITY_CHOICES,
                                 blank=True)
    approved = models.BooleanField(default=False, help_text='Is this order '
                                   'eligible for being processed?')
    order_type = models.CharField(max_length=30, default=PRODUCT_ORDER,
                                  choices=ORDER_TYPE_CHOICES)

    def __unicode__(self):
        return '%s(%i)' % (self.order_type, self.id)

class Batch(models.Model):
    order = models.ForeignKey('Order')
    status = models.CharField(max_length=50,
                              choices=CustomizableItem.STATUS_CHOICES,
                              default=CustomizableItem.SUBMITTED,
                              help_text='initial status')

    class Meta:
        verbose_name_plural = 'batches'


class OrderItem(CustomizableItem):
    batch = models.ForeignKey('Batch')
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

class DeliveryOption(models.Model):
    EACH_READY = 'As each product is ready'
    ALL_READY = 'Once all products are ready'
    OTHER = 'other'
    SHIPPING_CHOICES = (
        (EACH_READY, EACH_READY),
        (ALL_READY, ALL_READY),
        (OTHER, OTHER),
    )
    customizable_item = models.OneToOneField('CustomizableItem')
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

