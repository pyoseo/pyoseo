# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0005_auto_20141227_1740'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='GroupedDeliveryOption',
            new_name='AvailableDeliveryOption',
        ),
        migrations.RenameModel(
            old_name='GroupedOption',
            new_name='AvailableOption',
        ),
        migrations.RenameModel(
            old_name='GroupedSceneSelectionOption',
            new_name='AvailablePaymentOption',
        ),
        migrations.RenameModel(
            old_name='GroupedPaymentOption',
            new_name='AvailableSceneSelectionOption',
        ),
        migrations.AlterField(
            model_name='availablepaymentoption',
            name='option',
            field=models.ForeignKey(to='oseoserver.PaymentOption'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='availablesceneselectionoption',
            name='option',
            field=models.ForeignKey(to='oseoserver.SceneSelectionOption'),
            preserve_default=True,
        ),
    ]
