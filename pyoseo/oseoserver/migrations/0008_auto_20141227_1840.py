# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0007_auto_20141227_1820'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collection',
            name='massive_order_configuration',
            field=models.OneToOneField(related_name='massive_collection', default=1, to='oseoserver.OrderConfiguration'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='collection',
            name='product_order_configuration',
            field=models.OneToOneField(related_name='product_collection', default=1, to='oseoserver.OrderConfiguration'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='collection',
            name='subscription_order_configuration',
            field=models.OneToOneField(related_name='subscription_collection', default=1, to='oseoserver.OrderConfiguration'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='collection',
            name='tasking_order_configuration',
            field=models.OneToOneField(related_name='tasking_collection', default=1, to='oseoserver.OrderConfiguration'),
            preserve_default=False,
        ),
    ]
