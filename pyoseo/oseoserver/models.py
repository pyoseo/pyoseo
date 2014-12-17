# Copyright 2014 Ricardo Garcia Silva
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""
Database models for pyoseo
"""

import datetime as dt

from django.db import models
from django.db.models import signals
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
import pytz

class OseoUser(models.Model):
    user = models.OneToOneField(User)
    disk_quota = models.SmallIntegerField(default=50, help_text='Disk space '
                                          'available to each user. Expressed '
                                          'in Gigabytes')
    order_availability_time = models.SmallIntegerField(
        default=10,
        help_text='How many days does a completed order stay on the server, '
                  'waiting to be downloaded'
    )
    delete_downloaded_order_files = models.BooleanField(
        default=True,
        help_text='If this option is selected, ordered items will be deleted '
                  'from the server as soon as their download has been '
                  'aknowledged. If not, the ordered items are only deleted '
                  'after the expiration of the "order availability time" '
                  'period.'
    )

    def __unicode__(self):
        return self.user.username

class OptionGroup(models.Model):
    name = models.CharField(max_length=40, help_text='Id for the group of '
                            'options')
    description = models.CharField(max_length=255, help_text='Description of '
                                   'the order option group', blank=True)

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
    completed_on = models.DateTimeField(null=True, blank=True)
    status_changed_on = models.DateTimeField(editable=False, blank=True, null=True)
    remark = models.TextField(help_text='Some specific remark about the item',
                              blank=True)
    option_group = models.ForeignKey('OptionGroup',
                                     related_name='customizable_item')

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
    user = models.ForeignKey(OseoUser, related_name='orders')
    order_type = models.ForeignKey('OrderType', related_name='orders')
    last_describe_result_access_request = models.DateTimeField(null=True,
                                                               blank=True)
    reference = models.CharField(max_length=30, help_text='Some specific '
                                 'reference about this order', blank=True)
    packaging = models.CharField(max_length=30, choices=PACKAGING_CHOICES,
                                 blank=True)
    priority = models.CharField(max_length=30, choices=PRIORITY_CHOICES,
                                blank=True)

    def show_batches(self):
        return ', '.join([str(b.id) for b in self.batches.all()])
    show_batches.short_description = 'available batches'

    def __unicode__(self):
        return '%s(%i)' % (self.order_type.name, self.id)

class Batch(models.Model):
    order = models.ForeignKey('Order', related_name='batches')

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
        if any(item_statuses):
            status = list(item_statuses)[0]
            for st in item_statuses:
                if order[st] < order[status]:
                    status = st
        else:
            status = None
        return status

    class Meta:
        verbose_name_plural = 'batches'

    def __unicode__(self):
        return str(self.id)

class OrderItem(CustomizableItem):
    batch = models.ForeignKey('Batch', related_name='order_items')
    item_id = models.CharField(max_length=30, help_text='Id for the item in '
                               'the order request')
    identifier = models.CharField(max_length=255, help_text='identifier for '
                                  'this order item. It is the product Id in '
                                  'the catalog', blank=True)
    collection_id = models.CharField(max_length=255, help_text='identifier for '
                                  'the collection. It is the id of the '
                                  'collection in the catalog', blank=True)
    file_name = models.CharField(max_length=255, help_text='name of the file '
                                 'that this order item represents', blank=True)
    downloads = models.SmallIntegerField(default=0, help_text='Number of '
                                         'times this order item has been '
                                         'downloaded.')
    #last_downloaded_on = models.DateTimeField(editable=False, blank=True,
    #                                          null=True)

    def __unicode__(self):
        return str(self.item_id)

class DeliveryOption(models.Model):

    def child_instance(self):
        try:
            instance = OnlineDataAccess.objects.get(id=self.id)
        except ObjectDoesNotExist:
            try:
                instance = OnlineDataDelivery.objects.get(id=self.id)
            except ObjectDoesNotExist:
                try:
                    instance = MediaDelivery.objects.get(id=self.id)
                except ObjectDoesNotExist:
                    instance = self
        return instance

    def __unicode__(self):
        instance = self.child_instance()
        return instance.__unicode__()

class GroupDeliveryOption(models.Model):
    delivery_option = models.ForeignKey('DeliveryOption')
    option_group = models.ForeignKey('OptionGroup')

    def __unicode__(self):
        return '%s:%s' % (self.delivery_option, self.option_group)

class SelectedDeliveryOption(models.Model):
    group_delivery_option = models.ForeignKey('GroupDeliveryOption')
    customizable_item = models.OneToOneField(
        'CustomizableItem',
        related_name='selected_delivery_option',
        blank=True,
        null=True
    )
    copies = models.PositiveSmallIntegerField(null=True, blank=True)
    annotation = models.TextField(blank=True)
    special_instructions = models.TextField(blank=True)

class OnlineDataAccess(DeliveryOption):
    FTP = 'ftp'
    SFTP = 'sftp'
    FTPS = 'ftps'
    P2P = 'P2P'
    WCS = 'wcs'
    WMS = 'wms'
    E_MAIL = 'e-mail'
    DDS = 'dds'
    HTTP = 'http'
    HTTPS = 'https'
    PROTOCOL_CHOICES = (
        (FTP, FTP),
        (SFTP, SFTP),
        (FTPS, FTPS),
        (P2P, P2P),
        (WCS, WCS),
        (WMS, WMS),
        (E_MAIL, E_MAIL),
        (DDS, DDS),
        (HTTP, HTTP),
        (HTTPS, HTTPS),
    )
    protocol = models.CharField(max_length=20, choices=PROTOCOL_CHOICES,
                                default=FTP, unique=True)

    class Meta:
        verbose_name_plural = 'online data accesses'

    def __unicode__(self):
        return '%s:%s' % (self.__class__.__name__, self.protocol)

class OnlineDataDelivery(DeliveryOption):
    protocol = models.CharField(
        max_length=20,
        choices=OnlineDataAccess.PROTOCOL_CHOICES,
        default=OnlineDataAccess.FTP,
        unique=True
    )

    class Meta:
        verbose_name_plural = 'online data deliveries'

    def __unicode__(self):
        return '%s:%s' % (self.__class__.__name__, self.protocol)

class MediaDelivery(DeliveryOption):
    NTP = 'NTP'
    DAT = 'DAT'
    EXABYTE = 'Exabyte'
    CD_ROM = 'CD-ROM'
    DLT = 'DLT'
    D1 = 'D1'
    DVD = 'DVD'
    BD = 'BD'
    LTO = 'LTO'
    LTO2 = 'LTO2'
    LTO4 = 'LTO4'
    PACKAGE_MEDIUM_CHOICES = (
        (NTP, NTP),
        (DAT, DAT),
        (EXABYTE, EXABYTE),
        (CD_ROM, CD_ROM),
        (DLT, DLT),
        (D1, D1),
        (DVD, DVD),
        (BD, BD),
        (LTO, LTO),
        (LTO2, LTO2),
        (LTO4, LTO4),
    )

    package_medium = models.CharField(
        max_length=20,
        choices=PACKAGE_MEDIUM_CHOICES,
        blank=True
    )
    EACH_READY = 'as each product is ready'
    ALL_READY = 'once all products are ready'
    OTHER = 'other'
    SHIPPING_CHOICES = (
        (EACH_READY, EACH_READY),
        (ALL_READY, ALL_READY),
        (OTHER, OTHER),
    )
    shipping_instructions = models.CharField(
        max_length=100,
        choices= SHIPPING_CHOICES,
        blank=True
    )

    class Meta:
        verbose_name_plural = 'media deliveries'

    def __unicode__(self):
        return '%s:%s' % (self.__class__.__name__, self.package_medium)

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

#TODO: add a description attribute for this model
class Option(models.Model):
    name = models.CharField(max_length=100)
    product = models.ForeignKey('Product', null=True, blank=True)
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

class OptionOrderType(models.Model):
    option = models.ForeignKey('Option')
    order_type = models.ForeignKey('OrderType')

    def __unicode__(self):
        return '%s:%s' % (self.option, self.order_type)

class DeliveryOptionOrderType(models.Model):
    delivery_option = models.ForeignKey('DeliveryOption')
    order_type = models.ForeignKey('OrderType')

    def __unicode__(self):
        return '%s:%s' % (self.delivery_option, self.order_type)

class OptionChoice(models.Model):
    option = models.ForeignKey('Option', related_name='choices')
    value = models.CharField(max_length=255, help_text='Value for this option')

    def __unicode__(self):
        return self.value

class GroupOption(models.Model):
    option = models.ForeignKey('Option', related_name='group_options')
    group = models.ForeignKey('OptionGroup')

    def __unicode__(self):
        return '%s:%s' % (self.group, self.option)

class SelectedOption(models.Model):
    group_option = models.ForeignKey('GroupOption')
    customizable_item = models.ForeignKey('CustomizableItem',
                                          related_name='selected_options')
    value = models.CharField(max_length=255, help_text='Value for this option')

    def __unicode__(self):
        return self.value

# signal handlers

def add_user_profile_callback(sender, **kwargs):
    instance = kwargs['instance']
    try:
        profile = OseoUser.objects.get(user__id=instance.id)
    except ObjectDoesNotExist:
        profile = OseoUser()
        profile.user = kwargs['instance']
    profile.save()

def get_old_status_callback(sender, **kwargs):
    instance = kwargs['instance']
    instance.old_status = instance.status

def update_status_changed_on_callback(sender, **kwargs):
    instance = kwargs['instance']
    if instance.status_changed_on is None or \
            instance.status != instance.old_status:
        instance.status_changed_on = dt.datetime.now(pytz.utc)

signals.post_save.connect(
    add_user_profile_callback,
    User,
    weak=False,
    dispatch_uid='id_for_add_user_profile'
)

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
