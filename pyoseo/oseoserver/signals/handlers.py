import datetime as dt
import pytz

from django.dispatch import receiver
from django.db.models.signals import post_save, post_init, pre_save
from django.contrib.auth.models import User
from django.conf import settings
from actstream import action
from mailqueue.models import MailerMessage

import oseoserver.models as models


@receiver(post_save, sender=User, weak=False,
          dispatch_uid="id_for_add_user_profile")
def add_user_profile_callback(sender, **kwargs):
    instance = kwargs['instance']
    try:
        profile = models.OseoUser.objects.get(user__id=instance.id)
    except models.OseoUser.DoesNotExist:
        profile = models.OseoUser()
        profile.user = kwargs['instance']
    profile.save()


@receiver(post_init, sender=models.TaskingOrder, weak=False,
          dispatch_uid='id_for_get_old_status_tasking_order')
@receiver(post_init, sender=models.SubscriptionOrder, weak=False,
          dispatch_uid='id_for_get_old_status_subscription_order')
@receiver(post_init, sender=models.MassiveOrder, weak=False,
          dispatch_uid='id_for_get_old_status_massive_order')
@receiver(post_init, sender=models.ProductOrder, weak=False,
          dispatch_uid='id_for_get_old_status_product_order')
def get_old_status_order(sender, **kwargs):
    order = kwargs['instance']
    order.old_status = order.status


@receiver(pre_save, sender=models.TaskingOrder, weak=False,
          dispatch_uid='id_for_update_status_changed_on_tasking_order')
@receiver(pre_save, sender=models.SubscriptionOrder, weak=False,
          dispatch_uid='id_for_update_status_changed_on_subscription_order')
@receiver(pre_save, sender=models.MassiveOrder, weak=False,
          dispatch_uid='id_for_update_status_changed_on_massive_order')
@receiver(pre_save, sender=models.ProductOrder, weak=False,
          dispatch_uid='id_for_update_status_changed_on_product_order')
def update_status_changed_on_order(sender, **kwargs):
    order = kwargs['instance']
    if order.status_changed_on is None or \
            order.status != order.old_status:
        order.status_changed_on = dt.datetime.now(pytz.utc)


@receiver(post_init, sender=models.OrderItem, weak=False,
          dispatch_uid='id_for_get_old_status_order_item')
def get_old_status_order_item(sender, **kwargs):
    order_item = kwargs['instance']
    order_item.old_status = order_item.status


@receiver(pre_save, sender=models.OrderItem, weak=False,
          dispatch_uid='id_for_update_status_changed_on_order_item')
def update_status_changed_on_by_order_item(sender, **kwargs):
    order_item = kwargs['instance']
    if order_item.status_changed_on is None or \
                    order_item.status != order_item.old_status:
        order_item.status_changed_on = dt.datetime.now(pytz.utc)


@receiver(post_save, sender=models.OrderItem, weak=False,
          dispatch_uid='id_for_update_batch')
def update_batch(sender, **kwargs):
    order_item = kwargs["instance"]
    batch = order_item.batch
    now = dt.datetime.now(pytz.utc)
    batch.updated_on = now
    status = batch.status()
    if status in (models.CustomizableItem.COMPLETED,
                          models.CustomizableItem.FAILED,
                          models.CustomizableItem.TERMINATED):
        batch.completed_on = now
    elif status == models.CustomizableItem.DOWNLOADED:
        pass
    else:
        batch.completed_on = None


@receiver(post_save, sender=models.Collection, weak=False,
          dispatch_uid='id_for_create_order_configurations')
def create_order_configurations(sender, **kwargs):
    c = kwargs["instance"]
    models.ProductOrderConfiguration.objects.get_or_create(collection=c)
    models.MassiveOrderConfiguration.objects.get_or_create(collection=c)
    models.SubscriptionOrderConfiguration.objects.get_or_create(collection=c)
    models.TaskingOrderConfiguration.objects.get_or_create(collection=c)


@receiver(post_save, sender=models.ProductOrder, weak=False,
          dispatch_uid='id_for_notify_product_order')
def notify_product_order(sender, **kwargs):
    order = kwargs["instance"]
    user = order.user
    if kwargs["created"]:
        if order.order_type.notify_creation:
            action.send(user, verb="created", target=order)
    else:
        if order.status == models.Order.COMPLETED:
            action.send(order, verb="has been completed")
        elif order.status == models.Order.FAILED:
            action.send(order, verb="has failed")

@receiver(post_save, sender=models.ProductOrder, weak=False,
          dispatch_uid='id_for_moderate_product_order')
def moderate_product_order(sender, **kwargs):
    order = kwargs["instance"]
    created = kwargs["created"]
    if created and not order.order_type.automatic_approval:
        for staff in User.objects.filter(is_staff=True):
            action.send(order, verb="awaits moderation by",
                        target=staff.oseouser)
