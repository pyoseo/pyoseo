# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0032_auto_20150120_1800'),
    ]

    operations = [
        migrations.CreateModel(
            name='OseoFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('name', models.CharField(max_length=255)),
                ('available', models.BooleanField(default=False)),
                ('downloads', models.SmallIntegerField(default=0, help_text=b'Number of times this order item has been downloaded.')),
                ('order_item', models.ForeignKey(related_name='files', to='oseoserver.OrderItem')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
