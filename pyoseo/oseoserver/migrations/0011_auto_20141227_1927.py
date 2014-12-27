# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0010_auto_20141227_1859'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderconfiguration',
            name='delivery_options',
            field=models.ManyToManyField(to='oseoserver.DeliveryOption', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='orderconfiguration',
            name='options',
            field=models.ManyToManyField(to='oseoserver.Option', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='orderconfiguration',
            name='payment_options',
            field=models.ManyToManyField(to='oseoserver.PaymentOption', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='orderconfiguration',
            name='scene_selection_options',
            field=models.ManyToManyField(to='oseoserver.SceneSelectionOption', null=True, blank=True),
            preserve_default=True,
        ),
    ]
