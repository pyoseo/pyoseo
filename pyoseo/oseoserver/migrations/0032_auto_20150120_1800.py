# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0031_auto_20150118_1833'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderitem',
            name='downloads',
        ),
        migrations.RemoveField(
            model_name='orderitem',
            name='file_name',
        ),
        migrations.AlterField(
            model_name='order',
            name='packaging',
            field=models.CharField(blank=True, max_length=30, choices=[(b'bzip2', b'bzip2'), (b'zip', b'zip')]),
            preserve_default=True,
        ),
    ]
