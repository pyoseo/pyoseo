# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0003_remove_orderconfiguration_collection'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderconfiguration',
            name='description',
            field=models.TextField(blank=True),
            preserve_default=True,
        ),
    ]
