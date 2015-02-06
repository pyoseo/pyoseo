# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0013_auto_20141227_1959'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderconfiguration',
            name='description',
        ),
        migrations.RemoveField(
            model_name='orderconfiguration',
            name='name',
        ),
    ]
