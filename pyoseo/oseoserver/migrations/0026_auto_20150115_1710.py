# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0025_auto_20150115_1623'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoiceaddress',
            name='order',
            field=models.OneToOneField(related_name='invoice_address', null=True, to='oseoserver.Order'),
            preserve_default=True,
        ),
    ]
