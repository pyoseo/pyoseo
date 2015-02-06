# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0027_auto_20150116_1415'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=30)),
                ('enabled', models.BooleanField(default=False)),
                ('automatic_approval', models.BooleanField(default=False)),
                ('notify_creation', models.BooleanField(default=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
