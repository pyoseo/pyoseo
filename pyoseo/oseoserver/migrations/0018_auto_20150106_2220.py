# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0017_auto_20150106_2215'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderconfiguration',
            name='collection',
        ),
        migrations.AddField(
            model_name='massiveorderconfiguration',
            name='collection',
            field=models.OneToOneField(default=1, to='oseoserver.Collection'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='productorderconfiguration',
            name='collection',
            field=models.OneToOneField(default=1, to='oseoserver.Collection'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='subscriptionorderconfiguration',
            name='collection',
            field=models.OneToOneField(default=1, to='oseoserver.Collection'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='taskingorderconfiguration',
            name='collection',
            field=models.OneToOneField(default=1, to='oseoserver.Collection'),
            preserve_default=False,
        ),
    ]
