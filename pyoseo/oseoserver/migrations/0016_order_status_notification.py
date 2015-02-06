# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0015_auto_20141230_1903'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='status_notification',
            field=models.CharField(default=b'None', max_length=10, choices=[(b'None', b'None'), (b'Final', b'Final'), (b'All', b'All')]),
            preserve_default=True,
        ),
    ]
