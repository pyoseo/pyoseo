# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0006_auto_20141227_1803'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collection',
            name='massive_order_configuration',
            field=models.OneToOneField(related_name='massive_collection', null=True, blank=True, to='oseoserver.OrderConfiguration'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='collection',
            name='product_order_configuration',
            field=models.OneToOneField(related_name='product_collection', null=True, blank=True, to='oseoserver.OrderConfiguration'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='collection',
            name='subscription_order_configuration',
            field=models.OneToOneField(related_name='subscription_collection', null=True, blank=True, to='oseoserver.OrderConfiguration'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='collection',
            name='tasking_order_configuration',
            field=models.OneToOneField(related_name='tasking_collection', null=True, blank=True, to='oseoserver.OrderConfiguration'),
            preserve_default=True,
        ),
    ]
