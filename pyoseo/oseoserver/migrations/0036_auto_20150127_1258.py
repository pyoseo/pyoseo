# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0035_auto_20150127_1207'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='oseofile',
            name='name',
        ),
        migrations.AddField(
            model_name='oseofile',
            name='url',
            field=models.CharField(default='nothing', help_text=b'URL where this file is available', max_length=255),
            preserve_default=False,
        ),
    ]
