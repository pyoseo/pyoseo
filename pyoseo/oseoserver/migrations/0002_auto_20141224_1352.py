# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ordertype',
            name='automatic_approval',
            field=models.BooleanField(default=False, help_text=b'Should this type of order be approved automatically?'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='ordertype',
            name='name',
            field=models.CharField(default=b'PRODUCT_ORDER', unique=True, max_length=30, choices=[(b'PRODUCT_ORDER', b'PRODUCT_ORDER'), (b'MASSIVE_ORDER', b'MASSIVE_ORDER'), (b'SUBSCRIPTION_ORDER', b'SUBSCRIPTION_ORDER'), (b'TASKING_ORDER', b'TASKING_ORDER')]),
            preserve_default=True,
        ),
    ]
