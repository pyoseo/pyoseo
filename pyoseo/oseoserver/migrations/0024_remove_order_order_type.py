# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0023_auto_20150115_1445'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='order_type',
        ),
    ]
