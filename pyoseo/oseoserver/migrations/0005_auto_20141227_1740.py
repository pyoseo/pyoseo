# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0004_auto_20141227_1712'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='deliveryoptiongroup',
            name='collection_configuration',
        ),
        migrations.RemoveField(
            model_name='optiongroup',
            name='collection_configuration',
        ),
        migrations.RemoveField(
            model_name='paymentoptiongroup',
            name='collection_configuration',
        ),
        migrations.RemoveField(
            model_name='sceneselectionoptiongroup',
            name='collection_configuration',
        ),
        migrations.RemoveField(
            model_name='groupeddeliveryoption',
            name='group',
        ),
        migrations.DeleteModel(
            name='DeliveryOptionGroup',
        ),
        migrations.RemoveField(
            model_name='groupedoption',
            name='group',
        ),
        migrations.DeleteModel(
            name='OptionGroup',
        ),
        migrations.RemoveField(
            model_name='groupedpaymentoption',
            name='group',
        ),
        migrations.DeleteModel(
            name='PaymentOptionGroup',
        ),
        migrations.RemoveField(
            model_name='groupedsceneselectionoption',
            name='group',
        ),
        migrations.DeleteModel(
            name='SceneSelectionOptionGroup',
        ),
        migrations.AddField(
            model_name='groupeddeliveryoption',
            name='order_configuration',
            field=models.ForeignKey(default=1, to='oseoserver.OrderConfiguration'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='groupedoption',
            name='order_configuration',
            field=models.ForeignKey(default=1, to='oseoserver.OrderConfiguration'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='groupedpaymentoption',
            name='order_configuration',
            field=models.ForeignKey(default=1, to='oseoserver.OrderConfiguration'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='groupedsceneselectionoption',
            name='order_configuration',
            field=models.ForeignKey(default=1, to='oseoserver.OrderConfiguration'),
            preserve_default=False,
        ),
    ]
