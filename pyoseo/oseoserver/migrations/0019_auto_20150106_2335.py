# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0018_auto_20150106_2220'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='massiveorderconfiguration',
            name='collection',
        ),
        migrations.RemoveField(
            model_name='productorderconfiguration',
            name='collection',
        ),
        migrations.RemoveField(
            model_name='subscriptionorderconfiguration',
            name='collection',
        ),
        migrations.RemoveField(
            model_name='taskingorderconfiguration',
            name='collection',
        ),
        migrations.AddField(
            model_name='collection',
            name='massive_order_configuration',
            field=models.OneToOneField(default=1, to='oseoserver.MassiveOrderConfiguration'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='collection',
            name='product_order_configuration',
            field=models.OneToOneField(default=1, to='oseoserver.ProductOrderConfiguration'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='collection',
            name='subscription_order_configuration',
            field=models.OneToOneField(default=1, to='oseoserver.SubscriptionOrderConfiguration'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='collection',
            name='tasking_order_configuration',
            field=models.OneToOneField(default=1, to='oseoserver.TaskingOrderConfiguration'),
            preserve_default=False,
        ),
    ]
