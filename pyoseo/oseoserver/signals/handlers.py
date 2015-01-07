import datetime as dt
import pytz

from django.dispatch import receiver
from django.db.models.signals import post_save, post_init, pre_save
from django.contrib.auth.models import User

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


@receiver(post_init, sender=models.Order, weak=False,
          dispatch_uid='id_for_get_old_status_order')
def get_old_status_order(sender, **kwargs):
    order = kwargs['instance']
    order.old_status = order.status


@receiver(post_init, sender=models.OrderItem, weak=False,
          dispatch_uid='id_for_get_old_status_order_item')
def get_old_status_order_item(sender, **kwargs):
    order_item = kwargs['instance']
    order_item.old_status = order_item.status


@receiver(pre_save, sender=models.Order, weak=False,
          dispatch_uid='id_for_update_status_changed_on_order')
def update_status_changed_on_by_order(sender, **kwargs):
    order = kwargs['instance']
    if order.status_changed_on is None or \
            order.status != order.old_status:
        order.status_changed_on = dt.datetime.now(pytz.utc)


@receiver(pre_save, sender=models.OrderItem, weak=False,
          dispatch_uid='id_for_update_status_changed_on_order_item')
def update_status_changed_on_by_order_item(sender, **kwargs):
    order_item = kwargs['instance']
    if order_item.status_changed_on is None or \
                    order_item.status != order_item.old_status:
        order_item.status_changed_on = dt.datetime.now(pytz.utc)

@receiver(pre_save, sender=models.OrderItem, weak=False,
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
