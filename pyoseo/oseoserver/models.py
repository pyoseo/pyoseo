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
from datetime import datetime
import pytz

from django.conf import settings
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User

import managers


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
    order = models.ForeignKey("Order", null=True, related_name="batches")
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
        if CustomizableItem.FAILED in item_statuses:
            status = CustomizableItem.FAILED
        elif len(item_statuses) == 1:
            status = item_statuses.pop()
        elif any(item_statuses):
            status = list(item_statuses)[0]
            for st in item_statuses:
                if order[st] < order[status]:
                    status = st
        else:
            status = None
        return status

    def price(self):
        total = Decimal(0)
        #order_fee = None
        #for oi in self.order_items.all():
        #    collection = oi.collection
        #    product_price = collection.product_price
        #    if order_fee is None:
        #        order_fee = collection.orderconfiguration.order_processing_fee
        #    total += product_price
        #total += order_fee
        return total

    def expired_files(self):
        now = datetime.now(pytz.utc)
        expired = OseoFile.objects.filter(available=True, expires_on__lt=now,
                                          order_item__batch=self)
        expired = list(expired)  # forcing evaluation of the queryset
        if self.order.user.delete_downloaded_order_files:
            downloaded = OseoFile.objects.filter(available=True,
                                                 downloads__gt=0,
                                                 order_item__batch=self)
            downloaded = list(downloaded)  # forcing evaluation of the queryset
            expired.extend(downloaded)
        return list(set(expired))

    class Meta:
        verbose_name_plural = "batches"

    def __unicode__(self):
        return str(self.id)


class Collection(models.Model):
    name = models.CharField(max_length=50, unique=True)
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

    def _product_orders_enabled(self):
        return "enabled" if self.productorderconfiguration.enabled \
            else "disabled"
    product_orders = property(_product_orders_enabled)

    def _massive_orders_enabled(self):
        return "enabled" if self.massiveorderconfiguration.enabled \
            else "disabled"
    massive_orders = property(_massive_orders_enabled)

    def _subscription_orders_enabled(self):
        return "enabled" if self.subscriptionorderconfiguration.enabled \
            else "disabled"
    subscription_orders = property(_subscription_orders_enabled)

    def _tasking_orders_enabled(self):
        return "enabled" if self.taskingorderconfiguration.enabled \
            else "disabled"
    tasking_orders = property(_tasking_orders_enabled)

    def allows_group(self, oseo_group):
        """
        Specify whether the input oseo_group can order from this collection
        """

        result = True
        try:
            self.authorized_groups.get(name=oseo_group.name)
        except self.DoesNotExist:
            result = False
        return result

    def __unicode__(self):
        return self.name


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
    order = models.OneToOneField("Order", null=True,
                                 related_name="invoice_address")

    class Meta:
        verbose_name_plural = "invoice addresses"


class ItemProcessor(models.Model):
    PROCESSING_PARSE_OPTION = "option_parsing"
    PROCESSING_PROCESS_ITEM = "item_processing"
    PROCESSING_CLEAN_ITEM = "item_cleanup"

    python_path = models.CharField(
        max_length=255,
        default="oseoserver.orderpreparation.noop.FakeOrderProcessor",
        help_text="Python import path to a custom class that is used to "
                  "process the order items. This class must conform to the "
                  "expected interface."
    )

    def export_params(self, processing_step):
        valid_params = dict()
        if processing_step == self.PROCESSING_PARSE_OPTION:
            qs = self.parameters.filter(use_in_option_parsing=True)
        elif processing_step == self.PROCESSING_PROCESS_ITEM:
            qs = self.parameters.filter(use_in_item_processing=True)
        else:
            qs = self.parameters.filter(use_in_item_cleanup=True)
        for param in qs:
            valid_params[param.name] = param.value
        return valid_params

    def __unicode__(self):
        return self.python_path


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
        unique_together = ("package_medium", "shipping_instructions")

    def __unicode__(self):
        return "{}:{}:{}".format(self.__class__.__name__, self.package_medium,
                                 self.shipping_instructions)


class Option(AbstractOption):

    def _get_choices(self):
        return ", ".join([c.value for c in self.choices.all()])
    available_choices = property(_get_choices)

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

    enabled = models.BooleanField(default=False)
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
        return "{}".format("Enabled" if self.enabled else "Disabled")


class ProductOrderConfiguration(OrderConfiguration):
    collection = models.OneToOneField("Collection", null=False)


class MassiveOrderConfiguration(OrderConfiguration):
    collection = models.OneToOneField("Collection", null=False)


class SubscriptionOrderConfiguration(OrderConfiguration):
    collection = models.OneToOneField("Collection", null=False)


class TaskingOrderConfiguration(OrderConfiguration):
    collection = models.OneToOneField("Collection", null=False)


class Order(CustomizableItem):
    MAX_ORDER_ITEMS = getattr(settings, "MAX_ORDER_ITEMS", 200)
    PRODUCT_ORDER = 'PRODUCT_ORDER'
    SUBSCRIPTION_ORDER = 'SUBSCRIPTION_ORDER'
    MASSIVE_ORDER = 'MASSIVE_ORDER'
    TASKING_ORDER = 'TASKING_ORDER'
    ZIP = "zip"
    PACKAGING_CHOICES = (
        (ZIP, ZIP),
    )
    STANDARD = "STANDARD"
    FAST_TRACK = "FAST_TRACK"
    PRIORITY_CHOICES = ((STANDARD, STANDARD), (FAST_TRACK, FAST_TRACK))
    NONE = 'None'
    FINAL = 'Final'
    ALL = 'All'
    STATUS_NOTIFICATION_CHOICES = (
        (NONE, NONE),
        (FINAL, FINAL),
        (ALL, ALL),
    )
    user = models.ForeignKey("OseoUser", related_name="orders")
    order_type = models.ForeignKey("OrderType", related_name="orders")
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
    status_notification = models.CharField(max_length=10, default=NONE,
                                           choices=STATUS_NOTIFICATION_CHOICES)

    def show_batches(self):
        return ', '.join([str(b.id) for b in self.batches.all()])
    show_batches.short_description = 'available batches'

    def __unicode__(self):
        return '{}'.format(self.id)


class OrderPendingModeration(Order):
    objects = managers.OrderPendingModerationManager()

    class Meta:
        proxy = True
        verbose_name_plural = "orders pending moderation"



class ProductOrder(Order):

    def create_batch(self, item_status, *order_item_spec):
        batch = Batch()
        batch.save()
        for oi in order_item_spec:
            item = OrderItem(
                batch=batch,
                status=item_status,
                additional_status_info="Order item has been submitted and "
                                       "is awaiting approval",
                remark=oi["order_item_remark"],
                collection=oi["collection"],
                identifier=oi["identifier"],
                item_id=oi["item_id"]
            )
            item.save()

            for k, v in oi["option"].iteritems():
                option = Option.objects.get(name=k)
                item.selected_options.add(SelectedOption(option=option,
                                                         value=v))
            for k, v in oi["scene_selection"].iteritems():
                item.selected_scene_selection_options.add(
                    SelectedSceneSelectionOption(option=k, value=v))
            delivery = oi["delivery_options"]
            if delivery is not None:
                copies = 1 if delivery["copies"] is None else delivery["copies"]
                sdo = SelectedDeliveryOption(
                    customizable_item=item,
                    annotation=delivery["annotation"],
                    copies=copies,
                    special_instructions=delivery["special_instructions"],
                    option=delivery["type"]
                )
                sdo.save()
            if oi["payment"] is not None:
                payment = PaymentOption.objects.get(oi["payment"])
                item.selected_payment_option = SelectedPaymentOption(
                    option=payment)
            item.save()
        self.batches.add(batch)
        return batch

    def __unicode__(self):
        return "ProductOrder({})".format(self.id)


class DerivedOrder(Order):
    collections = models.ManyToManyField("Collection",
                                         related_name="derived_orders")

    def create_batch(self):
        raise NotImplementedError


class MassiveOrder(DerivedOrder):
    pass


class SubscriptionOrder(DerivedOrder):
    pass


class TaskingOrder(DerivedOrder):
    pass


class OrderType(models.Model):
    name = models.CharField(max_length=30)
    enabled = models.BooleanField(default=False)
    automatic_approval = models.BooleanField(default=False)
    notify_creation = models.BooleanField(default=True)
    item_processor = models.ForeignKey("ItemProcessor")
    item_availability_days = models.PositiveSmallIntegerField(
        default=10,
        help_text="How many days will an item be available for "
                  "download after it has been generated?"
    )

    def __unicode__(self):
        return self.name


class OrderItem(CustomizableItem):
    batch = models.ForeignKey("Batch", related_name="order_items")
    collection = models.ForeignKey("Collection")
    identifier = models.CharField(max_length=255, blank=True,
                                  help_text="identifier for this order item. "
                                            "It is the product Id in the "
                                            "catalog")
    item_id = models.CharField(max_length=30, help_text="Id for the item in "
                                                        "the order request")

    def export_options(self):
        valid_options = dict()
        for order_option in self.batch.order.selected_options.all():
            valid_options[order_option.option.name] = order_option.value
        for item_option in self.selected_options.all():
            valid_options[item_option.option.name] = item_option.value
        return valid_options

    def export_delivery_options(self):
        delivery = getattr(self, "selected_delivery_option", None)
        if delivery is None:
            delivery = getattr(self.batch.order, "selected_delivery_option")
        valid_delivery = {
            "copies": delivery.copies,
            "annotation": delivery.annotation,
            "special_instructions": delivery.special_instructions,
            "delivery_fee": delivery.option.delivery_fee,
        }
        if hasattr(delivery.option, "onlinedataaccess"):
            valid_delivery["delivery_type"] = "onlinedataaccess"
            valid_delivery["protocol"] = \
                delivery.option.onlinedataaccess.protocol
        elif hasattr(delivery.option, "onlinedatadelivery"):
            valid_delivery["delivery_type"] = "onlinedatadelivery"
            valid_delivery["protocol"] = \
                delivery.option.onlinedatadelivery.protocol
        else:  # media delivery
            valid_delivery["delivery_type"] = "mediadelivery"
        return valid_delivery

    def __unicode__(self):
        return str(self.item_id)


class OseoFile(models.Model):
    order_item = models.ForeignKey("OrderItem", related_name="files")
    created_on = models.DateTimeField(auto_now_add=True)
    url = models.CharField(max_length=255, help_text="URL where this file "
                                                     "is available")
    expires_on = models.DateTimeField(null=True, blank=True)
    available = models.BooleanField(default=False)
    downloads = models.SmallIntegerField(default=0,
                                         help_text="Number of times this "
                                                   "order item has been "
                                                   "downloaded.")

    def can_be_deleted(self):
        result = False
        now = datetime.now(pytz.utc)
        if self.expires_on < now:
            result = True
        else:
            user = self.order_item.batch.order.user
            if self.downloads > 0 and user.delete_downloaded_files:
                result = True
        return result

    def __unicode__(self):
        return self.url


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

    def __unicode__(self):
        return self.name


class OseoUser(models.Model):
    user = models.OneToOneField(User)
    oseo_group = models.ForeignKey("OseoGroup", blank=True, null=True)
    disk_quota = models.SmallIntegerField(default=50, help_text='Disk space '
                                          'available to each user. Expressed '
                                          'in Gigabytes')
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


class ProcessorParameter(models.Model):
    item_processor = models.ForeignKey("ItemProcessor",
                                       related_name="parameters")
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    use_in_option_parsing = models.BooleanField(default=False)
    use_in_item_processing = models.BooleanField(default=False)
    use_in_item_cleanup = models.BooleanField(default=False)

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
    order_item = models.OneToOneField('OrderItem',
                                      related_name='selected_payment_option',
                                      null=True,
                                      blank=True)
    option = models.ForeignKey('PaymentOption')

    def __unicode__(self):
        return self.option.name


class SelectedSceneSelectionOption(models.Model):
    order_item = models.ForeignKey(
        'OrderItem',
        related_name='selected_scene_selection_options'
    )
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

    def __unicode__(self):
        return self.option.__unicode__()


