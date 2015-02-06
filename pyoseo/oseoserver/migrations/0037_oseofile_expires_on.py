# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0036_auto_20150127_1258'),
    ]

    operations = [
        migrations.AddField(
            model_name='oseofile',
            name='expires_on',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
