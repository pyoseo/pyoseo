# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0008_auto_20141227_1840'),
    ]

    operations = [
        migrations.CreateModel(
            name='MassiveOrderConfiguration',
            fields=[
                ('orderconfiguration_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='oseoserver.OrderConfiguration')),
            ],
            options={
            },
            bases=('oseoserver.orderconfiguration',),
        ),
        migrations.CreateModel(
            name='ProductOrderConfiguration',
            fields=[
                ('orderconfiguration_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='oseoserver.OrderConfiguration')),
            ],
            options={
            },
            bases=('oseoserver.orderconfiguration',),
        ),
        migrations.CreateModel(
            name='SubscriptionOrderConfiguration',
            fields=[
                ('orderconfiguration_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='oseoserver.OrderConfiguration')),
            ],
            options={
            },
            bases=('oseoserver.orderconfiguration',),
        ),
        migrations.CreateModel(
            name='TaskingOrderConfiguration',
            fields=[
                ('orderconfiguration_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='oseoserver.OrderConfiguration')),
            ],
            options={
            },
            bases=('oseoserver.orderconfiguration',),
        ),
        migrations.AlterField(
            model_name='collection',
            name='massive_order_configuration',
            field=models.OneToOneField(to='oseoserver.MassiveOrderConfiguration'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='collection',
            name='product_order_configuration',
            field=models.OneToOneField(to='oseoserver.ProductOrderConfiguration'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='collection',
            name='subscription_order_configuration',
            field=models.OneToOneField(to='oseoserver.SubscriptionOrderConfiguration'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='collection',
            name='tasking_order_configuration',
            field=models.OneToOneField(to='oseoserver.TaskingOrderConfiguration'),
            preserve_default=True,
        ),
    ]
