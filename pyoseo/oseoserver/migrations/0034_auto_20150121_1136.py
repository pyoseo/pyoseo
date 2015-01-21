# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0033_oseofile'),
    ]

    operations = [
        migrations.CreateModel(
            name='ItemProcessor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('python_path', models.CharField(default=b'oseoserver.orderpreparation.noop.FakeOrderProcessor', max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProcessorParameter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('value', models.CharField(max_length=255)),
                ('use_in_option_parsing', models.BooleanField(default=False)),
                ('use_in_item_processing', models.BooleanField(default=False)),
                ('use_in_item_cleanup', models.BooleanField(default=False)),
                ('item_processor', models.ForeignKey(related_name='parameters', to='oseoserver.ItemProcessor')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='collection',
            name='item_preparation_class',
        ),
        migrations.AddField(
            model_name='collection',
            name='item_processor',
            field=models.ForeignKey(default=1, to='oseoserver.ItemProcessor'),
            preserve_default=False,
        ),
    ]
