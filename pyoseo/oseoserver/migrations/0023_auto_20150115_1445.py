# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0022_auto_20150112_1524'),
    ]

    operations = [
        migrations.CreateModel(
            name='DerivedOrder',
            fields=[
                ('order_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='oseoserver.Order')),
            ],
            options={
            },
            bases=('oseoserver.order',),
        ),
        migrations.CreateModel(
            name='MassiveOrder',
            fields=[
                ('derivedorder_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='oseoserver.DerivedOrder')),
            ],
            options={
            },
            bases=('oseoserver.derivedorder',),
        ),
        migrations.CreateModel(
            name='ProductOrder',
            fields=[
                ('order_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='oseoserver.Order')),
            ],
            options={
            },
            bases=('oseoserver.order',),
        ),
        migrations.CreateModel(
            name='SubscriptionOrder',
            fields=[
                ('derivedorder_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='oseoserver.DerivedOrder')),
            ],
            options={
            },
            bases=('oseoserver.derivedorder',),
        ),
        migrations.CreateModel(
            name='TaskingOrder',
            fields=[
                ('derivedorder_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='oseoserver.DerivedOrder')),
            ],
            options={
            },
            bases=('oseoserver.derivedorder',),
        ),
        migrations.AddField(
            model_name='derivedorder',
            name='collections',
            field=models.ManyToManyField(related_name='derived_orders', to='oseoserver.Collection'),
            preserve_default=True,
        ),
    ]
