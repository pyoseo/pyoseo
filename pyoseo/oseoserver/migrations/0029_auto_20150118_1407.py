# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0028_ordertype'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderconfiguration',
            name='automatic_approval',
        ),
        migrations.AddField(
            model_name='order',
            name='order_type',
            field=models.ForeignKey(related_name='orders', default=1, to='oseoserver.OrderType'),
            preserve_default=False,
        ),
    ]
