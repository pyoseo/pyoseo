# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0021_auto_20150107_0014'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='mediadelivery',
            unique_together=set([('package_medium', 'shipping_instructions')]),
        ),
    ]
