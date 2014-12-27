# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0009_auto_20141227_1850'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='collection',
            name='massive_order_configuration',
        ),
        migrations.RemoveField(
            model_name='collection',
            name='product_order_configuration',
        ),
        migrations.RemoveField(
            model_name='collection',
            name='subscription_order_configuration',
        ),
        migrations.RemoveField(
            model_name='collection',
            name='tasking_order_configuration',
        ),
        migrations.AddField(
            model_name='orderconfiguration',
            name='collection',
            field=models.OneToOneField(default=1, to='oseoserver.Collection'),
            preserve_default=False,
        ),
    ]
