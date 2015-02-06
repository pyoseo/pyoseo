# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0012_auto_20141227_1929'),
    ]

    operations = [
        migrations.AlterField(
            model_name='selectedpaymentoption',
            name='order_item',
            field=models.OneToOneField(null=True, blank=True, to='oseoserver.OrderItem'),
            preserve_default=True,
        ),
    ]
