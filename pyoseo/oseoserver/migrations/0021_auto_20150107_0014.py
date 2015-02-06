# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oseoserver', '0020_auto_20150106_2343'),
    ]

    operations = [
        migrations.RenameField(
            model_name='collection',
            old_name='short_name',
            new_name='name',
        ),
    ]
