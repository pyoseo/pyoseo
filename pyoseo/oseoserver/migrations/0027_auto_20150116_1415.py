# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0026_auto_20150115_1710'),
    ]

    operations = [
        migrations.AlterField(
            model_name='batch',
            name='order',
            field=models.ForeignKey(related_name='batches', to='oseoserver.Order', null=True),
            preserve_default=True,
        ),
    ]
