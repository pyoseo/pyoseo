# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0016_order_status_notification'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderconfiguration',
            name='collection',
            field=models.ForeignKey(to='oseoserver.Collection'),
            preserve_default=True,
        ),
    ]
