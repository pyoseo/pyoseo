# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0024_remove_order_order_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='selectedpaymentoption',
            name='order_item',
            field=models.OneToOneField(related_name='selected_payment_option', null=True, blank=True, to='oseoserver.OrderItem'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='selectedsceneselectionoption',
            name='order_item',
            field=models.ForeignKey(related_name='selected_scene_selection_options', to='oseoserver.OrderItem'),
            preserve_default=True,
        ),
    ]
