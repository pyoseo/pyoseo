# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0011_auto_20141227_1927'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='availabledeliveryoption',
            name='option',
        ),
        migrations.RemoveField(
            model_name='availabledeliveryoption',
            name='order_configuration',
        ),
        migrations.DeleteModel(
            name='AvailableDeliveryOption',
        ),
        migrations.RemoveField(
            model_name='availableoption',
            name='option',
        ),
        migrations.RemoveField(
            model_name='availableoption',
            name='order_configuration',
        ),
        migrations.DeleteModel(
            name='AvailableOption',
        ),
        migrations.RemoveField(
            model_name='availablepaymentoption',
            name='option',
        ),
        migrations.RemoveField(
            model_name='availablepaymentoption',
            name='order_configuration',
        ),
        migrations.DeleteModel(
            name='AvailablePaymentOption',
        ),
        migrations.RemoveField(
            model_name='availablesceneselectionoption',
            name='option',
        ),
        migrations.RemoveField(
            model_name='availablesceneselectionoption',
            name='order_configuration',
        ),
        migrations.DeleteModel(
            name='AvailableSceneSelectionOption',
        ),
    ]
