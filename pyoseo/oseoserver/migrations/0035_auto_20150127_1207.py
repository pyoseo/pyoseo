# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0034_auto_20150121_1136'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='collection',
            name='item_processor',
        ),
        migrations.AddField(
            model_name='ordertype',
            name='item_processor',
            field=models.ForeignKey(default=1, to='oseoserver.ItemProcessor'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='itemprocessor',
            name='python_path',
            field=models.CharField(default=b'oseoserver.orderpreparation.noop.FakeOrderProcessor', help_text=b'Python import path to a custom class that is used to process the order items. This class must conform to the expected interface.', max_length=255),
            preserve_default=True,
        ),
    ]
