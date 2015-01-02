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

from decimal import Decimal

from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User


class AbstractDeliveryAddress(models.Model):
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

    class Meta:
        abstract = True


class AbstractOption(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        abstract = True


class AbstractOptionChoice(models.Model):
    value = models.CharField(max_length=255, help_text="Value for this option")

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.value


class Batch(models.Model):
    order = models.ForeignKey("Order", related_name="batches")
    created_on = models.DateTimeField(auto_now_add=True)
    completed_on = models.DateTimeField(null=True, blank=True)
    updated_on = models.DateTimeField(editable=False, blank=True, null=True)

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

    def price(self):
        total = Decimal(0)
        order_fee = None
        for oi in self.order_items.all():
            collection = oi.collection
            product_price = collection.product_price
            if order_fee is None:
                order_fee = collection.orderconfiguration.order_processing_fee
            total += product_price
        total += order_fee
        return total

    class Meta:
        verbose_name_plural = "batches"

    def __unicode__(self):
        return str(self.id)


class Collection(models.Model):
    short_name = models.CharField(max_length=50, unique=True)
    authorized_groups = models.ManyToManyField("OseoGroup", null=True,
                                               blank=True)
    catalogue_endpoint = models.CharField(
        max_length=255,
        help_text="URL of the CSW server where this collection is available"
    )
    collection_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="Identifier of the dataset series for this collection in "
                  "the catalogue"
    )
    product_price = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text="The price of an individual product",
        default=Decimal(0)
    )
    item_preparation_class = models.CharField(
        max_length=255,
        help_text="Python path to a custom class used for preparing "
                  "order items"
    )

    def __unicode__(self):
        return self.short_name


class CustomizableItem(models.Model):
    SUBMITTED = "Submitted"
    ACCEPTED = "Accepted"
    IN_PRODUCTION = "InProduction"
    SUSPENDED = "Suspended"
    CANCELLED = "Cancelled"
    COMPLETED = "Completed"
    FAILED = "Failed"
    TERMINATED = "Terminated"
    DOWNLOADED = "Downloaded"
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
                              default=SUBMITTED, help_text="initial status")
    additional_status_info = models.TextField(help_text="Additional "
                                              "information about the status",
                                              blank=True)
    mission_specific_status_info = models.TextField(help_text="Additional "
                                                    "information about the "
                                                    "status that is specific "
                                                    "to the mission",
                                                    blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    completed_on = models.DateTimeField(null=True, blank=True)
    status_changed_on = models.DateTimeField(editable=False, blank=True,
                                             null=True)
    remark = models.TextField(help_text="Some specific remark about the item",
                              blank=True)

    def __unicode__(self):
        try:
            instance = Order.objects.get(id=self.id)
        except ObjectDoesNotExist:
            instance = OrderItem.objects.get(id=self.id)
        return instance.__unicode__()


class DeliveryInformation(AbstractDeliveryAddress):
    order = models.OneToOneField("Order", related_name="delivery_information")


class DeliveryOption(models.Model):
    FTP = "ftp"
    SFTP = "sftp"
    FTPS = "ftps"
    P2P = "P2P"
    WCS = "wcs"
    WMS = "wms"
    E_MAIL = "e-mail"
    DDS = "dds"
    HTTP = "http"
    HTTPS = "https"
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
    delivery_fee = models.DecimalField(default=Decimal(0), max_digits=5,
                                       decimal_places=2)

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


class InvoiceAddress(AbstractDeliveryAddress):
    order = models.OneToOneField("Order", related_name="invoice_address")

    class Meta:
        verbose_name_plural = "invoice addresses"


class MediaDelivery(DeliveryOption):
    NTP = "NTP"
    DAT = "DAT"
    EXABYTE = "Exabyte"
    CD_ROM = "CD-ROM"
    DLT = "DLT"
    D1 = "D1"
    DVD = "DVD"
    BD = "BD"
    LTO = "LTO"
    LTO2 = "LTO2"
    LTO4 = "LTO4"
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
    EACH_READY = "as each product is ready"
    ALL_READY = "once all products are ready"
    OTHER = "other"
    SHIPPING_CHOICES = (
        (EACH_READY, EACH_READY),
        (ALL_READY, ALL_READY),
        (OTHER, OTHER),
    )
    shipping_instructions = models.CharField(
        max_length=100,
        choices=SHIPPING_CHOICES,
        blank=True
    )

    class Meta:
        verbose_name_plural = "media deliveries"

    def __unicode__(self):
        return "{}:{}".format(self.__class__.__name__, self.package_medium)


class Option(AbstractOption):

    def __unicode__(self):
        return self.name


class OptionChoice(AbstractOptionChoice):
    option = models.ForeignKey('Option', related_name='choices')


class OnlineDataAccess(DeliveryOption):
    protocol = models.CharField(max_length=20,
                                choices=DeliveryOption.PROTOCOL_CHOICES,
                                default=DeliveryOption.FTP,
                                unique=True)

    class Meta:
        verbose_name_plural = 'online data accesses'

    def __unicode__(self):
        return "{}:{}".format(self.__class__.__name__, self.protocol)


class OnlineDataDelivery(DeliveryOption):
    protocol = models.CharField(
        max_length=20,
        choices=DeliveryOption.PROTOCOL_CHOICES,
        default=DeliveryOption.FTP,
        unique=True
    )

    class Meta:
        verbose_name_plural = 'online data deliveries'

    def __unicode__(self):
        return "{}:{}".format(self.__class__.__name__, self.protocol)


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


class OrderConfiguration(models.Model):

    collection = models.OneToOneField("Collection")
    enabled = models.BooleanField(default=False)
    automatic_approval = models.BooleanField(
        default=False,
        help_text="Should this type of order be approved automatically for "
                  "the selected collection?"
    )
    order_processing_fee = models.DecimalField(default=Decimal(0),
                                               max_digits=5,
                                               decimal_places=2)
    options = models.ManyToManyField("Option", null=True, blank=True)
    delivery_options = models.ManyToManyField("DeliveryOption", null=True,
                                              blank=True)
    payment_options = models.ManyToManyField("PaymentOption", null=True,
                                             blank=True)
    scene_selection_options = models.ManyToManyField("SceneSelectionOption",
                                                     null=True, blank=True)

    def __unicode__(self):
        return "{}:{}".format("Enabled" if self.enabled else "Disabled",
                              "Auto" if self.automatic_approval else "Manual")


class ProductOrderConfiguration(OrderConfiguration):
    pass


class MassiveOrderConfiguration(OrderConfiguration):
    pass


class SubscriptionOrderConfiguration(OrderConfiguration):
    pass


class TaskingOrderConfiguration(OrderConfiguration):
    pass


class Order(CustomizableItem):
    BZIP2 = "bzip2"
    PACKAGING_CHOICES = (
        (BZIP2, BZIP2),
    )
    STANDARD = "STANDARD"
    FAST_TRACK = "FAST_TRACK"
    PRIORITY_CHOICES = ((STANDARD, STANDARD), (FAST_TRACK, FAST_TRACK))
    PRODUCT_ORDER = 'PRODUCT_ORDER'
    SUBSCRIPTION_ORDER = 'SUBSCRIPTION_ORDER'
    MASSIVE_ORDER = 'MASSIVE_ORDER'
    TASKING_ORDER = 'TASKING_ORDER'
    ORDER_TYPE_CHOICES = (
        (PRODUCT_ORDER, PRODUCT_ORDER),
        (MASSIVE_ORDER, MASSIVE_ORDER),
        (SUBSCRIPTION_ORDER, SUBSCRIPTION_ORDER),
        (TASKING_ORDER, TASKING_ORDER),
    )
    user = models.ForeignKey("OseoUser", related_name="orders")
    order_type = models.CharField(max_length=30, choices=ORDER_TYPE_CHOICES,
                                  default=PRODUCT_ORDER)
    last_describe_result_access_request = models.DateTimeField(null=True,
                                                               blank=True)
    reference = models.CharField(max_length=30,
                                 help_text="Some specific reference about "
                                           "this order",
                                 blank=True)
    packaging = models.CharField(max_length=30,
                                 choices=PACKAGING_CHOICES,
                                 blank=True)
    priority = models.CharField(max_length=30,
                                choices=PRIORITY_CHOICES,
                                blank=True)

    def show_batches(self):
        return ', '.join([str(b.id) for b in self.batches.all()])
    show_batches.short_description = 'available batches'

    def __unicode__(self):
        return '{}({})'.format(self.order_type, self.id)


class OrderItem(CustomizableItem):
    batch = models.ForeignKey("Batch", related_name="order_items")
    collection = models.ForeignKey("Collection")
    identifier = models.CharField(max_length=255, blank=True,
                                  help_text="identifier for this order item. "
                                            "It is the product Id in the "
                                            "catalog")
    item_id = models.CharField(max_length=30, help_text="Id for the item in "
                                                        "the order request")
    file_name = models.CharField(max_length=255,
                                 help_text="name of the file that this order "
                                           "item represents",
                                 blank=True)
    downloads = models.SmallIntegerField(default=0,
                                         help_text="Number of times this "
                                                   "order item has been "
                                                   "downloaded.")
    #    last_downloaded_on = models.DateTimeField(editable=False, blank=True,
    #                                              null=True)

    def __unicode__(self):
        return str(self.item_id)


class OseoGroup(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    authentication_class = models.CharField(
        max_length=255,
        help_text="Python path to a custom authentication class to use when"
                  "validating orders for users belonging to this group",
        blank=True
    )
    # these fields are probably not needed
    #product_orders_enabled = models.BooleanField(default=False)
    #massive_orders_enabled = models.BooleanField(default=False)
    #subscription_orders_enabled = models.BooleanField(default=False)
    #tasking_orders_enabled = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name


class OseoUser(models.Model):
    user = models.OneToOneField(User)
    oseo_group = models.ForeignKey("OseoGroup")
    disk_quota = models.SmallIntegerField(default=50, help_text='Disk space '
                                          'available to each user. Expressed '
                                          'in Gigabytes')
    order_availability_days = models.SmallIntegerField(
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


class PaymentOption(AbstractOption):

    def __unicode__(self):
        return self.name


class SceneSelectionOption(AbstractOption):

    def __unicode__(self):
        return self.name


class SceneSelectionOptionChoice(AbstractOptionChoice):
    scene_selection_option = models.ForeignKey('SceneSelectionOption',
                                               related_name='choices')


class SelectedOption(models.Model):
    customizable_item = models.ForeignKey('CustomizableItem',
                                          related_name='selected_options')
    option = models.ForeignKey('Option')
    value = models.CharField(max_length=255, help_text='Value for this option')

    def __unicode__(self):
        return self.value


class SelectedPaymentOption(models.Model):
    order_item = models.OneToOneField('OrderItem', null=True, blank=True)
    option = models.ForeignKey('PaymentOption')

    def __unicode__(self):
        return self.option.name


class SelectedSceneSelectionOption(models.Model):
    order_item = models.ForeignKey('OrderItem')
    option = models.ForeignKey('SceneSelectionOption')
    value = models.CharField(max_length=255,
                             help_text='Value for this option')

    def __unicode__(self):
        return self.value


class SelectedDeliveryOption(models.Model):
    customizable_item = models.OneToOneField(
        'CustomizableItem',
        related_name='selected_delivery_option',
        blank=True,
        null=True
    )
    option = models.ForeignKey('DeliveryOption')
    copies = models.PositiveSmallIntegerField(null=True, blank=True)
    annotation = models.TextField(blank=True)
    special_instructions = models.TextField(blank=True)
