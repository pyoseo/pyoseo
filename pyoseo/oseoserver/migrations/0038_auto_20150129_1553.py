# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0037_oseofile_expires_on'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='oseouser',
            name='order_availability_days',
        ),
        migrations.AddField(
            model_name='ordertype',
            name='item_availability_days',
            field=models.PositiveSmallIntegerField(default=10, help_text=b'How many days will an item be available fordownload after it has been generated?'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='order',
            name='packaging',
            field=models.CharField(blank=True, max_length=30, choices=[(b'zip', b'zip')]),
            preserve_default=True,
        ),
    ]
