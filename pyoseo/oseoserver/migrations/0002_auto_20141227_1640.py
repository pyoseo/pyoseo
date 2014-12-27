# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderConfiguration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('enabled', models.BooleanField(default=False)),
                ('automatic_approval', models.BooleanField(default=False, help_text=b'Should this type of order be approved automatically for the selected collection?')),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=255, blank=True)),
                ('order_processing_fee', models.DecimalField(default=Decimal('0'), max_digits=5, decimal_places=2)),
                ('collection', models.ForeignKey(to='oseoserver.Collection')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='collectionconfiguration',
            name='collection',
        ),
        migrations.RemoveField(
            model_name='collectionconfiguration',
            name='order_type',
        ),
        migrations.AddField(
            model_name='collection',
            name='massive_order_configuration',
            field=models.ForeignKey(related_name='massive_collection', blank=True, to='oseoserver.OrderConfiguration', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='collection',
            name='product_order_configuration',
            field=models.ForeignKey(related_name='product_collection', blank=True, to='oseoserver.OrderConfiguration', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='collection',
            name='subscription_order_configuration',
            field=models.ForeignKey(related_name='subscription_collection', blank=True, to='oseoserver.OrderConfiguration', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='collection',
            name='tasking_order_configuration',
            field=models.ForeignKey(related_name='tasking_collection', blank=True, to='oseoserver.OrderConfiguration', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='deliveryoptiongroup',
            name='collection_configuration',
            field=models.ForeignKey(related_name='oseoserver_deliveryoptiongroup_related', to='oseoserver.OrderConfiguration'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='optiongroup',
            name='collection_configuration',
            field=models.ForeignKey(related_name='oseoserver_optiongroup_related', to='oseoserver.OrderConfiguration'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='order',
            name='order_type',
            field=models.CharField(default=b'PRODUCT_ORDER', max_length=30, choices=[(b'PRODUCT_ORDER', b'PRODUCT_ORDER'), (b'MASSIVE_ORDER', b'MASSIVE_ORDER'), (b'SUBSCRIPTION_ORDER', b'SUBSCRIPTION_ORDER'), (b'TASKING_ORDER', b'TASKING_ORDER')]),
            preserve_default=True,
        ),
        migrations.DeleteModel(
            name='OrderType',
        ),
        migrations.AlterField(
            model_name='paymentoptiongroup',
            name='collection_configuration',
            field=models.ForeignKey(related_name='oseoserver_paymentoptiongroup_related', to='oseoserver.OrderConfiguration'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='sceneselectionoptiongroup',
            name='collection_configuration',
            field=models.ForeignKey(related_name='oseoserver_sceneselectionoptiongroup_related', to='oseoserver.OrderConfiguration'),
            preserve_default=True,
        ),
        migrations.DeleteModel(
            name='CollectionConfiguration',
        ),
    ]
